import os
import gc
import zlib
import struct
import mmap
import logging
import concurrent.futures
import json
from dataclasses import dataclass
from pathlib import Path, PurePath
from typing import List

try:
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn
    console = Console()
except ImportError:
    class DummyConsole:
        def print(self, *args, **kwargs):
            if args:
                print(*args)
    console = DummyConsole()
    Progress = None

try:
    from Crypto.Hash import SHA1
except ImportError:
    SHA1 = None

from pak.crypto import (
    PakCrypto, SM4, RSA_MOD_2,
    EM_SIMPLE1, EM_SIMPLE2, EM_SM4_2, EM_SM4_4,
    CM_NONE, CM_ZLIB, CM_ZSTD, CM_ZSTD_DICT, CM_MASK
)
from pak.compression import PakCompression

class Misc:
    @staticmethod
    def pad_to_n(data: bytes, n: int) -> bytes:
        assert n > 0, "Block alignment size must be greater than 0"
        padding = n - len(data) % n
        if padding == n:
            return data
        else:
            return data + b'\x00' * padding

    @staticmethod
    def align_up(x: int, n: int) -> int:
        return (x + n - 1) // n * n

class Reader:
    def __init__(self, buffer, cursor=0):
        self._buffer = buffer
        self._cursor = cursor

    def u1(self, move_cursor=True) -> int:
        return self.unpack('B', move_cursor=move_cursor)[0]

    def u4(self, move_cursor=True) -> int:
        return self.unpack('<I', move_cursor=move_cursor)[0]

    def u8(self, move_cursor=True) -> int:
        return self.unpack('<Q', move_cursor=move_cursor)[0]

    def i1(self, move_cursor=True) -> int:
        return self.unpack('b', move_cursor=move_cursor)[0]

    def i4(self, move_cursor=True) -> int:
        return self.unpack('<i', move_cursor=move_cursor)[0]

    def i8(self, move_cursor=True) -> int:
        return self.unpack('<q', move_cursor=move_cursor)[0]

    def s(self, n: int, move_cursor=True) -> bytes:
        return self.unpack(f'{n}s', move_cursor=move_cursor)[0]

    def unpack(self, f: str, offset=0, move_cursor=True):
        x = struct.unpack_from(f, self._buffer, self._cursor + offset)
        if move_cursor:
            self._cursor += struct.calcsize(f)
        return x

    def string(self, move_cursor=True) -> str:
        length = self.i4(move_cursor=move_cursor)
        if length == 0:
            return str()
        else:
            assert length > 0, "String length in PAK index reader must be greater than 0"
            offset = 0 if move_cursor else 4
            return self.unpack(f'{length}s', offset=offset, move_cursor=move_cursor)[0].rstrip(b'\x00').decode()

class PakInfo:
    def __init__(self, buffer, keystream: List[int]):
        def decrypt_index_encrypted(x: int) -> int:
            MASK_8 = 255
            return (x ^ keystream[3]) & MASK_8
        def decrypt_magic(x: int) -> int:
            return x ^ keystream[2]
        def decrypt_index_hash(x: bytes) -> bytes:
            key = struct.pack('<5I', *keystream[4:][:5])
            assert len(x) == len(key), "Index hash decryption key length mismatch"
            return bytes((a ^ b for a, b in zip(x, key)))
        def decrypt_index_size(x: int) -> int:
            return x ^ (keystream[10] << 32 | keystream[11])
        def decrypt_index_offset(x: int) -> int:
            return x ^ (keystream[0] << 32 | keystream[1])

        reader = Reader(buffer[-PakInfo._mem_size((-1)):])
        self.index_encrypted = decrypt_index_encrypted(reader.u1()) == 1
        self.magic = decrypt_magic(reader.u4())
        self.version = reader.u4()
        self.index_hash = decrypt_index_hash(reader.s(20)) if self.version >= 6 else bytes()
        self.index_size = decrypt_index_size(reader.u8())
        self.index_offset = decrypt_index_offset(reader.u8())
        if self.version <= 3:
            self.index_encrypted = False

    @staticmethod
    def _mem_size(_: int) -> int:
        return 45

