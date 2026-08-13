import os
import gc
import zlib
import struct
import shutil
from pathlib import Path, PurePath
import copy as _cp

try:
    from rich.console import Console
    console = Console()
except ImportError:
    class DummyConsole:
        def print(self, *args, **kwargs):
            if args:
                print(*args)
    console = DummyConsole()

try:
    from Crypto.Cipher import AES
    from Crypto.Hash import SHA1
except ImportError:
    AES = None
    SHA1 = None

try:
    from zstandard import ZstdCompressor
except ImportError:
    ZstdCompressor = None

from pak.crypto import (
    PakCrypto, RSA_MOD_1,
    EM_SIMPLE1, EM_SIMPLE2, EM_SM4_2, EM_SM4_4,
    CM_NONE, CM_ZLIB, CM_ZSTD, CM_ZSTD_DICT
)
from pak.compression import PakCompression
from pak.container import (
    Reader, TencentPakInfo, PakCompressedBlock,
    TencentPakEntry, check_disk_space
)

class SimpleBlockDisplay:
    def __init__(self, total_files: int, pak_name: str):
        self.total_files = total_files
        self.pak_name = pak_name
        self.processed_files = 0
        self.current_file = ""
        self.current_file_idx = 0
        self.all_blocks = []
        self.total_fitted = 0
        self.total_skipped = 0
        
    def start_file(self, file_name: str, total_blocks: int):
        self.current_file_idx += 1
        self.current_file = file_name
        self.current_blocks = []
        self.current_total_blocks = total_blocks
        self.current_fitted = 0
        self.current_skipped = 0
        
        console.print()
        console.print(f"[bold cyan]┌─────────────────────────────────────────────────────────────[/bold cyan]")
        console.print(f"[bold cyan]│[/] [bold yellow][{self.current_file_idx}/{self.total_files}][/] [bold green]{file_name}[/bold green] [dim]({total_blocks} blocks)[/dim]")
        console.print(f"[bold cyan]├─────────────────────────────────────────────────────────────[/bold cyan]")
        
    def add_block(self, block_idx: int, block_size: int, fitted: bool, compression_ratio: float = None):
        size_mb = block_size / (1024 * 1024)
        if fitted:
            self.current_fitted += 1
            self.total_fitted += 1
            ratio_str = f" [{compression_ratio:.1%}]" if compression_ratio else ""
            status = f"[green]✓ FITTED{ratio_str}[/green]"
        else:
            self.current_skipped += 1
            self.total_skipped += 1
            status = f"[red]✗ SKIPPED[/red]"
        
        console.print(f"[bold cyan]│[/]    Block {block_idx:3d}: {size_mb:>7.2f} MB  →  {status}")
        self.current_blocks.append({'fitted': fitted})
        
    def finish_file(self):
        total_blocks = len(self.current_blocks)
        
        if total_blocks > 0:
            if self.current_fitted == total_blocks:
                status = "[green]✓ ALL FITTED[/green]"
            elif self.current_fitted > 0:
                status = f"[yellow]✓ {self.current_fitted}/{total_blocks} FITTED[/yellow]"
            else:
                status = "[red]✗ ALL SKIPPED[/red]"
        else:
            status = "[green]✓ DONE[/green]"
        
        console.print(f"[bold cyan]└─────────────────────────────────────────────────────────────[/bold cyan]")
        console.print(f"  [dim]Result: {status}[/dim]")
        
        self.processed_files += 1
        self.all_blocks.extend(self.current_blocks)
        
    def final_summary(self):
        total_blocks = len(self.all_blocks)
        
        console.print()
        console.print(f"[bold green]╔═════════════════════════════════════════════════════════════════╗[/bold green]")
        console.print(f"[bold green]║[/] [bold yellow]REPACK SUMMARY[/bold yellow]")
        console.print(f"[bold green]║[/]")
        console.print(f"[bold green]║[/]   Total Files:   [bold cyan]{self.processed_files}[/bold cyan]")
        console.print(f"[bold green]║[/]   Total Blocks:  [bold cyan]{total_blocks}[/bold cyan]")
        console.print(f"[bold green]║[/]   Fitted Blocks: [bold green]{self.total_fitted}[/bold green]")
        console.print(f"[bold green]║[/]   Skipped Blocks:[bold red]{self.total_skipped}[/bold red]")
        if total_blocks > 0:
            success_rate = (self.total_fitted / total_blocks) * 100
            console.print(f"[bold green]║[/]   Success Rate:  [bold yellow]{success_rate:.1f}%[/bold yellow]")
        console.print(f"[bold green]╚═════════════════════════════════════════════════════════════════╝[/bold green]")

def dump_unpacking_log(pak_file, output_log_path: Path):
    with open(output_log_path, 'w', encoding='utf-8') as log_file:
        log_file.write('================================================================================\n')
        log_file.write('PAK UNPACKING DEBUG LOG\n')
        log_file.write('================================================================================\n\n')
        log_file.write(f'PAK File: {pak_file._file_path}\n')
        log_file.write(f'PAK Info Version: {pak_file._pak_info.version}\n')
        log_file.write(f'Mount Point: {pak_file._mount_point}\n')
        log_file.write('--------------------------------------------------------------------------------\n\n')
        file_count = 0
        for dir_path, files in pak_file._index.items():
            for file_name, entry in files.items():
                file_count += 1
                full_path = str(PurePath(dir_path) / file_name).replace('\\', '/')
                log_file.write(f'\n[{file_count}] {full_path}\n')
                log_file.write(f'  Uncompressed Size: {entry.uncompressed_size:,} bytes\n')
                log_file.write(f'  Compressed Size: {entry.size:,} bytes\n')
                log_file.write(f'  Compression Method: {entry.compression_method}\n')
                log_file.write(f'  Encryption Method: {entry.encryption_method}\n')
                log_file.write(f'  Compressed Blocks: {len(entry.compressed_blocks)}\n')
                if entry.compressed_blocks:
                    for i, blk in enumerate(entry.compressed_blocks):
                        block_size = blk.end - blk.start
                        log_file.write(f'    Block {i}: Offset={blk.start:,} Size={block_size:,} bytes\n')
        log_file.write('\n================================================================================\n')
        log_file.write('END OF LOG\n')
        log_file.write('================================================================================\n')
    console.print(f'[bold #00FF88]✅ Debug log saved to: {output_log_path}[/bold #00FF88]')

LARGE_FILE_THRESHOLD = 200 * 1024 * 1024

def _compute_file_sha1(file_path: Path) -> bytes:
    if SHA1 is not None:
        h = SHA1.new()
    else:
        import hashlib
        h = hashlib.sha1()
    with open(file_path, 'rb') as f:
        while True:
            chunk = f.read(16 * 1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return h.digest()

def _zstd_add_skippable_padding(data: bytes, pad_len: int) -> bytes:
    if pad_len <= 0:
        return data
    else:
        out = bytearray(data)
        while pad_len > 0:
            frame_len = min(max(pad_len - 8, 0), 1048576)
            out += b'P*M\x18'
            out += struct.pack('<I', frame_len)
            out += b'\x00' * frame_len
            pad_len -= 8 + frame_len
        return bytes(out)

def _encrypt_plaintext(plaintext: bytes, pak_relative_path: PurePath, encryption_method: int) -> bytes:
    from pak.crypto import SIMPLE1_DECRYPT_KEY, SIMPLE2_DECRYPT_KEY, SIMPLE2_BLOCK_SIZE
    if PakCrypto._is_simple1_method(encryption_method):
        return bytes((b ^ SIMPLE1_DECRYPT_KEY for b in plaintext))
    else:
        if PakCrypto._is_simple2_method(encryption_method):
            pad = -len(plaintext) % SIMPLE2_BLOCK_SIZE
            plaintext += b'\x00' * pad
            key, = struct.unpack('<I', SIMPLE2_DECRYPT_KEY)
            rolling = key
            out = []
            for x, in struct.iter_unpack('<I', plaintext):
                c = rolling ^ x
                out.append(c)
                rolling ^= c
            return struct.pack(f'<{len(out)}I', *out)
        else:
            if PakCrypto._is_sm4_method(encryption_method):
                key = PakCrypto._derive_sm4_key(pak_relative_path, encryption_method)
                sm4 = PakCrypto._sm4_context_for_key(key)
                pad_len = -len(plaintext) % 16
                if pad_len > 0:
                    plaintext = plaintext + b'\x00' * pad_len
                out = bytearray()
                for i in range(0, len(plaintext), 16):
                    block = plaintext[i:i + 16]
                    if len(block) < 16:
                        block = block.ljust(16, b'\x00')
                    out.extend(sm4.encrypt(block))
                return bytes(out)
            else:
                return plaintext

def _repack_uncompressed(outfh, pak_file, entry, pak_relative_path: PurePath, new_data):
    enc_method = entry.encryption_method
    target_size = entry.size
    enc_region = PakCrypto.align_encrypted_content_size(target_size, enc_method) if entry.encrypted else target_size
    
    if isinstance(new_data, (str, Path)):
        p_path = Path(new_data)
        file_sz = p_path.stat().st_size
        read_len = min(file_sz, enc_region)
        outfh.seek(entry.offset)
        if not entry.encrypted:
            _stream_copy_bytes(p_path, 0, read_len, outfh)
            if target_size > read_len:
                outfh.seek(entry.offset + read_len)
                with open(pak_file._file_path, 'rb') as src:
                    src.seek(entry.offset + read_len)
                    outfh.write(src.read(target_size - read_len))
        else:
            with open(p_path, 'rb') as pf:
                chunk = pf.read(read_len)
            a = PakCrypto.align_encrypted_content_size(len(chunk), enc_method)
            chunk += b'\x00' * (a - len(chunk))
            cipher = _encrypt_plaintext(chunk, pak_relative_path, enc_method)
            outfh.write(cipher)
            with open(pak_file._file_path, 'rb') as src:
                src.seek(entry.offset + len(cipher))
                outfh.write(src.read(enc_region - len(cipher)))
    else:
        plaintext = new_data[:enc_region]
        if entry.encrypted:
            a = PakCrypto.align_encrypted_content_size(len(plaintext), enc_method)
            plaintext += b'\x00' * (a - len(plaintext))
            cipher = _encrypt_plaintext(plaintext, pak_relative_path, enc_method)
            outfh.seek(entry.offset)
            outfh.write(cipher)
            with open(pak_file._file_path, 'rb') as src:
                src.seek(entry.offset + len(cipher))
                outfh.write(src.read(enc_region - len(cipher)))
        else:
            outfh.seek(entry.offset)
            outfh.write(plaintext)
            with open(pak_file._file_path, 'rb') as src:
                src.seek(entry.offset + len(plaintext))
                outfh.write(src.read(target_size - len(plaintext)))

def _best_compress(chunk, cm, zstd_dict=None):
    if cm == CM_ZLIB:
        return zlib.compress(chunk, 9)
    if cm in (CM_ZSTD, CM_ZSTD_DICT):
        zd = zstd_dict if cm == CM_ZSTD_DICT else None
        for lvl in [19, 12, 7, 3, 1]:
            try:
                return ZstdCompressor(level=lvl, dict_data=zd, threads=0).compress(chunk)
            except Exception:
                continue
    return chunk

def _stream_copy_bytes(src_file_path: PurePath, offset: int, length: int, dst_fh) -> None:
    with open(src_file_path, 'rb') as src:
        src.seek(offset)
        remaining = length
        chunk_size = 16 * 1024 * 1024
        while remaining > 0:
            read_size = min(chunk_size, remaining)
            data = src.read(read_size)
            if not data:
                break
            dst_fh.write(data)
            remaining -= len(data)

def _pw_string(s):
    if not s: return struct.pack('<i', 0)
    b = s.encode('utf-8') + b'\x00'
    return struct.pack('<i', len(b)) + b

def _pw_entry(e, v):
    w = bytearray(e.content_hash)
    w += struct.pack('<Q', e.offset)
    w += struct.pack('<Q', e.uncompressed_size)
    w += struct.pack('<I', e.compression_method)
    w += struct.pack('<Q', e.size)
    if v >= 5:
        w += bytes([e.unk1])
        w += e.unk2
    if e.compression_method != CM_NONE and v >= 3:
        w += struct.pack('<I', len(e.compressed_blocks))
        for b in e.compressed_blocks:
            w += struct.pack('<QQ', b.start, b.end)
    if v >= 4:
        w += struct.pack('<I', e.compression_block_size)
        w += bytes([1 if e.encrypted else 0])
    if v >= 12:
        w += struct.pack('<II', e.encryption_method, e.index_new_sep)
    return bytes(w)

def _get_all_dirs_and_mp(pak_file):
    raw = bytes(pak_file._file_content[
        pak_file._pak_info.index_offset:][:pak_file._pak_info.index_size])
    if pak_file._pak_info.index_encrypted:
        raw = PakCrypto.decrypt_index(raw, pak_file._pak_info)
    r = Reader(raw)
    mp = r.string()
    num_files = r.u4()
    for _ in range(num_files):
        TencentPakEntry(r, pak_file._pak_info.version)
    dirs = {}
    for _ in range(r.u8()):
        dp = r.string()
        cnt = r.u8()
        dirs[dp] = {r.string(): pak_file._files[~r.i4()] for _ in range(cnt)}
    return mp, dirs

def repack_pak_file_full(pak_file, edited_root, output_path, target_path=None, force_add=False):
    console.print(f'[bold cyan][BUILD] Full PAK Rebuild mode[/bold cyan]')
    if target_path:
        console.print(f'[bold cyan][TARGET] Target path: {target_path}[/bold cyan]')
    
    estimated_out_size = os.path.getsize(pak_file._file_path) if os.path.exists(pak_file._file_path) else 1024 * 1024 * 100
    if not check_disk_space(Path(output_path).parent, estimated_out_size):
        console.print("[yellow][!] Repack cancelled due to disk space warning.[/yellow]")
        return 0

    edit_files = []
    edit_p = Path(edited_root)
    ignored_names = {'.gitkeep', '.ds_store', 'desktop.ini', 'thumbs.db'}
    if edit_p.is_file():
        if edit_p.name.lower() not in ignored_names and not edit_p.name.startswith('.'):
            edit_files.append(edit_p)
    elif edit_p.is_dir():
        for p in edit_p.rglob('*'):
            if p.is_file() and p.name.lower() not in ignored_names and not p.name.startswith('.'):
                edit_files.append(p)
    
    if not edit_files:
        console.print(f'[bold red][X] Source folder ({edited_root}) me koi valid file nahi mili. Pehle edited files is folder me daalo.[/bold red]')
        return 0
    
    console.print(f'[bold cyan][+] Found {len(edit_files)} file(s) to process[/bold cyan]')

    version = pak_file._pak_info.version
    keystream = PakCrypto.zuc_keystream()
    orig_fc = pak_file._file_content

    mp_str, all_dirs = _get_all_dirs_and_mp(pak_file)

    if target_path and force_add:
        target_path = target_path.replace('\\', '/')
        matched_dir = None
        for existing_dir in all_dirs.keys():
            if existing_dir.strip('/').lower() == target_path.strip('/').lower():
                matched_dir = existing_dir
                break
        if matched_dir:
            target_path = matched_dir
        else:
            target_path = target_path.strip('/') + '/'
    
    pak_name_map = {}
    for dir_path, files in pak_file._index.items():
        for name, entry in files.items():
            full_path = str(PurePath(dir_path)/name).replace('\\', '/')
            pak_name_map.setdefault(name.lower(), []).append((full_path, entry))

    edited = {}
    
    for p in edit_files:
        fl = p.name.lower()
        
        if force_add and target_path:
            if edit_p.is_dir():
                try:
                    rel_p = p.relative_to(edit_p)
                    rel_fp = str(rel_p).replace('\\', '/')
                except Exception:
                    rel_fp = p.name
            else:
                rel_fp = p.name

            new_fp = f"{target_path.rstrip('/')}/{rel_fp}"
            
            existing_ent = None
            for dir_path, files in pak_file._index.items():
                for name, entry in files.items():
                    if str(PurePath(dir_path)/name).replace('\\', '/') == new_fp:
                        existing_ent = entry
                        break
                if existing_ent:
                    break
            
            if existing_ent:
                edited[new_fp] = (p, existing_ent)
            else:
                template_entry = None
                for dir_path, files in pak_file._index.items():
                    for name, entry in files.items():
                        if Path(name).suffix.lower() == p.suffix.lower():
                            template_entry = entry
                            break
                    if template_entry:
                        break
                if not template_entry:
                    for dir_path, files in pak_file._index.items():
                        for name, entry in files.items():
                            template_entry = entry
                            break
                        if template_entry:
                            break
                if template_entry:
                    edited[new_fp] = (p, template_entry)
                else:
                    console.print(f'[bold red][X] Failed to find template metadata for {p.name}[/bold red]')
            continue

        found_match = False
        
        if edit_p.is_dir():
            try:
                rel_p = p.relative_to(edit_p)
                rel_fp = str(rel_p).replace('\\', '/')
                for dir_path, files in pak_file._index.items():
                    for name, entry in files.items():
                        full_path = str(PurePath(dir_path)/name).replace('\\', '/')
                        if full_path.lower().endswith(rel_fp.lower()):
                            edited[full_path] = (p, entry)
                            found_match = True
                            break
                    if found_match:
                        break
            except Exception:
                pass

        if not found_match and fl in pak_name_map:
            cands = pak_name_map[fl]
            if target_path:
                target_candidates = [(fp, e) for fp, e in cands if target_path.strip('/') in fp]
                if target_candidates:
                    sz = p.stat().st_size
                    sm = [(fp, e) for fp, e in target_candidates if e.uncompressed_size == sz]
                    fp, ent = sm[0] if sm else target_candidates[0]
                    edited[fp] = (p, ent)
                    found_match = True
            
            if not found_match:
                sz = p.stat().st_size
                sm = [(fp, e) for fp, e in cands if e.uncompressed_size == sz]
                fp, ent = sm[0] if sm else cands[0]
                if target_path:
                    new_fp = f"{target_path.rstrip('/')}/{p.name}"
                    edited[new_fp] = (p, ent)
                else:
                    edited[fp] = (p, ent)
                found_match = True
        
        if not found_match:
            stem = p.stem.lower()
            ext = p.suffix.lower()
            for dir_path, files in pak_file._index.items():
                for name, entry in files.items():
                    if Path(name).stem.lower() == stem and Path(name).suffix.lower() == ext:
                        full_path = str(PurePath(dir_path)/name).replace('\\', '/')
                        if target_path:
                            new_fp = f"{target_path.rstrip('/')}/{p.name}"
                            edited[new_fp] = (p, entry)
                        else:
                            edited[full_path] = (p, entry)
                        found_match = True
                        break
                if found_match:
                    break

        if not found_match:
            stem = p.stem.lower()
            for dir_path, files in pak_file._index.items():
                for name, entry in files.items():
                    if Path(name).stem.lower() == stem:
                        full_path = str(PurePath(dir_path)/name).replace('\\', '/')
                        if target_path:
                            new_fp = f"{target_path.rstrip('/')}/{p.name}"
                            edited[new_fp] = (p, entry)
                        else:
                            edited[full_path] = (p, entry)
                        found_match = True
                        break
                if found_match:
                    break

    if not edited:
        console.print('[bold red][X] No files to repack![/bold red]')
        return 0

    console.print(f'  [bold cyan][+] Files to repack: {len(edited)}[/bold cyan]')

    new_files = []
    for e in pak_file._files:
        ne = _cp.copy(e)
        ne.compressed_blocks = [_cp.copy(b) for b in e.compressed_blocks]
        new_files.append(ne)

    old_to_new = {id(pak_file._files[i]): new_files[i] for i in range(len(pak_file._files))}
    edited_paths = {fp: p for fp, (p, _) in edited.items()}

    current_offset = 0
    temp_output_path = Path(str(output_path) + ".tmp")
    
    with open(temp_output_path, 'wb') as out_fh:
        processed_count = 0
        for dp_str, dir_files in list(all_dirs.items()):
            for name, old_entry in list(dir_files.items()):
                full_path = str(PurePath(dp_str)/name).replace('\\', '/')
                ne = old_to_new.get(id(old_entry), None)
                
                if ne is None:
                    ne = _cp.copy(old_entry)
                    ne.compressed_blocks = [_cp.copy(b) for b in old_entry.compressed_blocks]
                    new_files.append(ne)
                    old_to_new[id(old_entry)] = ne

                em = old_entry.encryption_method
                cm = old_entry.compression_method

                try:
                    if full_path in edited_paths:
                        p, template = edited[full_path]
                        file_sz = p.stat().st_size
                        pak_rel = PurePath(full_path)

                        ne.compression_method = template.compression_method if template else cm
                        ne.encryption_method = template.encryption_method if template else em
                        ne.encrypted = template.encrypted if template else old_entry.encrypted
                        ne.unk1 = template.unk1 if template else old_entry.unk1
                        
                        full_path_str = mp_str + full_path
                        ne.unk2 = SHA1.new(full_path_str.lower().encode('utf-8')).digest()
                        ne.index_new_sep = template.index_new_sep if template else old_entry.index_new_sep

                        if file_sz >= LARGE_FILE_THRESHOLD:
                            ne.content_hash = _compute_file_sha1(p)
                            ne.uncompressed_size = file_sz

                            if ne.compression_method == CM_NONE:
                                ne.offset = current_offset
                                ne.size = file_sz
                                if not ne.encrypted:
                                    _stream_copy_bytes(p, 0, file_sz, out_fh)
                                else:
                                    with open(p, 'rb') as pf:
                                        while True:
                                            chunk = pf.read(16 * 1024 * 1024)
                                            if not chunk:
                                                break
                                            cipher = _encrypt_plaintext(chunk, pak_rel, ne.encryption_method)
                                            out_fh.write(cipher)
                                current_offset += file_sz
                            else:
                                cs = (template.compression_block_size if template and template.compression_block_size > 0 
                                      else old_entry.compression_block_size if old_entry.compression_block_size > 0 
                                      else 65536)
                                new_blks = []
                                with open(p, 'rb') as pf:
                                    while True:
                                        chunk = pf.read(cs)
                                        if not chunk:
                                            break
                                        compressed = _best_compress(chunk, ne.compression_method, pak_file._zstd_dict)
                                        cipher = (_encrypt_plaintext(compressed, pak_rel, ne.encryption_method)
                                                  if ne.encrypted else compressed)
                                        blk = PakCompressedBlock.__new__(PakCompressedBlock)
                                        blk.start = current_offset
                                        blk.end = blk.start + len(cipher)
                                        out_fh.write(cipher)
                                        current_offset += len(cipher)
                                        new_blks.append(blk)

                                ne.compressed_blocks = new_blks
                                ne.offset = new_blks[0].start if new_blks else current_offset
                                ne.size = sum(b.end - b.start for b in new_blks)
                        else:
                            new_raw = p.read_bytes()
                            ne.content_hash = SHA1.new(new_raw).digest()
                            ne.uncompressed_size = len(new_raw)

                            if ne.compression_method == CM_NONE:
                                cipher = (_encrypt_plaintext(new_raw, pak_rel, ne.encryption_method)
                                          if ne.encrypted else new_raw)
                                ne.offset = current_offset
                                ne.size = len(new_raw)
                                out_fh.write(cipher)
                                current_offset += len(cipher)
                            else:
                                cs = (template.compression_block_size if template and template.compression_block_size > 0 
                                      else old_entry.compression_block_size if old_entry.compression_block_size > 0 
                                      else 65536)
                                chunks = [new_raw[i:i+cs] for i in range(0, len(new_raw), cs)]
                                new_blks = []
                                for chunk in chunks:
                                    compressed = _best_compress(chunk, ne.compression_method, pak_file._zstd_dict)
                                    cipher = (_encrypt_plaintext(compressed, pak_rel, ne.encryption_method)
                                              if ne.encrypted else compressed)
                                    blk = PakCompressedBlock.__new__(PakCompressedBlock)
                                    blk.start = current_offset
                                    blk.end = blk.start + len(cipher)
                                    out_fh.write(cipher)
                                    current_offset += len(cipher)
                                    new_blks.append(blk)

                                ne.compressed_blocks = new_blks
                                ne.offset = new_blks[0].start if new_blks else current_offset
                                ne.size = sum(b.end - b.start for b in new_blks)

                        console.print(f'[green]✓ Processed: {full_path}[/green]')

                    else:
                        if cm == CM_NONE:
                            read_sz = (PakCrypto.align_encrypted_content_size(old_entry.size, em)
                                       if old_entry.encrypted else old_entry.size)
                            ne.offset = current_offset
                            _stream_copy_bytes(pak_file._file_path, old_entry.offset, read_sz, out_fh)
                            current_offset += read_sz

                        elif old_entry.compressed_blocks:
                            new_blks = []
                            for ob in old_entry.compressed_blocks:
                                unc = ob.end - ob.start
                                enc = (PakCrypto.align_encrypted_content_size(unc, em)
                                       if old_entry.encrypted else unc)
                                nb = PakCompressedBlock.__new__(PakCompressedBlock)
                                nb.start = current_offset
                                nb.end = nb.start + unc
                                _stream_copy_bytes(pak_file._file_path, ob.start, enc, out_fh)
                                current_offset += enc
                                new_blks.append(nb)
                            ne.compressed_blocks = new_blks
                            ne.offset = new_blks[0].start
                except Exception as entry_repack_err:
                    console.print(f"[bold red][X] Skip corrupted repack entry '{full_path}': {entry_repack_err}[/bold red]")

                processed_count += 1
                if processed_count % 100 == 0:
                    gc.collect()

        if target_path and force_add:
            for fp, (p, template) in edited.items():
                already_processed = False
                for dp_str, dir_files in all_dirs.items():
                    for name, entry in dir_files.items():
                        if str(PurePath(dp_str)/name).replace('\\', '/') == fp:
                            already_processed = True
                            break
                    if already_processed:
                        break
                
                if not already_processed:
                    try:
                        ne = _cp.copy(template)
                        file_sz = p.stat().st_size
                        pak_rel = PurePath(fp)
                        
                        ne.compression_method = template.compression_method
                        ne.encryption_method = template.encryption_method
                        ne.encrypted = template.encrypted
                        ne.unk1 = template.unk1
                        
                        full_path_str = mp_str + fp
                        ne.unk2 = SHA1.new(full_path_str.lower().encode('utf-8')).digest()
                        ne.index_new_sep = template.index_new_sep

                        is_lua_file = p.suffix.lower() in ('.lua', '.luac', '.bytes', '.txt') or 'lua' in fp.lower()
                        if is_lua_file:
                            ne.compression_method = CM_NONE
                            ne.encrypted = False

                        if file_sz >= LARGE_FILE_THRESHOLD:
                            ne.content_hash = _compute_file_sha1(p)
                            ne.uncompressed_size = file_sz

                            if ne.compression_method == CM_NONE:
                                ne.offset = current_offset
                                ne.size = file_sz
                                if not ne.encrypted:
                                    _stream_copy_bytes(p, 0, file_sz, out_fh)
                                else:
                                    with open(p, 'rb') as pf:
                                        while True:
                                            chunk = pf.read(16 * 1024 * 1024)
                                            if not chunk:
                                                break
                                            cipher = _encrypt_plaintext(chunk, pak_rel, ne.encryption_method)
                                            out_fh.write(cipher)
                                current_offset += file_sz
                            else:
                                cs = template.compression_block_size if template.compression_block_size > 0 else 65536
                                new_blks = []
                                with open(p, 'rb') as pf:
                                    while True:
                                        chunk = pf.read(cs)
                                        if not chunk:
                                            break
                                        compressed = _best_compress(chunk, ne.compression_method, pak_file._zstd_dict)
                                        cipher = (_encrypt_plaintext(compressed, pak_rel, ne.encryption_method)
                                                  if ne.encrypted else compressed)
                                        blk = PakCompressedBlock.__new__(PakCompressedBlock)
                                        blk.start = current_offset
                                        blk.end = blk.start + len(cipher)
                                        out_fh.write(cipher)
                                        current_offset += len(cipher)
                                        new_blks.append(blk)

                                ne.compressed_blocks = new_blks
                                ne.offset = new_blks[0].start if new_blks else current_offset
                                ne.size = sum(b.end - b.start for b in new_blks)
                        else:
                            new_raw = p.read_bytes()
                            ne.content_hash = SHA1.new(new_raw).digest()
                            ne.uncompressed_size = len(new_raw)

                            if ne.compression_method == CM_NONE:
                                cipher = (_encrypt_plaintext(new_raw, pak_rel, ne.encryption_method)
                                          if ne.encrypted else new_raw)
                                ne.offset = current_offset
                                ne.size = len(new_raw)
                                out_fh.write(cipher)
                                current_offset += len(cipher)
                            else:
                                cs = template.compression_block_size if template.compression_block_size > 0 else 65536
                                chunks = [new_raw[i:i+cs] for i in range(0, len(new_raw), cs)]
                                new_blks = []
                                for chunk in chunks:
                                    compressed = _best_compress(chunk, ne.compression_method, pak_file._zstd_dict)
                                    cipher = (_encrypt_plaintext(compressed, pak_rel, ne.encryption_method)
                                              if ne.encrypted else compressed)
                                    blk = PakCompressedBlock.__new__(PakCompressedBlock)
                                    blk.start = current_offset
                                    blk.end = blk.start + len(cipher)
                                    out_fh.write(cipher)
                                    current_offset += len(cipher)
                                    new_blks.append(blk)

                                ne.compressed_blocks = new_blks
                                ne.offset = new_blks[0].start if new_blks else current_offset
                                ne.size = sum(b.end - b.start for b in new_blks)

                        new_files.append(ne)
                        
                        rel_dir = str(PurePath(fp).parent).replace('\\', '/')
                        if rel_dir in ('.', ''):
                            rel_dir = target_path.strip('/')

                        matched_dir_key = None
                        for existing_k in all_dirs.keys():
                            if existing_k.strip('/').lower() == rel_dir.strip('/').lower():
                                matched_dir_key = existing_k
                                break

                        if not matched_dir_key:
                            has_trailing_slash = any(k.endswith('/') for k in all_dirs.keys() if len(k) > 1)
                            matched_dir_key = rel_dir.strip('/') + '/' if has_trailing_slash else rel_dir.strip('/')
                            all_dirs[matched_dir_key] = {}

                        all_dirs[matched_dir_key][p.name] = ne
                        console.print(f'[green]✓ Added new: {fp}[/green]')
                    except Exception as add_err:
                        console.print(f"[bold red][X] Skip adding corrupted file '{fp}': {add_err}[/bold red]")

        eidx = {id(new_files[i]): i for i in range(len(new_files))}

        idx = bytearray(_pw_string(mp_str))
        idx += struct.pack('<I', len(new_files))
        for ne in new_files:
            idx += _pw_entry(ne, version)
        idx += struct.pack('<Q', len(all_dirs))
        for dp_str, dir_files in all_dirs.items():
            idx += _pw_string(dp_str)
            idx += struct.pack('<Q', len(dir_files))
            for name, old_e in dir_files.items():
                idx += _pw_string(name)
                found_idx = None
                for i, e in enumerate(new_files):
                    if id(e) == id(old_e):
                        found_idx = i
                        break
                if found_idx is None:
                    for i, e in enumerate(new_files):
                        if e.offset == old_e.offset and e.size == old_e.size:
                            found_idx = i
                            break
                if found_idx is not None:
                    idx += struct.pack('<i', ~found_idx)
                else:
                    idx += struct.pack('<i', -1)

        index_plain = bytes(idx)
        new_sha1 = SHA1.new(index_plain).digest()

        if pak_file._pak_info.index_encrypted:
            key = PakCrypto.rsa_extract(pak_file._pak_info.packed_key, RSA_MOD_1)
            iv = PakCrypto.rsa_extract(pak_file._pak_info.packed_iv, RSA_MOD_1)
            aes = AES.new(key, AES.MODE_CBC, iv[:16])
            pad = (-len(index_plain)) % AES.block_size or AES.block_size
            index_bytes = aes.encrypt(index_plain + bytes([pad] * pad))
        else:
            index_bytes = index_plain

        orig_pak_size = os.path.getsize(pak_file._file_path) if hasattr(pak_file, '_file_path') and os.path.exists(pak_file._file_path) else 0
        footer_sz = TencentPakInfo._mem_size(version)
        current_with_index_footer = current_offset + len(index_bytes) + footer_sz

        if orig_pak_size > 0 and current_with_index_footer < orig_pak_size:
            pad_bytes = orig_pak_size - current_with_index_footer
            out_fh.write(b'\x00' * pad_bytes)
            current_offset += pad_bytes
            console.print(f"[bold green][SIZE MATCH] Applied {pad_bytes:,} bytes padding before index -> Repacked PAK matches original ({orig_pak_size:,} bytes)[/bold green]")

        new_idx_offset = current_offset
        new_idx_size = len(index_bytes)
        out_fh.write(index_bytes)
        current_offset += len(index_bytes)

        new_footer = bytearray(orig_fc[-footer_sz:])

        h_key = struct.pack('<5I', *keystream[4:9])
        new_footer[-36:-16] = bytes(a ^ b for a, b in zip(new_sha1, h_key))
        new_footer[-16:-8] = ((new_idx_size ^ (keystream[10] << 32 | keystream[11])).to_bytes(8, 'little'))
        new_footer[-8:] = ((new_idx_offset ^ (keystream[0] << 32 | keystream[1])).to_bytes(8, 'little'))

        out_fh.write(new_footer)

    if os.path.exists(output_path):
        os.remove(output_path)
    os.rename(temp_output_path, output_path)
    gc.collect()

    return len(edited)

def _repack_compressed_with_display(outfh, pak_file, entry, pak_relative_path, new_data, repack_dir, display):
    blocks = entry.compressed_blocks
    enc_method = entry.encryption_method
    comp_method = entry.compression_method
    order = PakCrypto.generate_block_indices(len(blocks), enc_method)
    
    is_path_input = isinstance(new_data, (str, Path))
    if is_path_input:
        p_path = Path(new_data)
        raw_len = p_path.stat().st_size
    else:
        raw_len = len(new_data)
        if raw_len != entry.uncompressed_size:
            if raw_len < entry.uncompressed_size:
                is_text_lua = pak_relative_path.name.lower().endswith(('.lua', '.json', '.txt', '.xml', '.ini', '.csv')) or any(kw in new_data[:100] for kw in [b'function', b'local', b'--', b'return', b'{'])
                pad_byte = b' ' if is_text_lua else b'\x00'
                new_data = new_data.ljust(entry.uncompressed_size, pad_byte)
            else:
                new_data = new_data[:entry.uncompressed_size]
            raw_len = len(new_data)

    if len(blocks) > 1:
        if entry.compression_block_size > 0:
            chunk_size = entry.compression_block_size
        else:
            block_sizes = [blk.end - blk.start for blk in blocks]
            total_block_size = sum(block_sizes)
            avg_block_size = total_block_size / len(blocks)
            avg_compression_ratio = total_block_size / entry.uncompressed_size if entry.uncompressed_size > 0 else 1
            chunk_size = int(avg_block_size / avg_compression_ratio) if avg_compression_ratio > 0 else 65536
        
        ptr = 0
        pf = open(p_path, 'rb') if is_path_input else None
        try:
            for logical_i, phys_i in enumerate(order):
                blk = blocks[phys_i]
                target_size = blk.end - blk.start
                chunk_len = min(chunk_size, raw_len - ptr)
                if chunk_len <= 0: break
                
                if pf:
                    pf.seek(ptr)
                    chunk = pf.read(chunk_len)
                    if len(chunk) < chunk_len:
                        chunk = chunk.ljust(chunk_len, b'\x00')
                else:
                    chunk = new_data[ptr:ptr + chunk_len]
                ptr += chunk_len
                
                with open(pak_file._file_path, 'rb') as src:
                    src.seek(blk.start)
                    original_compressed = src.read(target_size)
                
                compressed_ok = False
                new_compressed = None
                zstd_dict = pak_file._zstd_dict if comp_method == CM_ZSTD_DICT else None
                
                if comp_method in (CM_ZSTD, CM_ZSTD_DICT):
                    for level in [19, 16, 12, 7, 4, 1]:
                        c = ZstdCompressor(level=level, dict_data=zstd_dict, threads=0)
                        new_compressed = c.compress(chunk)
                        if len(new_compressed) <= target_size:
                            compressed_ok = True
                            break
                elif comp_method == CM_ZLIB:
                    new_compressed = zlib.compress(chunk, zlib.Z_BEST_COMPRESSION)
                    if len(new_compressed) <= target_size:
                        compressed_ok = True
                
                if not compressed_ok:
                    outfh.seek(blk.start)
                    outfh.write(original_compressed)
                    display.add_block(logical_i, target_size, False)
                    del original_compressed
                    continue
                
                if entry.encrypted:
                    if PakCrypto._is_sm4_method(enc_method):
                        pad_len = -len(new_compressed) % 16
                        if pad_len > 0: new_compressed += b'\x00' * pad_len
                    new_compressed = _encrypt_plaintext(new_compressed, pak_relative_path, enc_method)
                
                if len(new_compressed) > target_size:
                    outfh.seek(blk.start)
                    outfh.write(original_compressed)
                    display.add_block(logical_i, target_size, False)
                else:
                    outfh.seek(blk.start)
                    outfh.write(new_compressed)
                    if len(new_compressed) < target_size:
                        outfh.write(b'\x00' * (target_size - len(new_compressed)))
                    ratio = len(new_compressed) / len(chunk) if len(chunk) > 0 else 1
                    display.add_block(logical_i, target_size, True, ratio)

                del original_compressed, new_compressed
                if logical_i % 20 == 0:
                    gc.collect()
        finally:
            if pf is not None:
                pf.close()
    else:
        if not blocks: return
        blk = blocks[0]
        target_size = blk.end - blk.start
        
        with open(pak_file._file_path, 'rb') as src:
            src.seek(blk.start)
            original_compressed = src.read(target_size)
        
        compressed_ok = False
        new_compressed = None
        zstd_dict = pak_file._zstd_dict if comp_method == CM_ZSTD_DICT else None
        block_data = Path(new_data).read_bytes() if is_path_input else new_data
        
        if comp_method in (CM_ZSTD, CM_ZSTD_DICT):
            for level in [22, 19, 16, 13, 10, 7, 4, 1]:
                c = ZstdCompressor(level=level, dict_data=zstd_dict, threads=1)
                new_compressed = c.compress(block_data)
                if len(new_compressed) <= target_size:
                    compressed_ok = True
                    break
        elif comp_method == CM_ZLIB:
            new_compressed = zlib.compress(block_data, zlib.Z_BEST_COMPRESSION)
            if len(new_compressed) <= target_size:
                compressed_ok = True
        
        if not compressed_ok:
            outfh.seek(blk.start)
            outfh.write(original_compressed)
            display.add_block(0, target_size, False)
            return
        
        if entry.encrypted:
            if PakCrypto._is_sm4_method(enc_method):
                pad_len = -len(new_compressed) % 16
                if pad_len > 0: new_compressed += b'\x00' * pad_len
            new_compressed = _encrypt_plaintext(new_compressed, pak_relative_path, enc_method)
        
        if len(new_compressed) > target_size:
            outfh.seek(blk.start)
            outfh.write(original_compressed)
            display.add_block(0, target_size, False)
        else:
            outfh.seek(blk.start)
            outfh.write(new_compressed)
            if len(new_compressed) < target_size:
                outfh.write(b'\x00' * (target_size - len(new_compressed)))
            ratio = len(new_compressed) / len(block_data) if len(block_data) > 0 else 1
            display.add_block(0, target_size, True, ratio)

def smart_resolve_by_fingerprint(filename: str, repack_file: Path, candidates: list):
    if not candidates:
        return None
    if len(candidates) == 1:
        return candidates[0]
    
    repack_size = repack_file.stat().st_size
    size_matches = [(path, entry) for path, entry in candidates if entry.uncompressed_size == repack_size]
    if len(size_matches) == 1:
        return size_matches[0]
    if size_matches:
        def fingerprint(e):
            return (e.uncompressed_size, e.size, e.compression_method, len(e.compressed_blocks), e.compression_block_size)
        base_fp = fingerprint(size_matches[0][1])
        final_matches = [(path, entry) for path, entry in size_matches if fingerprint(entry) == base_fp]
        if len(final_matches) == 1:
            return final_matches[0]
    return candidates[0]

def repack_pak_file_with_block_display(pak_file, edited_root: Path, output_path: Path):
    if pak_file._file_path.resolve() != output_path.resolve():
        try:
            shutil.copy2(pak_file._file_path, output_path)
        except Exception:
            pass
    
    pak_name_map = {}
    all_pak_entries = []
    for dir_path, files in pak_file._index.items():
        for name, entry in files.items():
            full_path = str(PurePath(dir_path) / name).replace('\\', '/')
            key = name.lower()
            pak_name_map.setdefault(key, []).append((full_path, entry))
            all_pak_entries.append((full_path, entry))
    
    edited = {}
    ignored_names = {'.ds_store', 'thumbs.db', 'metadata.json', 'desktop.ini', '.gitkeep'}

    sources_to_check = [edited_root]
    sd_repack = Path("/sdcard/FeaturesticLeaks/REPACK") / edited_root.name
    if sd_repack.exists() and sd_repack.resolve() != edited_root.resolve():
        sources_to_check.append(sd_repack)

    valid_files = []
    for src in sources_to_check:
        if src.exists():
            v_files = [p for p in src.rglob('*') if p.is_file() and p.name.lower() not in ignored_names and not p.name.startswith('.')]
            if v_files:
                valid_files = v_files
                edited_root = src
                break

    for p in valid_files:
        fname_lower = p.name.lower()
        rel_path = p.relative_to(edited_root).as_posix().lower()

        if fname_lower in pak_name_map:
            candidates = pak_name_map[fname_lower]
            if len(candidates) == 1:
                full_path, entry = candidates[0]
                edited[full_path] = (p, entry)
            else:
                rel_matched = None
                for full_path, entry in candidates:
                    fp_lower = full_path.lower()
                    if fp_lower.endswith(rel_path) or rel_path.endswith(fp_lower):
                        rel_matched = (full_path, entry)
                        break
                if rel_matched:
                    edited[rel_matched[0]] = (p, rel_matched[1])
                else:
                    resolved = smart_resolve_by_fingerprint(filename=p.name, repack_file=p, candidates=candidates)
                    if resolved:
                        full_path, entry = resolved
                        edited[full_path] = (p, entry)
                    else:
                        full_path, entry = candidates[0]
                        edited[full_path] = (p, entry)
        else:
            rel_matched = None
            for full_path, entry in all_pak_entries:
                fp_lower = full_path.lower()
                if fp_lower.endswith(rel_path) or rel_path.endswith(fp_lower):
                    rel_matched = (full_path, entry)
                    break
            if rel_matched:
                edited[rel_matched[0]] = (p, rel_matched[1])
                continue

            stem = p.stem.lower()
            ext = p.suffix.lower()
            found = False
            
            for full_path, entry in all_pak_entries:
                epath = Path(full_path)
                if epath.stem.lower() == stem and epath.suffix.lower() == ext:
                    edited[full_path] = (p, entry)
                    found = True
                    break
            
            if not found:
                for full_path, entry in all_pak_entries:
                    epath = Path(full_path)
                    if epath.stem.lower() == stem:
                        edited[full_path] = (p, entry)
                        found = True
                        break

            if not found and all_pak_entries:
                ext_match = None
                for full_path, entry in all_pak_entries:
                    if Path(full_path).suffix.lower() == ext:
                        ext_match = (full_path, entry)
                        break
                if ext_match:
                    edited[ext_match[0]] = (p, ext_match[1])
                else:
                    full_path, entry = all_pak_entries[0]
                    edited[full_path] = (p, entry)

    if not edited and all_pak_entries:
        data_path = Path("/sdcard/FeaturesticLeaks")
        unpack_cand = data_path / "UNPACK" / pak_file._file_path.stem
        if unpack_cand.exists():
            v_unpack = [p for p in unpack_cand.rglob('*') if p.is_file() and p.name.lower() not in ignored_names and not p.name.startswith('.')]
            for p in v_unpack:
                fname_lower = p.name.lower()
                if fname_lower in pak_name_map:
                    edited[pak_name_map[fname_lower][0][0]] = (p, pak_name_map[fname_lower][0][1])

    if not edited:
        console.print('[bold red][X] No valid files found to repack in source folder![/bold red]')
        console.print(f'[yellow][!] Please ensure your modified or unpacked files are placed in: {edited_root}[/yellow]')
        raise RuntimeError(f"No files found in source folder '{edited_root.name}' to repack into '{pak_file._file_path.name}'. Please check the folder contents.")
    
    total_files = len(edited)
    display = SimpleBlockDisplay(total_files, pak_file._file_path.name)
    
    with open(output_path, 'r+b') as outfh:
        for full_path, (p, entry) in edited.items():
            file_name = p.name
            total_blocks = len(entry.compressed_blocks) if entry.compressed_blocks else 1
            
            display.start_file(file_name, total_blocks)
            file_sz = p.stat().st_size
            if file_sz >= LARGE_FILE_THRESHOLD:
                new_data = p
            else:
                new_data = p.read_bytes()
            pak_rel = PurePath(full_path)
            
            if entry.compression_method == CM_NONE:
                _repack_uncompressed(outfh, pak_file, entry, pak_rel, new_data)
                display.add_block(0, file_sz if isinstance(new_data, (str, Path)) else len(new_data), True)
            else:
                _repack_compressed_with_display(outfh, pak_file, entry, pak_rel, new_data, edited_root, display)
            
            display.finish_file()
            if not isinstance(new_data, (str, Path)):
                del new_data
            gc.collect()
    
    display.final_summary()

    try:
        if hasattr(pak_file, '_file_path') and os.path.exists(pak_file._file_path):
            orig_sz = os.path.getsize(pak_file._file_path)
            curr_sz = os.path.getsize(output_path) if os.path.exists(output_path) else 0
            if orig_sz > 0 and curr_sz > 0 and curr_sz < orig_sz:
                diff = orig_sz - curr_sz
                with open(output_path, "ab") as out_f:
                    out_f.write(b'\x00' * diff)
                console.print(f"[bold green][SIZE MATCH] Auto-padded {diff:,} bytes -> Repacked PAK matches original ({orig_sz:,} bytes)[/bold green]")
    except Exception:
        pass

def detect_repack_mode(pak_path: Path) -> str:
    name = pak_path.name.lower()
    if name == 'mini_obb.pak':
        return 'MINI_OBB'
    if 'zsdic' in name:
        return 'OBBZSDIC'
    if 'game' in name or 'patch' in name:
        return 'GAMEPATCH'
    return 'OBBZSDIC'

def repack_mini_obb(pak, repack_dir, output_pak):
    console.print('[bold cyan][MODE] Repack Mode: MINI_OBB[/bold cyan]')
    pak._is_zstd_with_dict = False
    pak._zstd_dict = None
    repack_pak_file_with_block_display(pak_file=pak, edited_root=repack_dir, output_path=output_pak)

def repack_obbzsdic(pak, repack_dir, output_pak):
    console.print('[bold cyan][MODE] Repack Mode: OBBZSDIC[/bold cyan]')
    repack_pak_file_with_block_display(pak_file=pak, edited_root=repack_dir, output_path=output_pak)

def repack_gamepatch(pak, repack_dir, output_pak):
    console.print('[bold cyan][MODE] Repack Mode: GAMEPATCH[/bold cyan]')
    pak._is_zstd_with_dict = False
    pak._zstd_dict = None
    repack_pak_file_with_block_display(pak_file=pak, edited_root=repack_dir, output_path=output_pak)