class TencentPakInfo(PakInfo):
    def __init__(self, buffer, keystream: List[int]):
        def decrypt_unk(x: bytes) -> bytes:
            key = struct.pack('<8I', *keystream[7:][:8])
            assert len(x) == len(key), "PakInfo unknown key length mismatch"
            return bytes((a ^ b for a, b in zip(x, key)))
        def decrypt_stem_hash(x: int) -> int:
            return x ^ keystream[8]
        def decrypt_unk_hash(x: int) -> int:
            return x ^ keystream[9]

        super().__init__(buffer, keystream)
        reader = Reader(buffer[-TencentPakInfo._mem_size(self.version):])
        self.unk1 = decrypt_unk(reader.s(32)) if self.version >= 7 else bytes()
        self.packed_key = reader.s(256) if self.version >= 8 else bytes()
        self.packed_iv = reader.s(256) if self.version >= 8 else bytes()
        self.packed_index_hash = reader.s(256) if self.version >= 8 else bytes()
        self.stem_hash = decrypt_stem_hash(reader.u4()) if self.version >= 9 else 0
        self.unk2 = decrypt_unk_hash(reader.u4()) if self.version >= 9 else 0
        self.content_org_hash = reader.s(20) if self.version >= 12 else bytes()

    @staticmethod
    def _mem_size(version: int) -> int:
        size_for_7 = 32 if version >= 7 else 0
        size_for_8 = 768 if version >= 8 else 0
        size_for_9 = 8 if version >= 9 else 0
        size_for_12 = 20 if version >= 12 else 0
        return PakInfo._mem_size(version) + size_for_7 + size_for_8 + size_for_9 + size_for_12

class PakCompressedBlock:
    def __init__(self, reader: Reader):
        self.start = reader.u8()
        self.end = reader.u8()

class TencentPakEntry:
    def __init__(self, reader: Reader, version: int):
        self.content_hash = reader.s(20)
        if version <= 1:
            _ = reader.u8()
        self.offset = reader.u8()
        self.uncompressed_size = reader.u8()
        self.compression_method = reader.u4() & CM_MASK
        self.size = reader.u8()
        self.unk1 = reader.u1() if version >= 5 else 0
        self.unk2 = reader.s(20) if version >= 5 else bytes()
        if self.compression_method != 0 and version >= 3:
            self.compressed_blocks = [PakCompressedBlock(reader) for _ in range(reader.u4())]
        else:
            self.compressed_blocks = []
        self.compression_block_size = reader.u4() if version >= 4 else 0
        self.encrypted = reader.u1() == 1 if version >= 4 else False
        self.encryption_method = reader.u4() if version >= 12 else 0
        self.index_new_sep = reader.u4() if version >= 12 else 0

def check_disk_space(target_path: Path, estimated_required_bytes: int) -> bool:
    try:
        import shutil
        target_path.mkdir(parents=True, exist_ok=True)
        usage = shutil.disk_usage(target_path)
        if usage.free < estimated_required_bytes:
            req_mb = estimated_required_bytes / (1024 * 1024)
            free_mb = usage.free / (1024 * 1024)
            console.print(f"[bold red][⚠️ DISK SPACE WARNING] Estimated size: {req_mb:.1f} MB, Free space: {free_mb:.1f} MB[/bold red]")
            ans = input("-> Free space is low. Continue anyway? (y/N): ").strip().lower()
            return ans in ['y', 'yes']
    except Exception:
        pass
    return True

def load_checkpoint(checkpoint_file: Path) -> set:
    if checkpoint_file.exists():
        try:
            data = json.loads(checkpoint_file.read_text(encoding="utf-8"))
            return set(data.get("completed", []))
        except Exception:
            pass
    return set()

def save_checkpoint(checkpoint_file: Path, completed_set: set):
    try:
        checkpoint_file.parent.mkdir(parents=True, exist_ok=True)
        checkpoint_file.write_text(json.dumps({"completed": list(completed_set)}), encoding="utf-8")
    except Exception:
        pass

def clear_checkpoint(checkpoint_file: Path):
    try:
        if checkpoint_file.exists():
            checkpoint_file.unlink()
    except Exception:
        pass

class TencentPakFile:
    def __init__(self, file_path: PurePath, is_od=False):
        self._file_path = file_path
        p_path = Path(file_path)
        if not p_path.exists() or p_path.stat().st_size == 0:
            raise ValueError(f"PAK/OBB file '{p_path.name}' does not exist or is 0 bytes (empty).")
        if p_path.stat().st_size < 45:
            raise ValueError(f"PAK/OBB file '{p_path.name}' is too small or corrupt ({p_path.stat().st_size} bytes). Minimum header size is 45 bytes.")

        with open(file_path, 'rb') as file:
            try:
                self._mmap_obj = mmap.mmap(file.fileno(), 0, access=mmap.ACCESS_READ)
                self._file_content = memoryview(self._mmap_obj)
            except Exception:
                self._file_content = memoryview(file.read())
        self._is_od = is_od
        self._mount_point = PurePath()
        self._is_zstd_with_dict = 'zsdic' in str(self._file_path)
        self._zstd_dict = None
        self._files = []
        self._index = {}
        self._pak_info = TencentPakInfo(self._file_content, PakCrypto.zuc_keystream())
        self._verify_stem_hash()
        self._tencent_load_index()

    def _get_method_str(self, method_int, is_encryption):
        if is_encryption:
            if PakCrypto._is_simple1_method(method_int): return "SIMPLE1"
            if PakCrypto._is_simple2_method(method_int): return "SIMPLE2"
            if PakCrypto._is_sm4_method(method_int): return f"SM4 (Type {method_int})"
            return "NONE" if method_int == 0 else "UNKNOWN"
        else:
            if method_int == CM_NONE: return "NONE"
            if method_int == CM_ZLIB: return "ZLIB"
            if method_int == CM_ZSTD: return "ZSTD"
            if method_int == CM_ZSTD_DICT: return "ZSTD_DICT"
            return "UNKNOWN"

    def _verify_stem_hash(self) -> None:
        if not self._is_od and self._pak_info.version >= 9:
            calc_hash = zlib.crc32(self._file_path.stem.encode('utf-32le'))
            if self._pak_info.stem_hash != calc_hash:
                logging.warning(f"PAK filename stem CRC mismatch ({self._pak_info.stem_hash} vs {calc_hash}). Auto-repairing & bypassing stem check...")

    def _tencent_load_index(self) -> None:
        if self._pak_info.index_offset < 0 or self._pak_info.index_offset >= len(self._file_content):
            raise ValueError(f"PAK index offset invalid or corrupt ({self._pak_info.index_offset} vs content size {len(self._file_content)}). File may be corrupted or password protected.")
        index_data = self._file_content[self._pak_info.index_offset:][:self._pak_info.index_size]
        if not index_data or len(index_data) == 0:
            raise ValueError(f"PAK index data is empty or offset out of bounds ({self._pak_info.index_offset}, size {self._pak_info.index_size}). File is corrupted.")
        if self._pak_info.index_encrypted:
            index_data = PakCrypto.decrypt_index(index_data, self._pak_info)
        if not index_data or len(index_data) == 0:
            raise ValueError("Decrypted PAK index data is empty or corrupt.")
        self._verify_index_hash(index_data)
        self._load_index(index_data)

    def _verify_index_hash(self, index_data) -> None:
        expected_hash = self._pak_info.index_hash
        if not self._is_od and self._pak_info.version >= 8:
            try:
                extracted = PakCrypto.rsa_extract(self._pak_info.packed_index_hash, RSA_MOD_2)
                if expected_hash != extracted:
                    logging.warning("RSA index hash check soft-failed (custom/modified PAK signature). Proceeding...")
            except Exception as e:
                logging.warning(f"RSA index hash extraction skipped: {e}")
        computed_hash = SHA1.new(index_data).digest()
        if expected_hash != computed_hash:
            logging.warning("SHA1 index hash mismatch — PAK header/key may be modified. Attempting unpack anyway...")

    @staticmethod
    def _construct_mount_point(mount_point: str) -> PurePath:
        result = PurePath()
        for part in PurePath(mount_point).parts:
            if part != '..':
                result /= part
        return result

    def _peek_content(self, offset: int, size: int, encryption_method: int) -> memoryview:
        size = PakCrypto.align_encrypted_content_size(size, encryption_method)
        return self._file_content[offset:][:size]

    def _peek_block_content(self, block: PakCompressedBlock, encryption_method: int) -> memoryview:
        size = PakCrypto.align_encrypted_content_size(block.end - block.start, encryption_method)
        return self._file_content[block.start:][:size]

    def _construct_zstd_dict(self, dict_entry: TencentPakEntry) -> None:
        assert not self._zstd_dict, "ZSTD dictionary already loaded"
        assert not dict_entry.encrypted, "ZSTD dictionary entry cannot be encrypted"
        assert dict_entry.compression_method == CM_NONE, "ZSTD dictionary entry must not be compressed"
        reader = Reader(self._peek_content(dict_entry.offset, dict_entry.size, 0))
        dict_size = reader.u8()
        _ = reader.u4()
        assert dict_size == reader.u4(), "ZSTD dictionary header size mismatch"
        dict_data = reader.s(dict_size)
        self._zstd_dict = PakCompression.zstd_dictionary(dict_data)

    def _load_index(self, index_data) -> None:
        if self._pak_info.version <= 10:
            raise ValueError(f'Unsupported version: {self._pak_info.version}')
        else:
            reader = Reader(index_data)
            self._mount_point = self._construct_mount_point(reader.string())
            self._files = [TencentPakEntry(reader, self._pak_info.version) for _ in range(reader.u4())]
            for _ in range(reader.u8()):
                dir_path = PurePath(reader.string())
                e = {reader.string(): self._files[~reader.i4()] for _ in range(reader.u8())}
                if self._is_zstd_with_dict and dir_path.name == 'zstddic':
                    assert len(e) == 1, "ZSTD dictionary directory must contain exactly one file"
                    self._construct_zstd_dict(e[[*e.keys()][0]])
                else:
                    self._index.update({PurePath(dir_path): e})

    def _write_to_disk(self, file_path: Path, entry: TencentPakEntry, silent: bool = False) -> None:
        if not silent:
            encryption_method = entry.encryption_method
            compression_method = entry.compression_method

            enc_str = self._get_method_str(encryption_method, True)
            comp_str = self._get_method_str(compression_method, False)
            console.print(f"[bold cyan]->[/] Unpack: [bold green]{file_path.name}[/] [[bold yellow]{comp_str}[/]/[bold magenta]{enc_str}[/]]")

        with open(file_path, 'wb') as file:
            if entry.compression_method == CM_NONE:
                offset = entry.offset
                total_size = PakCrypto.align_encrypted_content_size(entry.size, entry.encryption_method)
                chunk_size = 64 * 1024 * 1024
                written = 0
                while written < total_size:
                    to_read = min(chunk_size, total_size - written)
                    data = self._file_content[offset + written:][:to_read]
                    if entry.encrypted:
                        data = PakCrypto.decrypt_block(data, file_path, entry.encryption_method)
                    file.write(data)
                    written += to_read
                file.truncate(entry.size)
                return
            else:
                if len(entry.compressed_blocks) == 0:
                    data = self._peek_content(entry.offset, entry.size, entry.encryption_method)
                    if entry.encrypted:
                        data = PakCrypto.decrypt_block(data, file_path, entry.encryption_method)
                    data = PakCompression.decompress_block(data, self._zstd_dict, entry.compression_method)
                    file.write(data)
                else:
                    block_size = entry.compression_block_size if entry.compression_block_size > 0 else 65536
                    for x in PakCrypto.generate_block_indices(len(entry.compressed_blocks), entry.encryption_method):
                        data = self._peek_block_content(entry.compressed_blocks[x], entry.encryption_method)
                        if entry.encrypted:
                            data = PakCrypto.decrypt_block(data, file_path, entry.encryption_method)
                        data = PakCompression.decompress_block(data, self._zstd_dict, entry.compression_method)
                        file.seek(x * block_size)
                        file.write(data)
                file.truncate(entry.uncompressed_size)

    def dump(self, out_path: Path) -> None:
        out_path = out_path / self._mount_point
        out_path.mkdir(parents=True, exist_ok=True)
        total_files = sum(len(d) for d in self._index.values())

        total_uncompressed_bytes = sum(entry.uncompressed_size for d in self._index.values() for entry in d.values())
        if not check_disk_space(out_path, total_uncompressed_bytes):
            console.print("[yellow][!] Extraction stopped due to disk space warning.[/yellow]")
            return

        checkpoint_file = out_path.parent / ".unpack_progress.json"
        completed = load_checkpoint(checkpoint_file)

        items_to_unpack = []
        for dir_path, dir_content in self._index.items():
            current_out_path = out_path / dir_path
            current_out_path.mkdir(parents=True, exist_ok=True)
            for file_name, entry in dir_content.items():
                rel_file_key = str(PurePath(dir_path) / file_name).replace('\\', '/')
                if rel_file_key not in completed:
                    target_file = current_out_path / file_name
                    items_to_unpack.append((target_file, entry, rel_file_key))

        silent_mode = len(items_to_unpack) > 10
        processed_count = 0

        def _unpack_item(item):
            t_file, ent, key = item
            try:
                self._write_to_disk(t_file, ent, silent=silent_mode)
                return True, key, None
            except Exception as e:
                return False, key, e

        with Progress(
            SpinnerColumn(),
            TextColumn("[bold cyan][UNPACK][/] {task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            task = progress.add_task("Extracting files in parallel...", total=total_files)
            progress.update(task, advance=len(completed))

            max_workers = min(16, (os.cpu_count() or 4) * 2)
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {executor.submit(_unpack_item, item): item for item in items_to_unpack}
                for future in concurrent.futures.as_completed(futures):
                    success, key, err = future.result()
                    if success:
                        completed.add(key)
                    else:
                        console.print(f"[bold red][X] Skip corrupted entry '{key}': {err}[/bold red]")

                    processed_count += 1
                    if processed_count % 100 == 0:
                        save_checkpoint(checkpoint_file, completed)
                        gc.collect()

                    progress.update(task, advance=1)

        clear_checkpoint(checkpoint_file)
        gc.collect()

pad_to_n = Misc.pad_to_n
align_up = Misc.align_up

