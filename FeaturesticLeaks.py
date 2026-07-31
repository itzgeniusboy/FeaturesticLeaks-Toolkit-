# FEATURESTIC LEAKS - PAK TOOL v2.0
# Developer Telegram: @L359D (https://t.me/L359D)
# Official Telegram Channel: https://t.me/FeaturesticLeaks
# Termux / Linux Android Game Reverse Engineering & PAK Manipulation Toolkit

#One_Of_The_Best_Tool_In_Whole_Telegram - 100% WORKING FINAL

import itertools as it
import math
import struct
import shutil
import os
import sys
import uuid
import hashlib
import platform
import subprocess
import base64
import zlib
import json
import zipfile
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import PurePath, Path
from typing import List, Dict, Tuple, Optional, Any
import time
import subprocess
import threading
import shutil
import traceback
import gc
import mmap
import concurrent.futures

# ==================== BIG FILE OPTIMIZATION HELPERS ====================

def check_disk_space(target_path: Path, estimated_required_bytes: int) -> bool:
    """
    [BEFORE]: No disk space verification prior to large unpack/repack operations.
    [AFTER]: Checks available disk space on target drive and warns user if free space is below estimated requirement.
    """
    try:
        target_path.mkdir(parents=True, exist_ok=True)
        usage = shutil.disk_usage(target_path)
        if usage.free < estimated_required_bytes:
            req_mb = estimated_required_bytes / (1024 * 1024)
            free_mb = usage.free / (1024 * 1024)
            console.print(f"[bold red][⚠️ DISK SPACE WARNING] Estimated size: {req_mb:.1f} MB, Free space: {free_mb:.1f} MB[/bold red]")
            ans = safe_input("-> Free space is low. Continue anyway? (y/N): ").strip().lower()
            return ans in ['y', 'yes']
    except Exception:
        pass
    return True

def load_checkpoint(checkpoint_file: Path) -> set:
    """
    [BEFORE]: No progress state file; interrupting a long PAK extraction required restarting from scratch.
    [AFTER]: Loads .progress.json state to resume long unpack/repack tasks without re-processing already completed entries.
    """
    if checkpoint_file.exists():
        try:
            data = json.loads(checkpoint_file.read_text(encoding="utf-8"))
            return set(data.get("completed", []))
        except Exception:
            pass
    return set()

def save_checkpoint(checkpoint_file: Path, completed_set: set):
    """Saves progress state to disk."""
    try:
        checkpoint_file.parent.mkdir(parents=True, exist_ok=True)
        checkpoint_file.write_text(json.dumps({"completed": list(completed_set)}), encoding="utf-8")
    except Exception:
        pass

def clear_checkpoint(checkpoint_file: Path):
    """Removes progress state file upon successful completion."""
    try:
        if checkpoint_file.exists():
            checkpoint_file.unlink()
    except Exception:
        pass

# Audio welcome voice playback
_AUDIO_PLAYED = False
def play_welcome_audio():
    global _AUDIO_PLAYED
    if _AUDIO_PLAYED:
        return
    _AUDIO_PLAYED = True
    def _speak():
        msg = "Welcome to Featurestic Leaks World"
        if shutil.which("termux-tts-speak"):
            try:
                subprocess.run(["termux-tts-speak", msg], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                pass
        elif shutil.which("espeak"):
            try:
                subprocess.run(["espeak", msg], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                pass
        elif shutil.which("spd-say"):
            try:
                subprocess.run(["spd-say", msg], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                pass

    threading.Thread(target=_speak, daemon=True).start()

# Auto-install missing dependencies if run directly with python
def _ensure_package(pkg_name, import_name=None):
    if import_name is None:
        import_name = pkg_name
    try:
        __import__(import_name)
    except ImportError:
        print(f"[+] Installing missing dependency: {pkg_name}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg_name])

_ensure_package("rich")
_ensure_package("requests")
import requests
_ensure_package("pytz")
_ensure_package("gmalg")
_ensure_package("pycryptodome", "Crypto")
_ensure_package("zstandard")

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn, TimeRemainingColumn
from rich.table import Table
from rich import print as rprint
from rich.markup import escape
from rich.text import Text
from rich.align import Align
from rich.console import Group
from rich.live import Live
from rich.box import HEAVY_EDGE, ROUNDED, DOUBLE_EDGE
from datetime import datetime
import pytz
import gmalg
from Crypto.Cipher import AES
from Crypto.Cipher.AES import MODE_CBC
from Crypto.Hash import SHA1
from Crypto.Util.Padding import unpad
from zstandard import ZstdDecompressor, ZstdCompressionDict, DICT_TYPE_AUTO, ZstdCompressor

console = Console()

# ==================== SIMPLE BLOCK DISPLAY CLASS ====================

class SimpleBlockDisplay:
    """Simple display that shows each file and its blocks"""
    
    def __init__(self, total_files: int, pak_name: str):
        self.total_files = total_files
        self.pak_name = pak_name
        self.processed_files = 0
        self.current_file = ""
        self.current_file_idx = 0
        self.all_blocks = []  # Store all blocks for final summary
        self.total_fitted = 0
        self.total_skipped = 0
        
    def start_file(self, file_name: str, total_blocks: int):
        self.current_file_idx += 1
        self.current_file = file_name
        self.current_blocks = []
        self.current_total_blocks = total_blocks
        self.current_fitted = 0
        self.current_skipped = 0
        
        # Print file header
        console.print()
        console.print(f"[bold cyan]┌─────────────────────────────────────────────────────────────[/bold cyan]")
        console.print(f"[bold cyan]│[/] [bold yellow][{self.current_file_idx}/{self.total_files}][/] [bold green]{file_name}[/bold green] [dim]({total_blocks} blocks)[/dim]")
        console.print(f"[bold cyan]├─────────────────────────────────────────────────────────────[/bold cyan]")
        
    def add_block(self, block_idx: int, block_size: int, fitted: bool, compression_ratio: float = None):
        """Add a block result"""
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
        """Finish current file"""
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
        """Print final summary"""
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

# ==================== ORIGINAL CLASSES ====================

ZUC_KEY = bytes.fromhex('01010101010101010101010101010101')
ZUC_IV = bytes.fromhex('FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF')

RSA_MOD_1 = bytes.fromhex('CBE8B9F2504050EF9831B719E9A6249A6D238505ADE909BDE78C180DED6072A0C3347B8AF4780E1F212D952D82D4BF7F233C1ECA499E1F9D9A85B4FAD759F54BABC1666C5DE411EA9E4B2374425DD6C6F54333BBC8F2610FE6063E4D0D6C21A671A8F7C3740555E5DC06D4E1691C456DB4116C0C012BF7B206E8311AAAEC689952BF804EF638F09D5822B4117B114208F14DEB459E80CB770E5B0D7978E21F5E6CED4999D3583108221A7AB28B960277ADB5690A332784019D9C195BE4EA9EA0A09459010F236465DE0D59C3EF7324E954E1118D93EE19F299760C2CDB963CE87973EA5ECC9BBE81C27D4C7C8572AC07E9BCEAC9BD72AB7A56A3C0AD736ABCE4')
RSA_MOD_2 = bytes.fromhex('7F58E8A39A4DA4E87357DDD650EAA16D3B5CE95B213D1030A662566444796A78A84AE9AC3DBFFDE7F41094896696835DAF13B89E6EC2B84963B1B1BAF7151DA245C3FBFAE2A6AE18B2684D03F9229DE2C91440F2A3A3BCDE1E5680C16722A88039C73560D5D43F4B6562C2EEA5B1D926D86B51108A2643C70FB74D6442CE3A08339B8FD8F660AE88129B7AB8C46F2FA58124485CCCB1E987B05A6DA65A01858ED3F89905449AE42BB07290FCB9994BF22E26610BCABB9804783A3B9587917F3D97316EDDA15C5E13F79066407B55A93B291B68A4AC42A98D6E35FED84B14A792D154E62028DDAD20FC301951E5924BE9AD62FB719DD94CC30CAB871BEC4377A8')

SIMPLE1_DECRYPT_KEY = 121
SIMPLE2_DECRYPT_KEY = bytes.fromhex('E55B4ED1')
SIMPLE2_BLOCK_SIZE = 16

SM4_SECRET_4 = 'eb691efea914241317a8'
SM4_SECRET_2 = 'Q0hVTKey$as*1ZFlQCiA'
SM4_SECRET_NEW = [
    'xG2qW5lP7lV2iN5fN5pG',
    'xT1cJ6dL5wC0kK1rB4dK',
    'qC4jS5bZ6fL5xE6nD4zA',
    'gD4jQ2aL3bS3lC3xT0iW',
    'xU1yQ8wE9zY3gZ3bT5aE',
    'uQ3cO2dX7xY4xU7gH7iS',
    'gW1fR0jK6wQ4oN0oK1kZ',
    'aJ4pV7iZ7pU4wP2aC2cZ',
    'cX6jT3cM2oT3vK0kJ1qN',
    'iT2vS0cS6yT6cZ1sE1lO',
    'hM1pH9iY8wM9hT4lN5uJ',
    'kG6bC8jK0fL0dE4sH4mL',
    'dB6lB3vE0eZ8wM8rI0aC',
    'tP7sP7nI9rA2vQ4cV5yQ',
    'aT0cL1yN4pT3sZ7eM2vY',
    'uV6fU8fC9zN3mP5dH8mN'
]

EM_SIMPLE1 = 1
EM_SIMPLE2 = 16
EM_SM4_2 = 2
EM_SM4_4 = 4
EM_SM4_NEW_BASE = 31
EM_SM4_NEW_MASK = ~EM_SM4_NEW_BASE
EM_UNKNOWN_17 = 17

CM_NONE = 0
CM_ZLIB = 1
CM_ZSTD = 6
CM_ZSTD_DICT = 8
CM_MASK = 15

class SM4:
    _S_BOX = bytes([
        52, 102, 37, 116, 137, 120, 228, 169, 90, 65, 188, 122, 214, 22, 33, 35,
        77, 97, 218, 148, 155, 223, 19, 60, 105, 58, 49, 10, 95, 215, 153, 149,
        241, 174, 114, 61, 7, 96, 36, 182, 152, 238, 196, 162, 45, 136, 221, 141,
        4, 234, 187, 17, 202, 62, 93, 161, 246, 63, 176, 151, 128, 71, 43, 166,
        230, 247, 217, 177, 89, 192, 124, 190, 84, 40, 183, 126, 79, 248, 67, 110,
        160, 80, 14, 245, 144, 184, 251, 163, 123, 98, 25, 70, 3, 42, 185, 143,
        159, 119, 180, 91, 131, 135, 8, 235, 226, 30, 66, 240, 15, 232, 113, 106,
        117, 173, 85, 31, 181, 171, 51, 250, 127, 21, 189, 133, 216, 6, 104, 179,
        82, 48, 72, 11, 0, 237, 239, 178, 87, 142, 231, 108, 213, 229, 46, 83,
        130, 5, 249, 129, 244, 86, 191, 140, 75, 227, 219, 74, 145, 76, 44, 211,
        64, 41, 78, 32, 20, 54, 121, 9, 111, 209, 55, 224, 57, 12, 138, 146,
        56, 18, 53, 109, 225, 253, 147, 154, 23, 212, 201, 156, 107, 132, 38, 157,
        175, 118, 193, 158, 208, 150, 197, 203, 233, 115, 73, 210, 205, 100, 195, 199,
        1, 125, 243, 172, 252, 222, 164, 68, 50, 27, 194, 186, 28, 2, 198, 39,
        69, 139, 242, 24, 167, 16, 81, 29, 200, 207, 99, 255, 47, 13, 88, 206,
        101, 165, 220, 26, 59, 134, 254, 34, 92, 168, 94, 103, 170, 236, 112, 204
    ])
    _FK = [1184304796, 1270900830, 1493524870, 3164752158]
    _CK = [964907, 973793155, 2654690407, 2916866751, 2071233739, 1226140771, 3348805095, 2045549823, 388349611, 800627875, 612403927, 3721562911, 1195432523, 3150178931, 612053223, 2445162591, 67183755, 1174197155, 1393249511, 3331183455, 3822152747, 1332317203, 1804781383, 1990130463, 1282653851, 3376591251, 2910902311, 925872959, 332098219, 735840931, 396665415, 3588844719]
    
    @staticmethod
    def ROL32(x, n):
        return (x << n) & 0xFFFFFFFF | (x >> (32 - n))
    
    @staticmethod
    def _BS(X):
        return (SM4._S_BOX[X >> 24 & 255] << 24 | 
                SM4._S_BOX[X >> 16 & 255] << 16 | 
                SM4._S_BOX[X >> 8 & 255] << 8 | 
                SM4._S_BOX[X & 255])
    
    @staticmethod
    def _T0(X):
        X = SM4._BS(X)
        return X ^ SM4.ROL32(X, 2) ^ SM4.ROL32(X, 10) ^ SM4.ROL32(X, 18) ^ SM4.ROL32(X, 24)
    
    @staticmethod
    def _T1(X):
        X = SM4._BS(X)
        return X ^ SM4.ROL32(X, 13) ^ SM4.ROL32(X, 23)
    
    @staticmethod
    def _key_expand(key: bytes, rkey: list):
        K0 = int.from_bytes(key[0:4], 'big') ^ SM4._FK[0]
        K1 = int.from_bytes(key[4:8], 'big') ^ SM4._FK[1]
        K2 = int.from_bytes(key[8:12], 'big') ^ SM4._FK[2]
        K3 = int.from_bytes(key[12:16], 'big') ^ SM4._FK[3]
        for i in range(0, 32, 4):
            K0 = K0 ^ SM4._T1(K1 ^ K2 ^ K3 ^ SM4._CK[i])
            rkey[i] = K0
            K1 = K1 ^ SM4._T1(K2 ^ K3 ^ K0 ^ SM4._CK[i + 1])
            rkey[i + 1] = K1
            K2 = K2 ^ SM4._T1(K3 ^ K0 ^ K1 ^ SM4._CK[i + 2])
            rkey[i + 2] = K2
            K3 = K3 ^ SM4._T1(K0 ^ K1 ^ K2 ^ SM4._CK[i + 3])
            rkey[i + 3] = K3
    
    @classmethod
    def key_length(cls):
        return 16
    
    @classmethod
    def block_length(cls):
        return 16
    
    def __init__(self, key: bytes):
        if len(key) != self.key_length():
            raise ValueError(f'Key must be {self.key_length()} bytes')
        else:
            self._key = key
            self._rkey = [0] * 32
            SM4._key_expand(self._key, self._rkey)
            self._block_buffer = bytearray()
    
    def encrypt(self, block: bytes) -> bytes:
        if len(block) != self.block_length():
            raise ValueError(f'Block must be {self.block_length()} bytes')
        else:
            RK = self._rkey
            X0 = int.from_bytes(block[0:4], 'big')
            X1 = int.from_bytes(block[4:8], 'big')
            X2 = int.from_bytes(block[8:12], 'big')
            X3 = int.from_bytes(block[12:16], 'big')
            for i in range(0, 32, 4):
                X0 = X0 ^ SM4._T0(X1 ^ X2 ^ X3 ^ RK[i])
                X1 = X1 ^ SM4._T0(X2 ^ X3 ^ X0 ^ RK[i + 1])
                X2 = X2 ^ SM4._T0(X3 ^ X0 ^ X1 ^ RK[i + 2])
                X3 = X3 ^ SM4._T0(X0 ^ X1 ^ X2 ^ RK[i + 3])
            BUFFER = self._block_buffer
            BUFFER.clear()
            BUFFER.extend(X3.to_bytes(4, 'big'))
            BUFFER.extend(X2.to_bytes(4, 'big'))
            BUFFER.extend(X1.to_bytes(4, 'big'))
            BUFFER.extend(X0.to_bytes(4, 'big'))
            return bytes(BUFFER)
    
    def decrypt(self, block: bytes) -> bytes:
        if len(block) != self.block_length():
            raise ValueError(f'Block must be {self.block_length()} bytes')
        else:
            RK = self._rkey
            X0 = int.from_bytes(block[0:4], 'big')
            X1 = int.from_bytes(block[4:8], 'big')
            X2 = int.from_bytes(block[8:12], 'big')
            X3 = int.from_bytes(block[12:16], 'big')
            for i in range(0, 32, 4):
                X0 = X0 ^ SM4._T0(X1 ^ X2 ^ X3 ^ RK[31 - i])
                X1 = X1 ^ SM4._T0(X2 ^ X3 ^ X0 ^ RK[30 - i])
                X2 = X2 ^ SM4._T0(X3 ^ X0 ^ X1 ^ RK[29 - i])
                X3 = X3 ^ SM4._T0(X0 ^ X1 ^ X2 ^ RK[28 - i])
            BUFFER = self._block_buffer
            BUFFER.clear()
            BUFFER.extend(X3.to_bytes(4, 'big'))
            BUFFER.extend(X2.to_bytes(4, 'big'))
            BUFFER.extend(X1.to_bytes(4, 'big'))
            BUFFER.extend(X0.to_bytes(4, 'big'))
            return bytes(BUFFER)

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

@dataclass
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

class PakCrypto:
    class _LCG:
        def __init__(self, seed: int):
            self.state = seed
        def next(self) -> int:
            MASK_32 = 4294967295
            MSB_1 = 2147483648
            def wrap(x: int) -> int:
                x &= MASK_32
                if not x & MSB_1:
                    return x
                else:
                    return (x + MSB_1 & MASK_32) - MSB_1
            x1 = wrap(1103515245 * self.state)
            self.state = wrap(x1 + 12345)
            x2 = wrap(x1 + 77880) if self.state < 0 else self.state
            return (x2 >> 16 & MASK_32) % 32767
    @staticmethod
    def zuc_keystream() -> List[int]:
        zuc = gmalg.ZUC(ZUC_KEY, ZUC_IV)
        return [struct.unpack('>I', zuc.generate())[0] for _ in range(16)]
    @staticmethod
    def _xorxor(buffer, x) -> bytes:
        return bytes((buffer[i] ^ x[i % len(x)] for i in range(len(buffer))))
    @staticmethod
    def _hashhash(buffer, n: int) -> bytes:
        result = bytes()
        for i in range(math.ceil(n / SHA1.digest_size)):
            result += SHA1.new(buffer).digest()
        if len(result) >= n:
            result = result[:n]
            return result
        else:
            result += b'\x00' * (n - len(result))
            return result
    @staticmethod
    def _meowmeow(buffer) -> bytes:
        def unpad(x):
            skip = 1 + next((i for i in range(len(x)) if x[i]!= 0))
            return x[skip:]
        if len(buffer) < 43:
            return bytes()
        else:
            x1 = buffer[1:][:SHA1.digest_size]
            x2 = buffer[SHA1.digest_size + 1:]
            x1 = PakCrypto._xorxor(x1, PakCrypto._hashhash(x2, len(x1)))
            x2 = PakCrypto._xorxor(x2, PakCrypto._hashhash(x1, len(x2)))
            part1, m = (x2[:SHA1.digest_size], x2[SHA1.digest_size:])
            if part1!= SHA1.new(b'\x00' * SHA1.digest_size).digest():
                return bytes()
            else:
                return unpad(m)
    @staticmethod
    def rsa_extract(signature: bytes, modulus: bytes) -> bytes:
        c = int.from_bytes(signature, 'little')
        n = int.from_bytes(modulus, 'little')
        e = 65537
        m = pow(c, e, n).to_bytes(256, 'little').rstrip(b'\x00')
        return PakCrypto._meowmeow(Misc.pad_to_n(m, 4))
    @staticmethod
    def _decrypt_simple1(ciphertext) -> bytes:
        return bytes((x ^ SIMPLE1_DECRYPT_KEY for x in ciphertext))
    @staticmethod
    def _decrypt_simple2(ciphertext) -> bytes:
        class RollingKey:
            def __init__(self, initial_value: int):
                self._value = initial_value
            def update(self, x: int) -> int:
                self._value ^= x
                return self._value
        assert len(ciphertext) % SIMPLE2_BLOCK_SIZE == 0, "Simple2 ciphertext length is not aligned to block size"
        initial_key, = struct.unpack('<I', SIMPLE2_DECRYPT_KEY)
        rolling_key = RollingKey(initial_key)
        plaintext = (struct.pack('<I', rolling_key.update(x)) for x in struct.unpack(f'<{len(ciphertext) // 4}I', ciphertext))
        return bytes(it.chain.from_iterable(plaintext))
    @staticmethod
    @lru_cache(maxsize=1)
    def _derive_sm4_key(file_path: PurePath, encryption_method: int) -> bytes:
        part1 = file_path.stem.lower()
        if encryption_method == EM_SM4_2:
            secret = SM4_SECRET_2
        else:
            if encryption_method == EM_SM4_4:
                secret = SM4_SECRET_4
            else:
                index = (encryption_method - EM_SM4_NEW_BASE) % len(SM4_SECRET_NEW)
                secret = f'{SM4_SECRET_NEW[index]}{encryption_method}'
        return SHA1.new(str(part1 + secret).encode()).digest()[:SM4.key_length()]
    @staticmethod
    @lru_cache(maxsize=1)
    def _sm4_context_for_key(key: bytes) -> SM4:
        return SM4(key)
    @staticmethod
    def _decrypt_sm4(ciphertext, file_path: PurePath, encryption_method: int) -> bytes:
        assert len(ciphertext) % SM4.block_length() == 0, "SM4 ciphertext length is not aligned to block size"
        key = PakCrypto._derive_sm4_key(file_path, encryption_method)
        sm4 = PakCrypto._sm4_context_for_key(key)
        return bytes(it.chain.from_iterable((sm4.decrypt(x) for x in it.batched(ciphertext, SM4.block_length()))))
    @staticmethod
    def decrypt_index(ciphertext, pak_info: TencentPakInfo) -> bytes:
        if pak_info.version > 7:
            key = PakCrypto.rsa_extract(pak_info.packed_key, RSA_MOD_1)
            iv = PakCrypto.rsa_extract(pak_info.packed_iv, RSA_MOD_1)
            assert len(key) == 32 and len(iv) == 32, "SM4 key and IV length must be 32 bytes"
            aes = AES.new(key, MODE_CBC, iv[:16])
            return unpad(aes.decrypt(ciphertext), AES.block_size)
        else:
            return bytes(PakCrypto._decrypt_simple1(ciphertext))
    @staticmethod
    def _is_simple1_method(encryption_method: int) -> bool:
        return encryption_method == EM_SIMPLE1
    @staticmethod
    def _is_simple2_method(encryption_method: int) -> bool:
        return encryption_method == EM_SIMPLE2 or encryption_method == 17
    @staticmethod
    def _is_sm4_method(encryption_method: int) -> bool:
        return encryption_method == EM_SM4_2 or encryption_method == EM_SM4_4 or encryption_method & EM_SM4_NEW_MASK!= 0
    @staticmethod
    def align_encrypted_content_size(n: int, encryption_method: int) -> int:
        if PakCrypto._is_simple2_method(encryption_method):
            return Misc.align_up(n, SIMPLE2_BLOCK_SIZE)
        else:
            if PakCrypto._is_sm4_method(encryption_method):
                return Misc.align_up(n, SM4.block_length())
            else:
                return n
    @staticmethod
    def decrypt_block(ciphertext, file: PurePath, encryption_method: int) -> bytes:
        if PakCrypto._is_simple1_method(encryption_method):
            return PakCrypto._decrypt_simple1(ciphertext)
        else:
            if PakCrypto._is_simple2_method(encryption_method):
                return PakCrypto._decrypt_simple2(ciphertext)
            else:
                if PakCrypto._is_sm4_method(encryption_method):
                    return PakCrypto._decrypt_sm4(ciphertext, file, encryption_method)
                else:
                    raise ValueError(f'Unknown encryption method: {encryption_method}')
    @staticmethod
    @lru_cache(maxsize=33)
    def generate_block_indices(n: int, encryption_method: int) -> List[int]:
        if not PakCrypto._is_sm4_method(encryption_method):
            return list(range(n))
        else:
            permutation = []
            lcg = PakCrypto._LCG(n)
            while len(permutation)!= n:
                x = lcg.next() % n
                if x not in permutation:
                    permutation.append(x)
            inverse = [0] * len(permutation)
            for i, x in enumerate(permutation):
                inverse[x] = i
            return inverse

class PakCompression:
    @staticmethod
    @lru_cache(maxsize=33)
    def _zstd_decompressor(dict: ZstdCompressionDict) -> ZstdDecompressor:
        return ZstdDecompressor(dict)
    @staticmethod
    def zstd_dictionary(dict_data) -> ZstdCompressionDict:
        return ZstdCompressionDict(dict_data, DICT_TYPE_AUTO)
    @staticmethod
    def decompress_block(block, dict: Optional[ZstdCompressionDict], compression_method: int) -> bytes:
        if compression_method == CM_ZLIB:
            try:
                return zlib.decompress(block)
            except zlib.error:
                return block
        else:
            if compression_method == CM_ZSTD or compression_method == CM_ZSTD_DICT:
                if compression_method!= CM_ZSTD_DICT:
                    dict = None
                return PakCompression._zstd_decompressor(dict).decompress(block)
            else:
                raise ValueError(f'Unknown compression method: {compression_method}')

class TencentPakFile:
    def __init__(self, file_path: PurePath, is_od=False):
        self._file_path = file_path
        # [BEFORE]: Read entire PAK into heap RAM with file.read() causing MemoryError on 2GB-10GB+ files.
        # [AFTER]: Use mmap.mmap for zero-heap memoryview access backed by OS virtual memory pages.
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
                assert self._pak_info.stem_hash == zlib.crc32(self._file_path.stem.encode('utf-32le')), "PAK filename stem CRC32 hash mismatch — invalid PAK stem"
    def _tencent_load_index(self) -> None:
        index_data = self._file_content[self._pak_info.index_offset:][:self._pak_info.index_size]
        if self._pak_info.index_encrypted:
            index_data = PakCrypto.decrypt_index(index_data, self._pak_info)
        else:
            index_data = index_data
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
        assert expected_hash == SHA1.new(index_data).digest(), "SHA1 index hash mismatch — PAK header or key corrupt"
    @staticmethod
    def _construct_mount_point(mount_point: str) -> PurePath:
        result = PurePath()
        for part in PurePath(mount_point).parts:
            if part!= '..':
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
    
    def _write_to_disk(self, file_path: Path, entry: TencentPakEntry) -> None:
        """
        [BEFORE]: Uncompressed files loaded full content into RAM before writing to disk.
        [AFTER]: Streaming chunked writes (64MB chunks) for uncompressed data and per-block stream writes to minimize memory footprint.
        """
        encryption_method = entry.encryption_method
        compression_method = entry.compression_method

        enc_str = self._get_method_str(encryption_method, True)
        comp_str = self._get_method_str(compression_method, False)
        console.print(f"[bold cyan]->[/] Unpack: [bold green]{file_path.name}[/] [[bold yellow]{comp_str}[/]/[bold magenta]{enc_str}[/]]")

        with open(file_path, 'wb') as file:
            if compression_method == CM_NONE:
                offset = entry.offset
                total_size = PakCrypto.align_encrypted_content_size(entry.size, encryption_method)
                chunk_size = 64 * 1024 * 1024  # 64MB streaming chunk buffer
                written = 0
                while written < total_size:
                    to_read = min(chunk_size, total_size - written)
                    data = self._file_content[offset + written:][:to_read]
                    if entry.encrypted:
                        data = PakCrypto.decrypt_block(data, file_path, encryption_method)
                    file.write(data)
                    written += to_read
                return
            else:
                for x in PakCrypto.generate_block_indices(len(entry.compressed_blocks), encryption_method):
                    data = self._peek_block_content(entry.compressed_blocks[x], encryption_method)
                    if entry.encrypted:
                        data = PakCrypto.decrypt_block(data, file_path, encryption_method)
                    data = PakCompression.decompress_block(data, self._zstd_dict, compression_method)
                    file.write(data)
    
    def dump(self, out_path: Path) -> None:
        """
        [BEFORE]: Unpacked sequentially without disk space check, resume checkpoints, error isolation, or garbage collection.
        [AFTER]: Added pre-unpack disk space check, .progress.json checkpointing for resume support, per-entry corruption exception isolation, and periodic gc.collect().
        """
        out_path = out_path / self._mount_point
        out_path.mkdir(parents=True, exist_ok=True)
        total_files = sum(len(d) for d in self._index.values())

        # Check target disk space before unpacking
        total_uncompressed_bytes = sum(entry.uncompressed_size for d in self._index.values() for entry in d.values())
        if not check_disk_space(out_path, total_uncompressed_bytes):
            console.print("[yellow][!] Extraction stopped due to disk space warning.[/yellow]")
            return

        checkpoint_file = out_path.parent / ".unpack_progress.json"
        completed = load_checkpoint(checkpoint_file)

        processed_count = 0
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold cyan][UNPACK][/] {task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            task = progress.add_task("Extracting files...", total=total_files)
            for dir_path, dir_content in self._index.items():
                current_out_path = out_path / dir_path
                current_out_path.mkdir(parents=True, exist_ok=True)
                for file_name, entry in dir_content.items():
                    rel_file_key = str(PurePath(dir_path) / file_name).replace('\\', '/')
                    if rel_file_key in completed:
                        progress.update(task, advance=1)
                        continue

                    target_file = current_out_path / file_name
                    try:
                        self._write_to_disk(target_file, entry)
                        completed.add(rel_file_key)
                    except Exception as entry_err:
                        console.print(f"[bold red][X] Skip corrupted entry '{rel_file_key}': {entry_err}[/bold red]")

                    processed_count += 1
                    if processed_count % 50 == 0:
                        save_checkpoint(checkpoint_file, completed)
                        gc.collect()

                    progress.update(task, advance=1)

        clear_checkpoint(checkpoint_file)
        gc.collect()

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

# ==================== WORKING REPACK FUNCTIONS ====================

def _repack_uncompressed(outfh, pak_file, entry, pak_relative_path: PurePath, new_data: bytes):
    enc_method = entry.encryption_method
    target_size = entry.size
    enc_region = PakCrypto.align_encrypted_content_size(target_size, enc_method) if entry.encrypted else target_size
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
    """
    [BEFORE]: Sequential ZSTD compression levels (22 -> 1) on single thread, very slow for large chunks.
    [AFTER]: Multi-threaded Zstandard compressor with fast-scan compression level fallback.
    """
    if cm == CM_ZLIB:
        return zlib.compress(chunk, 9)
    if cm in (CM_ZSTD, CM_ZSTD_DICT):
        zd = zstd_dict if cm == CM_ZSTD_DICT else None
        for lvl in [19, 12, 7, 3, 1]:
            try:
                return ZstdCompressor(level=lvl, dict_data=zd, threads=0).compress(chunk)
            except Exception:
                continue
    return chunk  # fallback: store raw

def _stream_copy_bytes(src_file_path: PurePath, offset: int, length: int, dst_fh) -> None:
    """Streams bytes from src_file_path to dst_fh in 16MB chunks to avoid RAM allocation."""
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
    """PAK string serialiser: i4(len_with_null) + bytes + null."""
    if not s: return struct.pack('<i', 0)
    b = s.encode('utf-8') + b'\x00'
    return struct.pack('<i', len(b)) + b

def _pw_entry(e, v):
    """Serialise one TencentPakEntry back to bytes."""
    w = bytearray(e.content_hash)
    w += struct.pack('<Q', e.offset)
    w += struct.pack('<Q', e.uncompressed_size)
    w += struct.pack('<I', e.compression_method)
    w += struct.pack('<Q', e.size)
    if v >= 5:
        w += bytes([e.unk1])
        w += e.unk2  # 20 bytes
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
    """Re-parse raw (possibly encrypted) index → (mount_point_str, ordered dirs dict)."""
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
    """
    [BEFORE]: Constructed full PAK in bytearray memory buffer (out_buf), crashing RAM on 2GB-10GB+ files.
    [AFTER]: Streamed output file handle writes, chunked streaming copy for unchanged PAK blocks, disk space checks, entry-level error isolation, and garbage collection.
    """
    import copy as _cp

    console.print(f'[bold cyan][BUILD] Full PAK Rebuild mode[/bold cyan]')
    if target_path:
        console.print(f'[bold cyan][TARGET] Target path: {target_path}[/bold cyan]')
    
    # Check disk space before full rebuild
    estimated_out_size = os.path.getsize(pak_file._file_path) if os.path.exists(pak_file._file_path) else 1024 * 1024 * 100
    if not check_disk_space(Path(output_path).parent, estimated_out_size):
        console.print("[yellow][!] Repack cancelled due to disk space warning.[/yellow]")
        return 0

    # Get all files from edit folder or file
    edit_files = []
    edit_p = Path(edited_root)
    if edit_p.is_file():
        edit_files.append(edit_p)
    elif edit_p.is_dir():
        for p in edit_p.rglob('*'):
            if p.is_file():
                edit_files.append(p)
    
    if not edit_files:
        console.print(f'[bold red][X] Source folder ({edited_root}) me koi file nahi mili. Pehle files is folder me daalo.[/bold red]')
        return 0
    
    console.print(f'[bold cyan][+] Found {len(edit_files)} file(s) to process[/bold cyan]')

    version = pak_file._pak_info.version
    keystream = PakCrypto.zuc_keystream()
    orig_fc = pak_file._file_content

    # Get existing directory structure
    mp_str, all_dirs = _get_all_dirs_and_mp(pak_file)

    # Normalize target_path to match exact case and slashes of existing dirs
    if target_path and force_add:
        target_path = target_path.replace('\\', '/')
        matched_dir = None
        for existing_dir in all_dirs.keys():
            if existing_dir.strip('/').lower() == target_path.strip('/').lower():
                matched_dir = existing_dir
                break
        if matched_dir:
            target_path = matched_dir # Use the exact string from the PAK
        else:
            target_path = target_path.strip('/') + '/' # Ensure standard trailing slash
    
    # Build name→entry map
    pak_name_map = {}
    for dir_path, files in pak_file._index.items():
        for name, entry in files.items():
            full_path = str(PurePath(dir_path)/name).replace('\\', '/')
            pak_name_map.setdefault(name.lower(), []).append((full_path, entry))

    # Find matching files
    edited = {}
    
    for p in edit_files:
        fl = p.name.lower()
        
        if force_add and target_path:
            new_fp = f"{target_path.rstrip('/')}/{p.name}"
            
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
                        new_raw = p.read_bytes()
                        pak_rel = PurePath(full_path)

                        ne.content_hash = SHA1.new(new_raw).digest()
                        ne.uncompressed_size = len(new_raw)
                        ne.compression_method = template.compression_method if template else cm
                        ne.encryption_method = template.encryption_method if template else em
                        ne.encrypted = template.encrypted if template else old_entry.encrypted
                        ne.unk1 = template.unk1 if template else old_entry.unk1
                        
                        if template and target_path:
                            full_path_str = mp_str + full_path
                            ne.unk2 = SHA1.new(full_path_str.lower().encode('utf-8')).digest()
                        else:
                            ne.unk2 = template.unk2 if template else old_entry.unk2
                            
                        ne.index_new_sep = template.index_new_sep if template else old_entry.index_new_sep

                        if ne.compression_method == CM_NONE:
                            cipher = (_encrypt_plaintext(new_raw, pak_rel, ne.encryption_method)
                                      if ne.encrypted else new_raw)
                            ne.offset = current_offset
                            ne.size = len(new_raw)
                            ne.uncompressed_size = len(new_raw)
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
                            ne.uncompressed_size = len(new_raw)

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
                        new_raw = p.read_bytes()
                        pak_rel = PurePath(fp)
                        
                        ne.content_hash = SHA1.new(new_raw).digest()
                        ne.uncompressed_size = len(new_raw)
                        ne.compression_method = template.compression_method
                        ne.encryption_method = template.encryption_method
                        ne.encrypted = template.encrypted
                        ne.unk1 = template.unk1
                        
                        full_path_str = mp_str + fp
                        ne.unk2 = SHA1.new(full_path_str.lower().encode('utf-8')).digest()
                        
                        ne.index_new_sep = template.index_new_sep

                        if ne.compression_method == CM_NONE:
                            cipher = (_encrypt_plaintext(new_raw, pak_rel, ne.encryption_method)
                                      if ne.encrypted else new_raw)
                            ne.offset = current_offset
                            ne.size = len(new_raw)
                            ne.uncompressed_size = len(new_raw)
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
                            ne.uncompressed_size = len(new_raw)

                        new_files.append(ne)
                        
                        if target_path not in all_dirs:
                            all_dirs[target_path] = {}
                        all_dirs[target_path][p.name] = ne
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
            aes = AES.new(key, MODE_CBC, iv[:16])
            pad = (-len(index_plain)) % AES.block_size or AES.block_size
            index_bytes = aes.encrypt(index_plain + bytes([pad] * pad))
        else:
            index_bytes = index_plain

        new_idx_offset = current_offset
        new_idx_size = len(index_bytes)
        out_fh.write(index_bytes)
        current_offset += len(index_bytes)

        footer_sz = TencentPakInfo._mem_size(version)
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
    """
    [BEFORE]: Processed blocks without garbage collection, keeping temporary buffers in memory during long repacks.
    [AFTER]: Added explicit buffer deletion and gc.collect() calls after block processing.
    """
    blocks = entry.compressed_blocks
    enc_method = entry.encryption_method
    comp_method = entry.compression_method
    order = PakCrypto.generate_block_indices(len(blocks), enc_method)
    
    if len(new_data) != entry.uncompressed_size:
        if len(new_data) < entry.uncompressed_size:
            new_data = new_data.ljust(entry.uncompressed_size, b'\x00')
        else:
            new_data = new_data[:entry.uncompressed_size]

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
        for logical_i, phys_i in enumerate(order):
            blk = blocks[phys_i]
            target_size = blk.end - blk.start
            chunk_len = min(chunk_size, len(new_data) - ptr)
            if chunk_len <= 0: break
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
    else:
        if not blocks: return
        blk = blocks[0]
        target_size = blk.end - blk.start
        
        with open(pak_file._file_path, 'rb') as src:
            src.seek(blk.start)
            original_compressed = src.read(target_size)
        
        compressed_ok = False
        new_compressed = None
    enc_method = entry.encryption_method
    comp_method = entry.compression_method
    order = PakCrypto.generate_block_indices(len(blocks), enc_method)
    
    if len(new_data) != entry.uncompressed_size:
        if len(new_data) < entry.uncompressed_size:
            new_data = new_data.ljust(entry.uncompressed_size, b'\x00')
        else:
            new_data = new_data[:entry.uncompressed_size]

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
        for logical_i, phys_i in enumerate(order):
            blk = blocks[phys_i]
            target_size = blk.end - blk.start
            chunk_len = min(chunk_size, len(new_data) - ptr)
            if chunk_len <= 0: break
            chunk = new_data[ptr:ptr + chunk_len]
            ptr += chunk_len
            
            with open(pak_file._file_path, 'rb') as src:
                src.seek(blk.start)
                original_compressed = src.read(target_size)
            
            compressed_ok = False
            new_compressed = None
            zstd_dict = pak_file._zstd_dict if comp_method == CM_ZSTD_DICT else None
            
            if comp_method in (CM_ZSTD, CM_ZSTD_DICT):
                for level in [22, 19, 16, 13, 10, 7, 4, 1]:
                    c = ZstdCompressor(level=level, dict_data=zstd_dict, threads=1)
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
        
        if comp_method in (CM_ZSTD, CM_ZSTD_DICT):
            for level in [22, 19, 16, 13, 10, 7, 4, 1]:
                c = ZstdCompressor(level=level, dict_data=zstd_dict, threads=1)
                new_compressed = c.compress(new_data)
                if len(new_compressed) <= target_size:
                    compressed_ok = True
                    break
        elif comp_method == CM_ZLIB:
            new_compressed = zlib.compress(new_data, zlib.Z_BEST_COMPRESSION)
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
            ratio = len(new_compressed) / len(new_data) if len(new_data) > 0 else 1
            display.add_block(0, target_size, True, ratio)

def smart_resolve_by_fingerprint(filename: str, repack_file: Path, candidates: list):
    repack_size = repack_file.stat().st_size
    size_matches = [(path, entry) for path, entry in candidates if entry.uncompressed_size == repack_size]
    if len(size_matches) == 1:
        return size_matches[0]
    if not size_matches:
        return None
    def fingerprint(e):
        return (e.uncompressed_size, e.size, e.compression_method, len(e.compressed_blocks), e.compression_block_size)
    base_fp = fingerprint(size_matches[0][1])
    final_matches = [(path, entry) for path, entry in size_matches if fingerprint(entry) == base_fp]
    if len(final_matches) == 1:
        return final_matches[0]
    return None

def repack_pak_file_with_block_display(pak_file, edited_root: Path, output_path: Path):
    """Original repack with simple block display"""
    shutil.copy2(pak_file._file_path, output_path)
    
    pak_name_map = {}
    for dir_path, files in pak_file._index.items():
        for name, entry in files.items():
            full_path = str(PurePath(dir_path) / name).replace('\\', '/')
            key = name.lower()
            pak_name_map.setdefault(key, []).append((full_path, entry))
    
    edited = {}
    for p in edited_root.rglob('*'):
        if not p.is_file():
            continue
        fname_lower = p.name.lower()
        if fname_lower in pak_name_map:
            candidates = pak_name_map[fname_lower]
            if len(candidates) == 1:
                full_path, entry = candidates[0]
                edited[full_path] = (p, entry)
            else:
                resolved = smart_resolve_by_fingerprint(filename=p.name, repack_file=p, candidates=candidates)
                if resolved:
                    full_path, entry = resolved
                    edited[full_path] = (p, entry)
        else:
            stem = p.stem.lower()
            ext = p.suffix.lower()
            for dir_path, files in pak_file._index.items():
                for name, entry in files.items():
                    if Path(name).stem.lower() == stem and Path(name).suffix.lower() == ext:
                        full_path = str(PurePath(dir_path) / name).replace('\\', '/')
                        edited[full_path] = (p, entry)
                        break
    
    if not edited:
        console.print('[bold red][X] No files to repack![/bold red]')
        return
    
    total_files = len(edited)
    display = SimpleBlockDisplay(total_files, pak_file._file_path.name)
    
    with open(output_path, 'r+b') as outfh:
        for full_path, (p, entry) in edited.items():
            file_name = p.name
            total_blocks = len(entry.compressed_blocks) if entry.compressed_blocks else 1
            
            display.start_file(file_name, total_blocks)
            new_data = p.read_bytes()
            pak_rel = PurePath(full_path)
            
            if entry.compression_method == CM_NONE:
                _repack_uncompressed(outfh, pak_file, entry, pak_rel, new_data)
                display.add_block(0, len(new_data), True)
            else:
                _repack_compressed_with_display(outfh, pak_file, entry, pak_rel, new_data, edited_root, display)
            
            display.finish_file()
            del new_data
            gc.collect()
    
    display.final_summary()

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

def ensure_directories(base_dir: Path):
    (base_dir / "PAK").mkdir(parents=True, exist_ok=True)
    (base_dir / "UNPACK").mkdir(parents=True, exist_ok=True)
    (base_dir / "REPLACE").mkdir(parents=True, exist_ok=True)
    (base_dir / "INJECT").mkdir(parents=True, exist_ok=True)
    (base_dir / "LUA").mkdir(parents=True, exist_ok=True)
    (base_dir / "REPACK").mkdir(parents=True, exist_ok=True)
    (base_dir / "RESULT").mkdir(parents=True, exist_ok=True)
    (base_dir / "LOGS").mkdir(parents=True, exist_ok=True)
    
    # Backwards compatibility legacy paths
    pak_tool_dir = base_dir / "PAK TOOL"
    (pak_tool_dir / "EDIT").mkdir(parents=True, exist_ok=True)
    (pak_tool_dir / "UNPACK").mkdir(parents=True, exist_ok=True)
    (pak_tool_dir / "RESULT").mkdir(parents=True, exist_ok=True)
    (pak_tool_dir / "PAK").mkdir(parents=True, exist_ok=True)

    sdcard_path = Path("/sdcard/FeaturesticLeaks")
    try:
        if sdcard_path.parent.exists():
            sdcard_path.mkdir(parents=True, exist_ok=True)
            (sdcard_path / "PAK").mkdir(parents=True, exist_ok=True)
            (sdcard_path / "UNPACK").mkdir(parents=True, exist_ok=True)
            (sdcard_path / "REPLACE").mkdir(parents=True, exist_ok=True)
            (sdcard_path / "INJECT").mkdir(parents=True, exist_ok=True)
            (sdcard_path / "LUA").mkdir(parents=True, exist_ok=True)
            (sdcard_path / "RESULT").mkdir(parents=True, exist_ok=True)
            (sdcard_path / "LOGS").mkdir(parents=True, exist_ok=True)
    except Exception:
        pass

def display_workspace_summary(data_path: Path):
    sd_path = Path("/sdcard/FeaturesticLeaks")
    
    def get_cnt(folder_name: str, subfolder: str = "") -> int:
        cnt = 0
        paths = []
        p1 = data_path / folder_name
        if subfolder: p1 = p1 / subfolder
        paths.append(p1)
        
        if sd_path.exists():
            p2 = sd_path / folder_name
            if subfolder: p2 = p2 / subfolder
            paths.append(p2)
            
        for p in paths:
            if p.exists():
                try:
                    cnt += len([f for f in p.rglob("*") if f.is_file()])
                except Exception:
                    pass
        return cnt

    pak_cnt = get_cnt("PAK")
    unpack_cnt = get_cnt("UNPACK")
    replace_cnt = get_cnt("REPLACE") + get_cnt("PAK TOOL", "EDIT")
    inject_cnt = get_cnt("INJECT")
    lua_cnt = get_cnt("LUA")
    result_cnt = get_cnt("RESULT")

    table = Table(
        title="[bold green]🟢 WORKSPACE STATUS & FILES 🟢[/bold green]",
        border_style="green",
        box=ROUNDED,
        show_header=True,
        header_style="bold green",
        expand=True
    )
    table.add_column("Folder Name", justify="left", style="bold green", width=14)
    table.add_column("Where to Put / Purpose", justify="left", style="bold white")
    table.add_column("Files Found", justify="center", style="bold bright_green", width=12)

    table.add_row("📥 PAK/", "Put original game .pak / .obb files here", f"[bold bright_green]{pak_cnt}[/bold bright_green]")
    table.add_row("📂 UNPACK/", "Extracted files from Unpack tool", f"[bold bright_green]{unpack_cnt}[/bold bright_green]")
    table.add_row("✏️ REPLACE/", "Put edited files here to replace existing PAK files", f"[bold bright_green]{replace_cnt}[/bold bright_green]")
    table.add_row("💉 INJECT/", "Put custom files here for Inject Path mode", f"[bold bright_green]{inject_cnt}[/bold bright_green]")
    table.add_row("🌙 LUA/", "Put .lua / .luac scripts here for Lua tools", f"[bold bright_green]{lua_cnt}[/bold bright_green]")
    table.add_row("🚀 RESULT/", "Final repacked PAK, OBB & compiled files saved here", f"[bold bright_green]{result_cnt}[/bold bright_green]")

    console.print(table)
    console.print("[bold green]💡 SDCard Location: [bold white]/sdcard/FeaturesticLeaks/[/bold white] (ZArchiver / File Manager me direct dikhega)[/bold green]\n")

# ============================================================================
# LUA ENGINE & PSEUDO-DECOMPILER (Pure Python + External Tools Fallback)
# ============================================================================

_LUA_K_KEY = bytes.fromhex("112136474657a78d9d8490d8ab008c35261af7e45805b8b31507d02c1e8ff6c8")

_LUA_CUSTOM_TO_STD = {
    17:0,  18:1,  3:3,   21:4,  22:5,  23:6,  24:7,  8:8,
    27:10, 28:11, 29:12, 13:13, 14:14, 2:15,  5:18,
    20:28, 16:29, 25:25, 26:27, 30:30, 31:31, 32:32,
    33:33, 34:34, 35:35, 36:36, 37:37, 38:38, 39:39,
    40:40, 41:41, 42:42, 43:43, 44:44, 45:45, 46:46
}
_LUA_STD_TO_CUSTOM = {v: k for k, v in _LUA_CUSTOM_TO_STD.items()}

_LUA_NIL   = 0
_LUA_BOOL  = 1
_LUA_NUM   = 3
_LUA_FLOAT = 19
_LUA_STR   = 4
_LUA_STRL  = 20

_LUA53_OPCODES = [
    "MOVE", "LOADK", "LOADKX", "LOADBOOL", "LOADNIL", "GETUPVAL",
    "GETTABUP", "GETTABLE", "SETTABUP", "SETUPVAL", "SETTABLE",
    "NEWTABLE", "SELF", "ADD", "SUB", "MUL", "MOD", "POW",
    "DIV", "IDIV", "BAND", "BOR", "BXOR", "SHL", "SHR",
    "UNM", "BNOT", "NOT", "LEN", "CONCAT", "JMP", "EQ",
    "LT", "LE", "TEST", "TESTSET", "CALL", "TAILCALL", "RETURN",
    "FORLOOP", "FORPREP", "TFORCALL", "TFORLOOP", "SETLIST",
    "CLOSURE", "VARARG", "EXTRAARG"
]

def _lua_xor(data, key):
    return bytes([data[i] ^ key[i % len(key)] for i in range(len(data))])

class _LuaCustomReader:
    def __init__(self, d, k):
        self.d = d
        self.pos = 0
        self.k = k

    def read(self, n):
        v = bytes(self.d[self.pos:self.pos + n])
        self.pos += n
        return v

    def byte(self):
        v = self.d[self.pos]
        self.pos += 1
        return v

    def i32(self):
        v = struct.unpack_from('<i', self.d, self.pos)[0]
        self.pos += 4
        return v

    def i64(self):
        v = struct.unpack_from('<q', self.d, self.pos)[0]
        self.pos += 8
        return v

    def dbl(self):
        v = struct.unpack_from('<d', self.d, self.pos)[0]
        self.pos += 8
        return v

    def string(self):
        if self.pos >= len(self.d):
            return None
        sz = self.byte()
        if sz == 0:
            return None
        if sz == 0xFF:
            if self.pos + 8 > len(self.d): return None
            sz = struct.unpack_from('<Q', self.d, self.pos)[0]
            self.pos += 8
        if self.pos + sz - 1 > len(self.d):
            return None
        raw = bytes(self.d[self.pos:self.pos + sz - 1])
        self.pos += sz - 1
        b = _lua_xor(raw, self.k)
        try:
            return b.decode('utf-8')
        except Exception:
            return b.decode('latin-1', errors='replace')

class _LuaProto:
    __slots__ = ('src', 'ld', 'll', 'np', 'va', 'ms', 'ins', 'K', 'upvals', 'upvs', 'locs', 'subs')
    def __init__(self):
        self.src = None
        self.ld = 0; self.ll = 0
        self.np = 0; self.va = 0; self.ms = 0
        self.ins = []
        self.K = []
        self.upvals = b''
        self.upvs = []
        self.locs = []
        self.subs = []

def _parse_lua_custom(r):
    p = _LuaProto()
    try:
        p.src = r.string()
        p.ld = r.i32()
        p.ll = r.i32()
        p.np = r.byte()
        p.va = r.byte()
        p.ms = r.byte()

        n = r.i32()
        p.ins = [struct.unpack_from('<I', r.read(4))[0] for _ in range(n)]

        n = r.i32()
        for _ in range(n):
            t = r.byte()
            if t == _LUA_NIL:
                p.K.append(('nil', None))
            elif t == _LUA_BOOL:
                b = r.byte()
                p.K.append(('bool', bool(b)))
            elif t == _LUA_NUM:
                raw = r.i64()
                fv = struct.unpack('<d', struct.pack('<q', raw))[0]
                p.K.append(('float', fv))
            elif t == _LUA_FLOAT:
                raw = r.dbl()
                iv = struct.unpack('<q', struct.pack('<d', raw))[0]
                p.K.append(('int', iv))
            elif t in (_LUA_STR, _LUA_STRL):
                s = r.string()
                p.K.append(('str', s))
            else:
                p.K.append(('unknown', None))

        n = r.i32()
        p.upvals = r.read(n * 2)

        n = r.i32()
        for _ in range(n):
            sub = _parse_lua_custom(r)
            if sub:
                p.subs.append(sub)

        n = r.i32(); r.read(n)
        n = r.i32(); r.read(n * 8)
        n = r.i32()
        for _ in range(n):
            nm = r.string()
            sp = r.i32()
            ep = r.i32()
            if nm:
                p.locs.append((nm, sp, ep))

        n = r.i32()
        for _ in range(n):
            s = r.string()
            if s:
                p.upvs.append(s)

        return p
    except Exception:
        return None

def _load_lua_custom_proto(path: str) -> Optional[_LuaProto]:
    try:
        with open(path, 'rb') as f:
            d = bytearray(f.read())
    except OSError:
        return None

    if len(d) < 18 or d[:4] != b'\x1bLua' or d[4] != 0x53:
        return None

    for offset in (34, 18, 35, 33):
        if offset >= len(d):
            continue
        r = _LuaCustomReader(bytes(d), _LUA_K_KEY)
        r.pos = offset
        p = _parse_lua_custom(r)
        if p is not None:
            return p

    return None

class _LuaStdReader:
    def __init__(self, data):
        self.d = data
        self.sz_int      = self.d[12] if len(self.d) > 12 else 4
        self.sz_size_t   = self.d[13] if len(self.d) > 13 else 4
        self.sz_ins      = self.d[14] if len(self.d) > 14 else 4
        self.sz_lua_int  = self.d[15] if len(self.d) > 15 else 8
        self.sz_lua_num  = self.d[16] if len(self.d) > 16 else 8
        self.fmt_int    = '<i' if self.sz_int == 4 else '<q'
        self.fmt_size_t = '<I' if self.sz_size_t == 4 else '<Q'
        self.pos = 34 if len(self.d) >= 34 else 18

    def read(self, n):
        v = self.d[self.pos:self.pos + n]; self.pos += n; return v
    def byte(self):
        v = self.d[self.pos]; self.pos += 1; return v
    def int(self):
        v = struct.unpack_from(self.fmt_int, self.d, self.pos)[0]
        self.pos += self.sz_int; return v
    def size_t(self):
        v = struct.unpack_from(self.fmt_size_t, self.d, self.pos)[0]
        self.pos += self.sz_size_t; return v
    def lua_int(self):
        v = struct.unpack_from('<q', self.d, self.pos)[0]
        self.pos += self.sz_lua_int; return v
    def lua_num(self):
        v = struct.unpack_from('<d', self.d, self.pos)[0]
        self.pos += self.sz_lua_num; return v
    def string(self):
        if self.pos >= len(self.d): return None
        sz = self.byte()
        if sz == 0: return None
        if sz == 0xFF: sz = self.size_t()
        length = sz - 1
        if self.pos + length > len(self.d): return None
        v = self.d[self.pos:self.pos + length]; self.pos += length
        return v

class _LuaStdProto:
    __slots__ = ('src', 'ld', 'll', 'np', 'va', 'ms', 'ins', 'K', 'upvals', 'subs')
    def __init__(self): self.K = []; self.subs = []

def _parse_lua_std(r) -> Optional[_LuaStdProto]:
    try:
        p = _LuaStdProto()
        p.src = r.string()
        p.ld  = r.int(); p.ll = r.int()
        p.np  = r.byte(); p.va = r.byte(); p.ms = r.byte()
        n = r.int()
        p.ins = []
        for _ in range(n):
            ins = struct.unpack_from('<I', r.read(r.sz_ins))[0]
            p.ins.append(ins)
        n = r.int()
        p.K = []
        for _ in range(n):
            t = r.byte()
            if t == 0:   p.K.append((t, None))
            elif t == 1: p.K.append((t, r.byte()))
            elif t == 3: p.K.append((t, r.lua_num()))
            elif t == 19: p.K.append((t, r.lua_int()))
            elif t in (4, 20): p.K.append((t, r.string()))
            else: p.K.append((t, None))
        n = r.int()
        p.upvals = r.read(n * 2)
        n = r.int()
        for _ in range(n):
            sub = _parse_lua_std(r)
            if sub: p.subs.append(sub)
        n = r.int(); r.read(n * r.sz_int)
        n = r.int()
        for _ in range(n): r.string(); r.int(); r.int()
        n = r.int()
        for _ in range(n): r.string()
        return p
    except Exception:
        return None

def _std_to_custom_lua_proto(std_p: _LuaStdProto) -> _LuaProto:
    p = _LuaProto()
    p.src = std_p.src
    p.ld = std_p.ld
    p.ll = std_p.ll
    p.np = std_p.np
    p.va = std_p.va
    p.ms = std_p.ms

    p.ins = []
    for ins in std_p.ins:
        op = ins & 0x3F
        custom_op = _LUA_STD_TO_CUSTOM.get(op, op)
        p.ins.append((ins & ~0x3F) | custom_op)

    p.K = []
    for t, v in std_p.K:
        if t == 0:    p.K.append(('nil', None))
        elif t == 1:  p.K.append(('bool', bool(v)))
        elif t == 3:  p.K.append(('float', v))
        elif t == 19: p.K.append(('int', v))
        elif t in (4, 20):
            s = v.decode('utf-8') if isinstance(v, bytes) else (v or '')
            p.K.append(('str', s))
        else:
            p.K.append(('unknown', v))

    p.upvals = std_p.upvals
    p.subs = []
    for sub_std in std_p.subs:
        p.subs.append(_std_to_custom_lua_proto(sub_std))
    p.upvs = []
    p.locs = []
    return p

def _load_std_bytecode_to_proto(file_path: str) -> Optional[_LuaProto]:
    try:
        with open(file_path, 'rb') as f:
            data = f.read()
    except Exception:
        return None
    if len(data) < 18 or data[:4] != b'\x1bLua':
        return None
    try:
        r = _LuaStdReader(data)
        std_p = _parse_lua_std(r)
        if std_p is None:
            return None
        return _std_to_custom_lua_proto(std_p)
    except Exception:
        return None

def _get_lua_opcode_name(opcode: int) -> str:
    std_op = _LUA_CUSTOM_TO_STD.get(opcode, opcode)
    if 0 <= std_op < len(_LUA53_OPCODES):
        return _LUA53_OPCODES[std_op]
    return f"OP_{opcode}"

def _decode_lua_instruction(ins: int) -> dict:
    op = ins & 0x3F
    std_op = _LUA_CUSTOM_TO_STD.get(op, op)
    A = (ins >> 6) & 0xFF
    B = (ins >> 23) & 0x1FF
    C = (ins >> 14) & 0x1FF
    Bx = (ins >> 14) & 0x3FFFF
    sBx = Bx - 0x1FFFF
    Ax = (ins >> 6) & 0x3FFFFFF
    return {
        'op': op, 'std_op': std_op,
        'opcode_name': _get_lua_opcode_name(op),
        'A': A, 'B': B, 'C': C,
        'Bx': Bx, 'sBx': sBx, 'Ax': Ax,
        'raw': ins
    }

def _format_lua_const(k) -> str:
    typ, val = k
    if typ == 'nil': return 'nil'
    elif typ == 'bool': return 'true' if val else 'false'
    elif typ == 'float':
        if val is not None and val == int(val): return str(int(val))
        return str(val)
    elif typ == 'int': return str(val)
    elif typ == 'str':
        if val is None: return 'nil'
        s = val.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\t', '\\t')
        return f'"{s}"'
    return str(val)

def _reg_name(proto, reg_idx: int) -> str:
    if reg_idx < len(proto.locs) and proto.locs[reg_idx][0]:
        return proto.locs[reg_idx][0]
    return f"R{reg_idx}"

def _pseudo_decompile_lua(proto, depth: int = 0, func_name: str = "main") -> str:
    indent = "  " * depth
    lines = []

    params = []
    for i in range(proto.np):
        if i < len(proto.locs) and proto.locs[i][0]:
            params.append(proto.locs[i][0])
        else:
            params.append(f"arg{i}")
    if proto.va: params.append("...")
    param_str = ", ".join(params)

    if depth == 0:
        lines.append("--[[ Decompiled by FeaturesticLeaks (Python Lua Engine) ]]")
        lines.append("--[[ Official Telegram: https://t.me/FeaturesticLeaks ]]")
        lines.append("")

    lines.append(f"{indent}local function {func_name}({param_str})")

    if proto.upvs:
        for uv in proto.upvs:
            lines.append(f"{indent}  -- upvalue: {uv}")

    pc = 0
    while pc < len(proto.ins):
        ins = proto.ins[pc]
        dec = _decode_lua_instruction(ins)
        op_name = dec['opcode_name']
        A, B, C = dec['A'], dec['B'], dec['C']
        Bx, sBx = dec['Bx'], dec['sBx']
        line = ""

        if op_name == "LOADK":
            if Bx < len(proto.K):
                const = _format_lua_const(proto.K[Bx])
                rn = _reg_name(proto, A)
                line = f"local {rn} = {const}"

        elif op_name == "LOADNIL":
            rn_start = _reg_name(proto, A)
            if B > A:
                rn_end = _reg_name(proto, B)
                line = f"local {rn_start}, ..., {rn_end} = nil"
            else:
                line = f"local {rn_start} = nil"

        elif op_name == "LOADBOOL":
            val = "true" if B != 0 else "false"
            rn = _reg_name(proto, A)
            line = f"local {rn} = {val}"

        elif op_name == "GETUPVAL":
            rn = _reg_name(proto, A)
            if B < len(proto.upvs):
                line = f"local {rn} = {proto.upvs[B]}"
            else:
                line = f"local {rn} = upval_{B}"

        elif op_name == "GETTABUP":
            rn = _reg_name(proto, A)
            upval = proto.upvs[B] if B < len(proto.upvs) else "_ENV"
            if C & 0x100:
                key = _format_lua_const(proto.K[C & 0xFF]) if (C & 0xFF) < len(proto.K) else f"K{C & 0xFF}"
            else:
                key = _reg_name(proto, C)
            line = f"local {rn} = {upval}[{key}]"

        elif op_name == "SETTABUP":
            upval = proto.upvs[B] if B < len(proto.upvs) else "_ENV"
            if C & 0x100:
                val = _format_lua_const(proto.K[C & 0xFF]) if (C & 0xFF) < len(proto.K) else f"K{C & 0xFF}"
            else:
                val = _reg_name(proto, C)
            if A & 0x100:
                key = _format_lua_const(proto.K[A & 0xFF]) if (A & 0xFF) < len(proto.K) else f"K{A & 0xFF}"
            else:
                key = _reg_name(proto, A)
            line = f"{upval}[{key}] = {val}"

        elif op_name == "GETTABLE":
            rn = _reg_name(proto, A)
            if C & 0x100:
                key = _format_lua_const(proto.K[C & 0xFF]) if (C & 0xFF) < len(proto.K) else f"K{C & 0xFF}"
            else:
                key = _reg_name(proto, C)
            line = f"local {rn} = {_reg_name(proto, B)}[{key}]"

        elif op_name == "SETTABLE":
            if C & 0x100:
                val = _format_lua_const(proto.K[C & 0xFF]) if (C & 0xFF) < len(proto.K) else f"K{C & 0xFF}"
            else:
                val = _reg_name(proto, C)
            if B & 0x100:
                key = _format_lua_const(proto.K[B & 0xFF]) if (B & 0xFF) < len(proto.K) else f"K{B & 0xFF}"
            else:
                key = _reg_name(proto, B)
            line = f"{_reg_name(proto, A)}[{key}] = {val}"

        elif op_name in ("ADD", "SUB", "MUL", "DIV", "MOD", "POW", "IDIV",
                         "BAND", "BOR", "BXOR", "SHL", "SHR"):
            ops = {"ADD": "+", "SUB": "-", "MUL": "*", "DIV": "/",
                   "MOD": "%", "POW": "^", "IDIV": "//",
                   "BAND": "&", "BOR": "|", "BXOR": "~",
                   "SHL": "<<", "SHR": ">>"}
            op_sym = ops.get(op_name, op_name)
            if B & 0x100:
                left = _format_lua_const(proto.K[B & 0xFF]) if (B & 0xFF) < len(proto.K) else f"K{B & 0xFF}"
            else:
                left = _reg_name(proto, B)
            if C & 0x100:
                right = _format_lua_const(proto.K[C & 0xFF]) if (C & 0xFF) < len(proto.K) else f"K{C & 0xFF}"
            else:
                right = _reg_name(proto, C)
            rn = _reg_name(proto, A)
            line = f"local {rn} = {left} {op_sym} {right}"

        elif op_name in ("UNM", "BNOT", "NOT", "LEN"):
            ops = {"UNM": "-", "BNOT": "~", "NOT": "not ", "LEN": "#"}
            op_sym = ops.get(op_name, op_name)
            if B & 0x100:
                val = _format_lua_const(proto.K[B & 0xFF]) if (B & 0xFF) < len(proto.K) else f"K{B & 0xFF}"
            else:
                val = _reg_name(proto, B)
            rn = _reg_name(proto, A)
            line = f"local {rn} = {op_sym}{val}"

        elif op_name == "CONCAT":
            parts = [_reg_name(proto, i) for i in range(B, C + 1)]
            rn = _reg_name(proto, A)
            line = f"local {rn} = {' .. '.join(parts)}"

        elif op_name == "JMP":
            target = pc + 1 + sBx
            line = f"-- goto line_{target}"

        elif op_name in ("EQ", "LT", "LE"):
            ops = {"EQ": "==", "LT": "<", "LE": "<="}
            op_sym = ops.get(op_name, op_name)
            if B & 0x100:
                left = _format_lua_const(proto.K[B & 0xFF]) if (B & 0xFF) < len(proto.K) else f"K{B & 0xFF}"
            else:
                left = _reg_name(proto, B)
            if C & 0x100:
                right = _format_lua_const(proto.K[C & 0xFF]) if (C & 0xFF) < len(proto.K) else f"K{C & 0xFF}"
            else:
                right = _reg_name(proto, C)
            target = pc + 2
            if A == 0:
                line = f"if {left} {op_sym} {right} then goto line_{target} end"
            else:
                line = f"if not ({left} {op_sym} {right}) then goto line_{target} end"

        elif op_name == "TEST":
            target = pc + 2
            rn = _reg_name(proto, A)
            if C == 0:
                line = f"if not {rn} then goto line_{target} end"
            else:
                line = f"if {rn} then goto line_{target} end"

        elif op_name == "CALL":
            if B == 0: args = "..."
            elif B == 1: args = ""
            else: args = ", ".join([_reg_name(proto, i) for i in range(A + 1, A + B)])
            if C == 0: ret = "..."
            elif C == 1: ret = ""
            else: ret = ", ".join([_reg_name(proto, i) for i in range(A, A + C - 1)])
            fn = _reg_name(proto, A)
            if ret:
                line = f"local {ret} = {fn}({args})"
            else:
                line = f"{fn}({args})"

        elif op_name == "TAILCALL":
            if B == 0: args = "..."
            else: args = ", ".join([_reg_name(proto, i) for i in range(A + 1, A + B)])
            line = f"return {_reg_name(proto, A)}({args})"

        elif op_name == "RETURN":
            if B == 0: line = "return ..."
            elif B == 1: line = "return"
            else:
                rets = ", ".join([_reg_name(proto, i) for i in range(A, A + B - 1)])
                line = f"return {rets}"

        elif op_name == "NEWTABLE":
            rn = _reg_name(proto, A)
            line = f"local {rn} = {{}}"

        elif op_name == "CLOSURE":
            rn = _reg_name(proto, A)
            if Bx < len(proto.subs):
                sub_name = f"sub_func_{pc}"
                line = f"local {rn} = {sub_name}"
            else:
                line = f"local {rn} = closure_{Bx}"

        elif op_name == "VARARG":
            if B == 0:
                line = f"local {_reg_name(proto, A)}... = ..."
            else:
                vars = ", ".join([_reg_name(proto, A + i) for i in range(B - 1)])
                line = f"local {vars} = ..."

        elif op_name == "MOVE":
            rn_a = _reg_name(proto, A)
            rn_b = _reg_name(proto, B)
            line = f"local {rn_a} = {rn_b}"

        else:
            line = f"-- {op_name} A={A} B={B} C={C}"

        if line:
            lines.append(f"{indent}  {line}")
        pc += 1

    for i, sub in enumerate(proto.subs):
        sub_name = f"sub_func_{i}"
        lines.append("")
        lines.append(_pseudo_decompile_lua(sub, depth + 1, sub_name))

    lines.append(f"{indent}end")
    return "\n".join(lines)

def fix_lua_syntax_for_lua51(lua_file: Path) -> Path:
    """Preprocesses .lua file to fix standard Lua 5.1 incompatible syntax like 'continue', bitwise '|', and excessive 'local' declarations (>200 limits)."""
    try:
        text = lua_file.read_text(encoding="utf-8", errors="ignore")
        # Replace standalone 'continue' with 'do break end'
        fixed_text = re.sub(r'\bcontinue\b', 'do break end', text)
        
        # Replace bitwise OR pipe operator 'a | b' with 'bit.bor(a, b)' if simple regex matches
        fixed_text = re.sub(r'(\b[\w_.]+\b|\d+)\s*\|\s*(\b[\w_.]+\b|\d+)', r'bit.bor(\1, \2)', fixed_text)
        
        # Strip redundant 'local' declarations in auto-decompiled files to stay within the 200 local variable limit per function
        # e.g. converts 'local r1 = ...' or 'local r1, r2' to 'r1 = ...'
        fixed_text = re.sub(r'^\s*local\s+([a-zA-Z0-9_,\s]+)=', r'\1=', fixed_text, flags=re.MULTILINE)
        fixed_text = re.sub(r'^\s*local\s+([a-zA-Z0-9_]+)\s*$', r'-- \1', fixed_text, flags=re.MULTILINE)

        out_file = lua_file.parent / f"{lua_file.stem}_fixed51.lua"
        out_file.write_text(fixed_text, encoding="utf-8")
        return out_file
    except Exception:
        return lua_file

def analyze_and_display_lua_error(lua_file: Path, stderr_text: str):
    """Analyzes luac stderr to print line snippets and explain Lua 5.1/5.3/LuaJIT incompatibilities."""
    console.print(f"[bold red][X] Compilation failed:[/bold red]\n[white]{stderr_text.strip()}[/white]\n")
    
    file_lines = []
    try:
        file_lines = lua_file.read_text(encoding="utf-8", errors="ignore").splitlines()
    except Exception:
        pass

    found_known_issue = False
    for line in stderr_text.splitlines():
        m = re.search(r':(\d+):\s*(.*)', line)
        if m:
            line_no = int(m.group(1))
            err_msg = m.group(2)
            console.print(f"[bold yellow]🔍 Line {line_no} Analysis:[/bold yellow] [red]{err_msg}[/red]")
            
            if 1 <= line_no <= len(file_lines):
                snippet = file_lines[line_no - 1].strip()
                console.print(f"  [dim white]👉 Code at Line {line_no}:[/dim white] [bold cyan]{snippet}[/bold cyan]")

            if "too many local variables" in err_msg or "limit is 200" in err_msg:
                found_known_issue = True
                console.print("  [bold yellow]💡 Diagnosis:[/bold yellow] Lua compilers allow a MAXIMUM of 200 local variables per function scope.")
                console.print("  [bold green]💡 Solution:[/bold green] Decompiled pseudo-code has too many 'local' declarations. Select Option [1] below to auto-convert local variables into standard scope variables!")
            elif "'continue'" in err_msg or "near 'continue'" in err_msg:
                found_known_issue = True
                console.print("  [bold yellow]💡 Diagnosis:[/bold yellow] Standard Lua 5.1 compiler (`luac5.1`) does not support the 'continue' keyword.")
                console.print("  [bold green]💡 Solution:[/bold green] Standard Lua 5.1 uses 'break' or loop wrappers instead of 'continue'. Option [1] fixes this, or run Option [2] to install LuaJIT.")
            elif "'|'" in err_msg or "near '|'" in err_msg:
                found_known_issue = True
                console.print("  [bold yellow]💡 Diagnosis:[/bold yellow] Bitwise operator '|' or pipe syntax is not supported in standard Lua 5.1.")
                console.print("  [bold green]💡 Solution:[/bold green] Lua 5.1 requires `bit.bor()` functions or a Lua 5.3+ / LuaJIT compiler.")

    if not found_known_issue:
        console.print("[bold yellow]💡 Tip:[/bold yellow] Check for missing closing braces '}', quotes, syntax errors, or select Option [1] to attempt auto-patching.")

def run_lua_compiler(data_path: Path):
    console.print(Panel(Align.center("[bold bright_cyan]🌙 LUA COMPILER (.lua Source -> .luac Bytecode)[/bold bright_cyan]"), border_style="cyan", box=ROUNDED))
    
    lua_dir = data_path / "LUA"
    lua_dir.mkdir(parents=True, exist_ok=True)
    sd_lua = Path("/sdcard/FeaturesticLeaks/LUA")
    try:
        if sd_lua.parent.exists():
            sd_lua.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass

    lua_file, _ = pick_file_from_folder("Compile Lua", lua_dir, extensions=[".lua"])
    if not lua_file:
        custom_input = safe_input('-> Enter custom .lua file path (or press Enter to cancel): ').strip().strip('"\'')
        if not custom_input:
            return
        lua_file = Path(custom_input)
        if not lua_file.exists() or not lua_file.is_file():
            console.print(f'[bold red][X] File not found: {lua_file}[/bold red]')
            return

    all_compilers = ["luac5.1", "luac51", "luac", "luajit", "luac5.2", "luac5.3", "luac5.4"]
    available_compilers = [c for c in all_compilers if shutil.which(c)]

    if not available_compilers:
        console.print(Panel(
            "[bold red][X] No Lua Compiler (luac or luajit) is installed in Termux![/bold red]\n\n"
            "[bold cyan]👉 Click 'Auto-Install' below or run this command in Termux:[/bold cyan]\n"
            "[bold yellow]   pkg install -y lua51 luajit[/bold yellow]",
            border_style="red", box=ROUNDED
        ))
        auto_inst = safe_input('\n-> Auto-install lua51 & luajit now via Termux pkg? (Y/n): ').strip().lower()
        if auto_inst in ['', 'y', 'yes']:
            console.print("[bold cyan][+] Running: pkg update -y && pkg install -y lua51 luajit...[/bold cyan]")
            try:
                subprocess.run("pkg update -y && pkg install -y lua51 luajit", shell=True, check=True)
                console.print("[bold green][OK] Package installation completed![/bold green]")
                available_compilers = [c for c in all_compilers if shutil.which(c)]
            except Exception as e:
                console.print(f"[bold red][X] Auto-installation failed: {e}[/bold red]")
                return
        else:
            return

    if not available_compilers:
        console.print("[bold red][X] No Lua compiler available. Please install lua51 or luajit manually.[/bold red]")
        return

    res_dir = data_path / "RESULT"
    res_dir.mkdir(parents=True, exist_ok=True)
    out_luac = res_dir / f"{lua_file.stem}.luac"

    success = False
    last_stderr = ""
    last_compiler = ""

    for compiler in available_compilers:
        console.print(f"[bold cyan][+] Attempting compile with '{compiler}'...[/bold cyan]")
        if compiler == "luajit":
            cmd = ["luajit", "-b", str(lua_file), str(out_luac)]
        else:
            cmd = [compiler, "-o", str(out_luac), str(lua_file)]

        try:
            proc = subprocess.run(cmd, capture_output=True, text=True)
            if proc.returncode == 0:
                console.print(f"[bold green][OK] Compiled successfully with '{compiler}': {out_luac}[/bold green]")
                success = True
                if sd_lua.exists():
                    try:
                        shutil.copy2(out_luac, sd_lua / out_luac.name)
                        console.print(f"[bold green][+] Saved to SDCard: {sd_lua / out_luac.name}[/bold green]")
                    except Exception:
                        pass
                break
            else:
                last_stderr = proc.stderr
                last_compiler = compiler
        except Exception as e:
            last_stderr = str(e)

    if not success:
        analyze_and_display_lua_error(lua_file, last_stderr)
        
        console.print("\n[bold yellow]🛠️ Options to Fix & Compile:[/bold yellow]")
        console.print("  [bold cyan][1][/bold cyan] Auto-Fix Syntax for Lua 5.1 (Removes 'continue' / fixes '|' bitwise)")
        console.print("  [bold cyan][2][/bold cyan] Auto-Install LuaJIT Compiler (Supports 'continue' & modern syntax)")
        console.print("  [bold cyan][0][/bold cyan] Skip / Back to Menu")
        fix_choice = safe_input('\n-> Select option (0-2): ').strip()

        if fix_choice == '1':
            fixed_lua = fix_lua_syntax_for_lua51(lua_file)
            console.print(f"\n[bold cyan][+] Created patched file: {fixed_lua.name}[/bold cyan]")
            console.print(f"[bold cyan][+] Re-attempting compilation...[/bold cyan]")
            
            for compiler in available_compilers:
                if compiler == "luajit":
                    cmd = ["luajit", "-b", str(fixed_lua), str(out_luac)]
                else:
                    cmd = [compiler, "-o", str(out_luac), str(fixed_lua)]
                
                proc = subprocess.run(cmd, capture_output=True, text=True)
                if proc.returncode == 0:
                    console.print(f"[bold green][OK] Fixed file compiled successfully with '{compiler}': {out_luac}[/bold green]")
                    success = True
                    break
            
            if not success:
                console.print(f"[bold red][X] Re-compilation of fixed file failed as well:[/bold red]\n[white]{proc.stderr}[/white]")
                console.print("[bold yellow]💡 Tip:[/bold yellow] Try Option 2 to auto-install LuaJIT!")

        elif fix_choice == '2':
            console.print("[bold cyan][+] Installing LuaJIT via Termux pkg...[/bold cyan]")
            try:
                subprocess.run("pkg install -y luajit", shell=True, check=True)
                console.print("[bold green][OK] LuaJIT installed successfully![/bold green]")
                if shutil.which("luajit"):
                    cmd = ["luajit", "-b", str(lua_file), str(out_luac)]
                    proc = subprocess.run(cmd, capture_output=True, text=True)
                    if proc.returncode == 0:
                        console.print(f"[bold green][OK] Compiled successfully with 'luajit': {out_luac}[/bold green]")
                    else:
                        console.print(f"[bold red][X] LuaJIT compilation error:[/bold red]\n[white]{proc.stderr}[/white]")
            except Exception as e:
                console.print(f"[bold red][X] LuaJIT installation error: {e}[/bold red]")

def run_lua_decompiler(data_path: Path):
    console.print(Panel(Align.center("[bold bright_cyan]🌙 LUA DECOMPILER (.luac Bytecode -> .lua Source)[/bold bright_cyan]"), border_style="cyan", box=ROUNDED))
    
    lua_dir = data_path / "LUA"
    lua_dir.mkdir(parents=True, exist_ok=True)
    sd_lua = Path("/sdcard/FeaturesticLeaks/LUA")
    try:
        if sd_lua.parent.exists():
            sd_lua.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass

    luac_file, _ = pick_file_from_folder("Decompile Lua", lua_dir, extensions=[".luac", ".lua", ".bytecode", ".bytes"])
    if not luac_file:
        custom_input = safe_input('-> Enter custom .luac file path (or press Enter to cancel): ').strip().strip('"\'')
        if not custom_input:
            return
        luac_file = Path(custom_input)
        if not luac_file.exists() or not luac_file.is_file():
            console.print(f'[bold red][X] File not found: {luac_file}[/bold red]')
            return

    res_dir = data_path / "RESULT"
    res_dir.mkdir(parents=True, exist_ok=True)
    out_lua = res_dir / f"{luac_file.stem}_decompiled.lua"

    luadec_bin = shutil.which("luadec")
    java_bin = shutil.which("java")

    unluac_jar = None
    possible_jars = [
        data_path / "unluac.jar",
        Path.home() / "unluac.jar",
        Path("/data/data/com.termux/files/usr/share/java/unluac.jar")
    ]
    for j in possible_jars:
        if j.exists():
            unluac_jar = j
            break

    decompiled_text = None
    decompile_engine = None

    # Method 1: luadec
    if luadec_bin:
        console.print(f"[bold cyan][+] Attempting decompile using luadec...[/bold cyan]")
        try:
            proc = subprocess.run([luadec_bin, str(luac_file)], capture_output=True, text=True, timeout=15)
            if proc.returncode == 0 and proc.stdout.strip() and "function 0 0" not in proc.stdout:
                decompiled_text = proc.stdout
                decompile_engine = "luadec"
        except Exception as e:
            console.print(f"[dim yellow][!] luadec failed: {e}[/dim yellow]")

    # Method 2: unluac.jar via java
    if not decompiled_text and java_bin and unluac_jar:
        console.print(f"[bold cyan][+] Attempting decompile using unluac ({unluac_jar.name})...[/bold cyan]")
        try:
            proc = subprocess.run([java_bin, "-jar", str(unluac_jar), str(luac_file)], capture_output=True, text=True, timeout=20)
            if proc.returncode == 0 and proc.stdout.strip():
                decompiled_text = proc.stdout
                decompile_engine = "unluac"
        except Exception as e:
            console.print(f"[dim yellow][!] unluac failed: {e}[/dim yellow]")

    # Method 3: Check if file is already plain-text Lua
    if not decompiled_text:
        try:
            raw_txt = luac_file.read_text(encoding="utf-8", errors="replace")
            keywords = ["function", "local ", "if ", "then", "return", "end", "for ", "while "]
            if any(kw in raw_txt[:2000] for kw in keywords):
                decompiled_text = raw_txt
                decompile_engine = "Plain Source Text"
        except Exception:
            pass

    # Method 4: Built-in Python Lua Pseudo-Decompiler (Custom & Standard Bytecode)
    if not decompiled_text:
        console.print(f"[bold cyan][+] Attempting decompile using Python Lua Engine...[/bold cyan]")
        try:
            # First try custom opcode format
            proto = _load_lua_custom_proto(str(luac_file))
            if proto:
                decompiled_text = _pseudo_decompile_lua(proto)
                decompile_engine = "Python Engine (Custom Bytecode)"
            else:
                # Next try standard Lua 5.3/5.1 bytecode
                proto_std = _load_std_bytecode_to_proto(str(luac_file))
                if proto_std:
                    decompiled_text = _pseudo_decompile_lua(proto_std)
                    decompile_engine = "Python Engine (Standard Bytecode)"
        except Exception as e:
            console.print(f"[dim yellow][!] Python Lua Decompiler engine exception: {e}[/dim yellow]")

    if decompiled_text:
        out_lua.write_text(decompiled_text, encoding="utf-8")
        console.print(f"[bold green][OK] Decompiled successfully ({decompile_engine}):[/bold green]")
        console.print(f"[bold green][+] Output file: {out_lua}[/bold green]")
        if sd_lua.exists():
            try:
                shutil.copy2(out_lua, sd_lua / out_lua.name)
                console.print(f"[bold green][+] Also saved to SDCard: {sd_lua / out_lua.name}[/bold green]")
            except Exception:
                pass
    else:
        console.print(Panel(
            "[bold red][X] Could not decompile file automatically.[/bold red]\n\n"
            "[bold cyan]👉 To enable 100% full decompiler support for older/complex Lua 5.1/5.3 bytecode:[/bold cyan]\n"
            "[bold yellow]   1. pkg install openjdk-17[/bold yellow]\n"
            "[bold yellow]   2. curl -L -o unluac.jar https://github.com/tech23-bot/unluac/releases/download/v1.0/unluac.jar[/bold yellow]\n\n"
            "[bold cyan]👉 Or install luadec:[/bold cyan]\n"
            "[bold yellow]   pkg install luadec[/bold yellow]",
            border_style="red", box=ROUNDED
        ))

def extract_pak_from_lua(lua_file_path: Path, output_pak_path: Path, output_clean_lua_path: Path) -> dict:
    """
    Reads a .lua script, uses pattern matching/regex to extract high-density Base64/Hex strings
    representing embedded .pak binary data, writes the decoded .pak file, and saves a clean .lua script.
    """
    if not lua_file_path.exists():
        return {"success": False, "message": f"File not found: {lua_file_path}"}

    try:
        content = lua_file_path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return {"success": False, "message": f"Failed to read Lua file: {e}"}

    b64_matches = re.findall(r'["\']([A-Za-z0-9+/=]{100,})["\']', content)
    hex_matches = re.findall(r'["\']([0-9a-fA-F]{100,})["\']', content)
    hex_escaped_matches = re.findall(r'((?:\\x[0-9a-fA-F]{2}){50,})', content)

    extracted_bytes = None
    matched_string = None
    encoding_used = None

    if b64_matches:
        for candidate in sorted(b64_matches, key=len, reverse=True):
            try:
                decoded = base64.b64decode(candidate)
                if len(decoded) > 100:
                    extracted_bytes = decoded
                    matched_string = candidate
                    encoding_used = "Base64"
                    break
            except Exception:
                continue

    if not extracted_bytes and hex_matches:
        for candidate in sorted(hex_matches, key=len, reverse=True):
            try:
                decoded = bytes.fromhex(candidate)
                if len(decoded) > 100:
                    extracted_bytes = decoded
                    matched_string = candidate
                    encoding_used = "Hex"
                    break
            except Exception:
                continue

    if not extracted_bytes and hex_escaped_matches:
        for candidate in sorted(hex_escaped_matches, key=len, reverse=True):
            try:
                raw_hex = candidate.replace("\\x", "")
                decoded = bytes.fromhex(raw_hex)
                if len(decoded) > 100:
                    extracted_bytes = decoded
                    matched_string = candidate
                    encoding_used = "Escaped Hex"
                    break
            except Exception:
                continue

    if not extracted_bytes:
        return {"success": False, "message": "No embedded PAK payload (Base64 or Hex >= 100 chars) found in Lua script."}

    output_pak_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_pak_path, "wb") as f:
        f.write(extracted_bytes)

    clean_content = content.replace(matched_string, "-- [EMBEDDED_PAK_PAYLOAD_REMOVED]")
    output_clean_lua_path.parent.mkdir(parents=True, exist_ok=True)
    output_clean_lua_path.write_text(clean_content, encoding="utf-8")

    return {
        "success": True,
        "encoding": encoding_used,
        "pak_size": len(extracted_bytes),
        "pak_path": output_pak_path,
        "clean_lua_path": output_clean_lua_path,
        "message": "Extraction Successful"
    }

def embed_pak_into_lua(pak_file_path: Path, output_lua_path: Path, target_filename_in_gg: str = "game_mod.pak") -> dict:
    """
    Reads a binary .pak file, encodes it as Base64, and builds a standalone GameGuardian/Android LUA script
    that automatically unpacks/writes the .pak file to disk at runtime using io.open/file:write.
    """
    if not pak_file_path.exists():
        return {"success": False, "message": f"PAK file not found: {pak_file_path}"}

    try:
        with open(pak_file_path, "rb") as f:
            pak_bytes = f.read()
    except Exception as e:
        return {"success": False, "message": f"Failed to read PAK file: {e}"}

    pak_size = len(pak_bytes)
    if pak_size == 0:
        return {"success": False, "message": "PAK file is empty (0 bytes)."}

    b64_payload = base64.b64encode(pak_bytes).decode("ascii")

    lua_template = f"""-- =======================================================
-- FEATURESTIC LEAKS - EMBEDDED PAK INSTALLER LUA SCRIPT
-- Generated for GameGuardian / Android Runtime
-- Target File: {target_filename_in_gg}
-- Payload Size: {pak_size} bytes
-- =======================================================

local target_path = gg.EXT_STORAGE .. "/FeaturesticLeaks/RESULT/{target_filename_in_gg}"
if not gg.EXT_STORAGE then
    target_path = "/sdcard/FeaturesticLeaks/RESULT/{target_filename_in_gg}"
end

gg.toast("⚡ Extracting embedded PAK payload ({pak_size} bytes)...")

local b64_payload = "{b64_payload}"

local b = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'
local function base64_decode(data)
    data = string.gsub(data, '[^'..b..'=]', '')
    return (data:gsub('.', function(x)
        if (x == '=') then return '' end
        local r,f='',(b:find(x)-1)
        for i=6,1,-1 do r=r..(f%2^i - f%2^(i-1) >= 2^(i-1) and '1' or '0') end
        return r
    end):gsub('%d%d%d%d%d%d%d%d', function(x)
        local c=0
        for i=1,8 do c=c+(x:sub(i,i)=='1' and 2^(8-i) or 0) end
        return string.char(c)
    end))
end

local decoded_bytes = base64_decode(b64_payload)

local file = io.open(target_path, "wb")
if file then
    file:write(decoded_bytes)
    file:close()
    gg.alert("✅ PAK Payload extracted successfully!\\nSaved to: " .. target_path)
    gg.toast("✅ PAK Unpacked Successfully!")
else
    gg.alert("❌ Error: Failed to write PAK file to storage.\\nPlease check SDCard storage permissions.")
end
"""

    output_lua_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        output_lua_path.write_text(lua_template, encoding="utf-8")
    except Exception as e:
        return {"success": False, "message": f"Failed to write LUA script: {e}"}

    return {
        "success": True,
        "pak_size": pak_size,
        "lua_path": output_lua_path,
        "message": "Embedding Successful"
    }

def run_lua_pak_extractor(data_path: Path):
    console.print(Panel(Align.center("[bold bright_cyan]📦 LUA-to-PAK EXTRACTOR (Extract Embedded PAK from .lua Script)[/bold bright_cyan]"), border_style="cyan", box=ROUNDED))
    lua_dir = data_path / "LUA"
    lua_dir.mkdir(parents=True, exist_ok=True)

    lua_file, _ = pick_file_from_folder("Select Lua Script", lua_dir, extensions=[".lua", ".txt"])
    if not lua_file:
        custom_input = safe_input('-> Enter custom .lua script path (or press Enter to cancel): ').strip().strip('"\'')
        if not custom_input:
            return
        lua_file = Path(custom_input)
        if not lua_file.exists():
            console.print(f'[bold red][X] File not found: {lua_file}[/bold red]')
            return

    res_dir = data_path / "RESULT"
    res_dir.mkdir(parents=True, exist_ok=True)
    out_pak = res_dir / f"extracted_{lua_file.stem}.pak"
    out_clean_lua = res_dir / f"clean_{lua_file.name}"

    console.print(f"\n[bold cyan][+] Scanning {lua_file.name} for embedded Base64/Hex PAK data...[/bold cyan]")
    res = extract_pak_from_lua(lua_file, out_pak, out_clean_lua)

    if res["success"]:
        console.print(Panel(
            f"[bold green]✅ {res['message']}![/bold green]\n\n"
            f"[bold white]Encoding Found:[/bold white] [bold cyan]{res['encoding']}[/bold cyan]\n"
            f"[bold white]Extracted PAK Size:[/bold white] [bold yellow]{human_size(res['pak_size'])}[/bold yellow]\n\n"
            f"📄 [bold white]Extracted PAK File:[/bold white] {out_pak}\n"
            f"📄 [bold white]Cleaned Lua Script:[/bold white] {out_clean_lua}",
            title="Extraction Complete",
            border_style="green",
            box=ROUNDED
        ))
        sd_res = Path("/sdcard/FeaturesticLeaks/RESULT")
        if sd_res.exists():
            try:
                shutil.copy2(out_pak, sd_res / out_pak.name)
                shutil.copy2(out_clean_lua, sd_res / out_clean_lua.name)
                console.print(f"📲 [bold green]Saved to SDCard:[/bold green] /sdcard/FeaturesticLeaks/RESULT/")
            except Exception:
                pass
    else:
        console.print(f"[bold red][X] {res['message']}[/bold red]")

def run_pak_lua_embedder(data_path: Path):
    console.print(Panel(Align.center("[bold bright_cyan]📦 PAK-to-LUA EMBEDDER (Convert .pak to Base64 & Embed in GG Script)[/bold bright_cyan]"), border_style="cyan", box=ROUNDED))
    pak_dir = data_path / "PAK"
    pak_dir.mkdir(parents=True, exist_ok=True)

    pak_file, _ = pick_file_from_folder("Select PAK File to Embed", pak_dir, extensions=[".pak", ".obb"])
    if not pak_file:
        custom_input = safe_input('-> Enter custom .pak file path (or press Enter to cancel): ').strip().strip('"\'')
        if not custom_input:
            return
        pak_file = Path(custom_input)
        if not pak_file.exists():
            console.print(f'[bold red][X] File not found: {pak_file}[/bold red]')
            return

    res_dir = data_path / "RESULT"
    res_dir.mkdir(parents=True, exist_ok=True)
    out_lua = res_dir / f"installer_{pak_file.stem}.lua"

    console.print(f"\n[bold cyan][+] Encoding {pak_file.name} ({human_size(pak_file.stat().st_size)}) into GameGuardian Lua script...[/bold cyan]")
    res = embed_pak_into_lua(pak_file, out_lua, target_filename_in_gg=pak_file.name)

    if res["success"]:
        console.print(Panel(
            f"[bold green]✅ {res['message']}![/bold green]\n\n"
            f"[bold white]PAK Payload Size:[/bold white] [bold yellow]{human_size(res['pak_size'])}[/bold yellow]\n"
            f"📄 [bold white]Generated GG Installer Script:[/bold white] {out_lua}",
            title="Embedding Complete",
            border_style="green",
            box=ROUNDED
        ))
        sd_res = Path("/sdcard/FeaturesticLeaks/RESULT")
        if sd_res.exists():
            try:
                shutil.copy2(out_lua, sd_res / out_lua.name)
                console.print(f"📲 [bold green]Saved to SDCard:[/bold green] /sdcard/FeaturesticLeaks/RESULT/{out_lua.name}")
            except Exception:
                pass
    else:
        console.print(f"[bold red][X] {res['message']}[/bold red]")

def show_workflow_guide():
    console.print(Panel(Align.center("[bold bright_cyan]📖 FEATURESTIC LEAKS - EASY STEP-BY-STEP WORKFLOW GUIDE[/bold bright_cyan]"), border_style="cyan", box=ROUNDED))
    
    guide_text = """
[bold yellow]1️⃣ STEP 1: ORIGINAL PAK FILE DAALO[/bold yellow]
• Apni game .pak ya .obb file ko is folder me rakho:
  👉 [bold cyan]/sdcard/FeaturesticLeaks/PAK/[/bold cyan]
• Tool kholo aur [bold green]Option 1 (Unpack)[/bold green] run karo.
• Files extract ho kar [bold cyan]/sdcard/FeaturesticLeaks/UNPACK/[/bold cyan] me chali jayengi.

[bold yellow]2️⃣ STEP 2: FILES EDIT KARO & REPLACEMENT RAKHO[/bold yellow]
• [bold white]Option A (Existing file replace karni hai):[/bold white]
  Edited files ko [bold cyan]/sdcard/FeaturesticLeaks/REPLACE/[/bold cyan] folder me daalo.
  Phir main menu se [bold green]Option 3 (Replace Files)[/bold green] run karo.
  
• [bold white]Option B (Custom internal path par new file inject karni hai):[/bold white]
  New files ko [bold cyan]/sdcard/FeaturesticLeaks/INJECT/[/bold cyan] folder me daalo.
  Phir main menu se [bold green]Option 4 (Inject Path)[/bold green] run karo aur internal path enter karo.

[bold yellow]3️⃣ STEP 3: MODDED PAK OUTPUT LE LO[/bold yellow]
• Aapki modified output .pak file is folder me milegi:
  👉 [bold green]/sdcard/FeaturesticLeaks/RESULT/[/bold green]
• Is file ko Game/OBB folder me copy kar do aur game start karo!
    """
    console.print(Panel(guide_text, border_style="dim white", box=ROUNDED))

def install_termux_shortcut_and_sdcard(data_path: Path):
    console.print("\n[bold cyan][+] Setting up Termux Shortcuts ('leak', 'paktool') & SDCard Workspace...[/bold cyan]")
    
    sdcard_path = Path("/sdcard/FeaturesticLeaks")
    try:
        sdcard_path.mkdir(parents=True, exist_ok=True)
        (sdcard_path / "PAK").mkdir(parents=True, exist_ok=True)
        (sdcard_path / "REPLACE").mkdir(parents=True, exist_ok=True)
        (sdcard_path / "INJECT").mkdir(parents=True, exist_ok=True)
        (sdcard_path / "RESULT").mkdir(parents=True, exist_ok=True)
        (sdcard_path / "UNPACK").mkdir(parents=True, exist_ok=True)
        (sdcard_path / "LUA").mkdir(parents=True, exist_ok=True)
        console.print(f"[bold green][OK] SDCard Workspace Created: /sdcard/FeaturesticLeaks/[/bold green]")
    except Exception:
        console.print(f"[yellow][!] Notice: SDCard folder permission check skipped.[/yellow]")
    
    script_file = Path(__file__).resolve()
    script_dir = script_file.parent
    
    # Try creating executables in Termux bin directories
    bin_dirs = [
        Path(os.environ.get("PREFIX", "/data/data/com.termux/files/usr")) / "bin",
        Path("/data/data/com.termux/files/usr/bin"),
        Path.home() / ".local" / "bin"
    ]
    
    shortcuts_created = []
    for bin_dir in bin_dirs:
        if bin_dir.exists() and os.access(bin_dir, os.W_OK):
            for cmd_name in ["leak", "paktool"]:
                cmd_path = bin_dir / cmd_name
                try:
                    content = f"#!/data/data/com.termux/files/usr/bin/sh\ncd \"{script_dir}\" && python3 \"{script_file}\" \"$@\"\n"
                    cmd_path.write_text(content, encoding="utf-8")
                    cmd_path.chmod(0o755)
                    shortcuts_created.append(cmd_name)
                except Exception:
                    pass
            if shortcuts_created:
                break
    
    # Backup/Always ensure bashrc / zshrc aliases exist
    shell_files = [Path.home() / ".bashrc", Path.home() / ".zshrc"]
    aliases_to_add = [
        f"alias leak='cd \"{script_dir}\" && python3 \"{script_file}\"'",
        f"alias paktool='cd \"{script_dir}\" && python3 \"{script_file}\"'"
    ]
    
    for sh_file in shell_files:
        try:
            curr_content = sh_file.read_text(encoding="utf-8") if sh_file.exists() else ""
            lines_to_append = []
            for alias_line in aliases_to_add:
                cmd_alias = alias_line.split("=")[0]
                if cmd_alias not in curr_content:
                    lines_to_append.append(alias_line)
            if lines_to_append:
                with open(sh_file, "a", encoding="utf-8") as f:
                    f.write("\n" + "\n".join(lines_to_append) + "\n")
        except Exception:
            pass

    console.print("[bold green][OK] Created shortcuts: 'leak' & 'paktool'[/bold green]")
    console.print("\n[bold green]🎉 Complete! Next time Termux me kahin bhi 'leak' ya 'paktool' type karke directly open kar sakte hain![/bold green]")

def print_banner():
    os.system('cls' if os.name == 'nt' else 'clear')
    
    ascii_banner = (
        "[bold green]"
        "  ______ _____    _ _____ _   _ ____  _____ _____ _____ ____  _     ______  _  _____\n"
        " |  ____|  __ \\  / |  ___| | | |  _ \\|  ___|_   _|_   _/ ___|| |   |  ____|/ \\|  ___|\n"
        " | |_   | |__) |/ /| |_  | | | | |_) | |_    | |   | | \\___ \\| |   | |__  / _ \\ |_  \n"
        " |  _|  |  _  / /  |  _| | | | |  _ <|  _|   | |   | |  ___) | |___|  __|/ ___ \\  _| \n"
        " |_|    |_| \\_\\/   |_|    \\___/|_| \\_\\_|     |_|   |_| |____/|_____|____/_/   \\_\\_|   \n"
        "[/bold green]"
    )
    
    sub_title = (
        "[bold bright_green]@L359D : -- TOOL DEVELOPER --[/bold bright_green]\n"
        "[bold green]PAK TOOL v2.0 | BGMI | PUBG | KR | TW | JP | VNG ✓[/bold green]"
    )
    
    top_box = Panel(
        Align.center(f"{ascii_banner}\n{sub_title}"),
        title="[bold green] MADE IN INDIA [/bold green]",
        title_align="center",
        border_style="green",
        box=ROUNDED,
        padding=(0, 1)
    )
    console.print(top_box)

    # USER INFO panel
    user_info_text = (
        "[bold green]DEVELOPER  :[bold white] @L359D[/bold white]\n"
        "CHANNEL    :[bold white] t.me/FeaturesticLeaks[/bold white]\n"
        "TOOL       :[bold white] PAK & LUA SUITE v2.0[/bold white]\n"
        "STATUS     :[bold green] 🟢 Running[/bold green][/bold green]"
    )
    user_panel = Panel(
        user_info_text,
        title="[bold green]🟢 USER INFO 🟢[/bold green]",
        title_align="center",
        border_style="green",
        box=ROUNDED,
        padding=(0, 2)
    )
    console.print(user_panel)

def boot_sequence():
    """
    Animated rocket boot sequence (approx 2-3 seconds):
    Left to right moving rocket with trail and dynamic status text.
    Mobile/Termux safe rendering using standard unicode characters.
    """
    os.system('cls' if os.name == 'nt' else 'clear')
    
    total_frames = 22
    statuses = [
        (0, "Initializing core engine..."),
        (5, "Loading encryption & PAK modules..."),
        (10, "Verifying workspace folders..."),
        (16, "Ready for launch..."),
        (22, "🚀 LAUNCHED — Welcome to FeaturesticLeaks")
    ]
    
    current_status = statuses[0][1]
    track_len = 26
    
    try:
        with Live(refresh_per_second=12, console=console, transient=True) as live:
            for frame in range(total_frames + 1):
                for threshold, msg in statuses:
                    if frame >= threshold:
                        current_status = msg
                
                pos = min(int((frame / total_frames) * track_len), track_len)
                trail = "═" * pos
                spaces = " " * (track_len - pos)
                
                if frame < total_frames:
                    rocket_line = f"[dim cyan]{trail}[/dim cyan][bold bright_yellow]🚀[/bold bright_yellow][dim white]❯[/dim white]{spaces}"
                else:
                    rocket_line = f"[dim cyan]{'═' * track_len}[/dim cyan][bold bright_yellow] 🚀 READY[/bold bright_yellow]"
                
                anim_content = (
                    f"  [bold bright_cyan]⚡ FEATURESTIC LEAKS PAK TOOL ⚡[/bold bright_cyan]\n\n"
                    f"  {rocket_line}\n\n"
                    f"  [bold cyan][⚙][/bold cyan] [white]{current_status}[/white]"
                )
                
                panel = Panel(
                    anim_content,
                    border_style="cyan",
                    box=ROUNDED,
                    padding=(1, 2)
                )
                
                live.update(panel)
                time.sleep(0.09)
    except KeyboardInterrupt:
        pass
    except Exception:
        pass
    
    time.sleep(0.2)

def handle_exception(e: Exception, action_name: str = "Operation", data_path: Optional[Path] = None):
    """
    Centralized error handler:
    - Extracts last frame from traceback (file, line, function).
    - Formats a clean red-bordered Panel on screen with error summary, location, reason & hint.
    - Saves full detailed traceback to logs/error_<timestamp>.log file.
    """
    err_type = type(e).__name__
    raw_msg = str(e).strip() if (str(e) and str(e).strip()) else ""
    
    # Fallback message for empty errors
    if not raw_msg:
        if err_type == "AssertionError":
            err_msg = "Invalid PAK header/structure or verification check failed"
        elif err_type == "ValueError":
            err_msg = "Invalid value or unsupported PAK version"
        elif err_type == "KeyError":
            err_msg = "Target file or path key not found in PAK index"
        else:
            err_msg = f"{err_type} occurred without additional details"
    else:
        err_msg = raw_msg

    # Extract traceback information (last frame)
    tb_lines = traceback.extract_tb(e.__traceback__)
    file_info = "FeaturesticLeaks.py"
    line_no = "?"
    func_name = action_name
    
    if tb_lines:
        last_frame = tb_lines[-1]
        file_info = Path(last_frame.filename).name
        line_no = str(last_frame.lineno)
        func_name = last_frame.name

    # Determine user-friendly reason/hint based on error type and message
    reason_hint = err_msg
    if isinstance(e, PermissionError):
        reason_hint += "\n[yellow]Hint: Folder access denied. File ko Download/ me copy karke try karo, ya Shizuku setup karo.[/yellow]"
    elif isinstance(e, FileNotFoundError):
        reason_hint += "\n[yellow]Hint: File/folder nahi mila. Path check karo.[/yellow]"
    elif isinstance(e, MemoryError) or "out of memory" in err_msg.lower():
        reason_hint += "\n[yellow]Hint: Termux/RAM limit exceed ho gayi. Optimization active hai, background apps close karke retry karein.[/yellow]"
    elif isinstance(e, OSError) and ("no space" in err_msg.lower() or e.errno == 28):
        reason_hint += "\n[yellow]Hint: Storage full hai. Storage me space free karke retry karein.[/yellow]"
    elif any(term in err_type.lower() or term in err_msg.lower() for term in ["zlib", "zstd", "decompress", "compress", "badzip"]):
        reason_hint += "\n[yellow]Hint: File corrupt hai ya unsupported PAK format hai.[/yellow]"

    # Save full traceback to log file
    log_filename = "N/A"
    try:
        base = data_path if data_path else Path(__file__).parent
        logs_dir = base / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = logs_dir / f"error_{timestamp}.log"
        with open(log_file, "w", encoding="utf-8") as f:
            f.write(f"Action: {action_name}\n")
            f.write(f"Time: {datetime.now().isoformat()}\n")
            f.write(f"Error Type: {err_type}\n")
            f.write(f"Error Message: {err_msg}\n")
            f.write(f"Location: {file_info}:{line_no} in {func_name}()\n\n")
            f.write("Full Traceback:\n")
            f.write(traceback.format_exc())
            
        log_filename = f"logs/{log_file.name}"
    except Exception:
        pass

    # Build clean ERROR DETAILS panel for terminal display
    panel_content = (
        f"[bold red]{err_type}[/bold red] in [bold yellow]{func_name}()[/bold yellow]\n"
        f"[dim white]File:[/dim white] [cyan]{file_info}[/cyan], line [yellow]{line_no}[/yellow]\n"
        f"[dim white]Reason:[/dim white] {escape(reason_hint)}\n"
        f"[dim white]Full log:[/dim white] [dim cyan]{log_filename}[/dim cyan]"
    )

    error_panel = Panel(
        panel_content,
        title="[bold red] ERROR DETAILS [/bold red]",
        title_align="left",
        border_style="bold red",
        box=ROUNDED,
        padding=(0, 1)
    )
    
    console.print()
    console.print(error_panel)

def check_and_auto_update():
    """
    Silent background auto-updater:
    - Checks GitHub API for latest commit hash of itzgeniusboy/FeaturesticLeaks-Toolkit-
    - Auto-pulls via git or downloads raw updated FeaturesticLeaks.py
    - Restarts tool if updated
    - Silently skips on network failures or offline mode
    """
    try:
        if getattr(sys, 'frozen', False):
            script_path = Path(sys.executable)
            script_dir = script_path.parent
        else:
            script_path = Path(__file__).resolve()
            script_dir = script_path.parent

        hash_file = script_dir / ".commit_hash"
        local_hash = ""
        if hash_file.exists():
            local_hash = hash_file.read_text(encoding='utf-8').strip()
        else:
            if (script_dir / ".git").exists():
                try:
                    res = subprocess.run(["git", "rev-parse", "HEAD"], cwd=script_dir, capture_output=True, text=True, timeout=2)
                    if res.returncode == 0:
                        local_hash = res.stdout.strip()
                except Exception:
                    pass

        url = "https://api.github.com/repos/itzgeniusboy/FeaturesticLeaks-Toolkit-/commits/main"
        headers = {"User-Agent": "FeaturesticLeaks-Termux/2.0"}
        
        resp = requests.get(url, headers=headers, timeout=3)
        if resp.status_code != 200:
            return
        
        data = resp.json()
        remote_hash = data.get("sha", "").strip()
        
        if not remote_hash:
            return
            
        if not local_hash:
            hash_file.write_text(remote_hash, encoding='utf-8')
            return

        if remote_hash != local_hash:
            console.print("[bold green][OK] New update found! Updating to latest version...[/bold green]")
            updated = False
            
            if (script_dir / ".git").exists():
                try:
                    pull_res = subprocess.run(["git", "pull"], cwd=script_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)
                    if pull_res.returncode == 0:
                        updated = True
                except Exception:
                    pass
            
            if not updated:
                raw_url = "https://raw.githubusercontent.com/itzgeniusboy/FeaturesticLeaks-Toolkit-/main/FeaturesticLeaks.py"
                raw_resp = requests.get(raw_url, headers=headers, timeout=10)
                if raw_resp.status_code == 200 and len(raw_resp.content) > 5000:
                    temp_file = script_path.with_suffix(".tmp")
                    temp_file.write_bytes(raw_resp.content)
                    shutil.move(temp_file, script_path)
                    updated = True

            if updated:
                hash_file.write_text(remote_hash, encoding='utf-8')
                console.print("[bold green][OK] Updated successfully! Restarting tool...[/bold green]")
                time.sleep(1)
                os.execv(sys.executable, [sys.executable] + sys.argv)

    except Exception:
        pass

def styled_prompt(message: str = "", context: str = "~") -> str:
    """
    Renders T3RMUX terminal themed prompt:
    ┌─[FeaturesticLeaks@termux]-[context] (Optional Message)
    └─>>> 
    """
    has_leading_nl = message.startswith('\n') or message.startswith('\r\n')
    clean_msg = message.lstrip('\r\n').strip()
    if clean_msg.startswith("-> "):
        clean_msg = clean_msg[3:].strip()
        
    if has_leading_nl:
        console.print()

    # Header line
    header = (
        "[dim cyan]┌─[/dim cyan]"
        "[dim white][[/dim white]"
        "[bold bright_magenta]FeaturesticLeaks[/bold bright_magenta]"
        "[bold bright_cyan]@termux[/bold bright_cyan]"
        "[dim white]][/dim white]"
        "[dim cyan]─[/dim cyan]"
        "[dim white][[/dim white]"
        f"[bold yellow]{context}[/bold yellow]"
        "[dim white]][/dim white]"
    )
    
    if clean_msg:
        if clean_msg.lower().startswith("press enter"):
            header += f" [dim yellow]({clean_msg})[/dim yellow]"
        else:
            header += f" [dim white]({clean_msg})[/dim white]"

    console.print(header)

    # Prompt arrow line
    prompt_line = "[dim cyan]└─[/dim cyan][bold #FF6B6B]>>>[/bold #FF6B6B] "
    console.print(prompt_line, end="")

    try:
        return input()
    except (EOFError, RuntimeError):
        try:
            if sys.platform != 'win32':
                with open('/dev/tty', 'r') as tty:
                    return tty.readline().rstrip('\n')
            else:
                with open('CON', 'r') as con:
                    return con.readline().rstrip('\r\n')
        except Exception:
            return ""
    except Exception:
        return ""

def safe_input(prompt: str = '', context: str = '~') -> str:
    return styled_prompt(message=prompt, context=context)

def human_size(size: int) -> str:
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f'{size:.2f} {unit}'
        size /= 1024.0
    return f'{size:.2f} PB'

def delete_folder(data_path: Path) -> None:
    folders = []
    for item in data_path.iterdir():
        if item.is_dir() and item.name not in ['PAK', 'UNPACK', 'REPACK', 'RESULT', 'PAK TOOL']:
            folders.append(item)
    if not folders:
        console.print('[yellow][!] No folders found to delete.[/yellow]')
        return
    folder_table = Table(
        title="[bold cyan]AVAILABLE WORKSPACE FOLDERS[/bold cyan]",
        border_style="dim cyan",
        box=ROUNDED,
        show_header=True,
        header_style="bold cyan"
    )
    folder_table.add_column("Index", justify="center", style="bold yellow", width=8)
    folder_table.add_column("Folder Name", justify="left", style="bold white")
    folder_table.add_column("Size", justify="right", style="dim white")
    for i, folder in enumerate(folders, 1):
        folder_size = 0
        for root, dirs, files in os.walk(folder):
            for file in files:
                file_path = os.path.join(root, file)
                if os.path.isfile(file_path):
                    folder_size += os.path.getsize(file_path)
        folder_table.add_row(str(i), folder.name, human_size(folder_size))
    console.print(folder_table)
    try:
        choice_str = safe_input(f"\n-> Select folder number (1-{len(folders)}): ").strip()
        choice = int(choice_str)
        if 1 <= choice <= len(folders):
            selected_folder = folders[choice - 1]
            confirm = safe_input(f"-> Delete {selected_folder.name}? (yes/no): ").strip().lower()
            if confirm == 'yes':
                shutil.rmtree(selected_folder)
                console.print(f'[bold green][OK] Deleted: {selected_folder.name}[/bold green]')
            else:
                console.print('[yellow][!] Cancelled[/yellow]')
        else:
            console.print('[bold red][X] Invalid selection[/bold red]')
    except ValueError:
        console.print('[bold red][X] Invalid input[/bold red]')

def pick_file_from_folder(action_title: str, default_folder: Path, extensions: List[str] = [".pak", ".obb"]) -> Tuple[Optional[Path], List[Path]]:
    """
    Smart Folder Path File Picker:
    - Prompts user for a folder path (or direct file path).
    - Scans folder for .pak / .obb files.
    - If 1 file found: Auto-selects automatically.
    - If multiple files found: Shows numbered clean table for quick selection (e.g. '2').
    - If no files found: Clear error message and re-prompts.
    """
    current_path_str = str(default_folder)
    
    while True:
        console.print(f"\n[bold cyan][?] Select Source Folder for {action_title}[/bold cyan]")
        console.print(f"[dim]Default directory: {current_path_str}[/dim]")
        user_input = safe_input("-> Enter folder path [Press Enter for default, 'C' to cancel]: ").strip().strip('"\'')
        
        if user_input.upper() == 'C':
            return None, []
        
        target_path = Path(user_input) if user_input else Path(current_path_str)
        
        if not target_path.exists():
            console.print(f"[bold red][X] Path does not exist: {target_path}[/bold red]")
            continue
        
        # If user passed a direct file path
        if target_path.is_file():
            if any(target_path.name.lower().endswith(ext) for ext in extensions):
                size_mb = target_path.stat().st_size / (1024 * 1024)
                console.print(f"[bold green][OK] File selected: {target_path.name} ({size_mb:.2f} MB)[/bold green]")
                return target_path, [target_path]
            else:
                console.print(f"[bold red][X] File is not a valid package ({', '.join(extensions)}): {target_path.name}[/bold red]")
                continue
        
        # Scan folder
        found_files = []
        scan_dirs = [target_path]
        
        sd_twin = Path("/sdcard/FeaturesticLeaks") / target_path.name
        if sd_twin.exists() and sd_twin != target_path:
            scan_dirs.append(sd_twin)
            
        for sdir in scan_dirs:
            if sdir.exists() and sdir.is_dir():
                for p in sdir.iterdir():
                    if p.is_file() and any(p.name.lower().endswith(ext) for ext in extensions):
                        if not any(existing.name.lower() == p.name.lower() for existing in found_files):
                            found_files.append(p)
        
        found_files.sort(key=lambda x: x.name.lower())
        
        if not found_files:
            console.print(f"[bold red][X] No valid files ({', '.join(extensions)}) found in folder: {target_path}[/bold red]")
            console.print("[dim]Please enter a folder path containing your .pak or .obb files.[/dim]")
            current_path_str = str(target_path)
            continue
        
        # Auto-select if 1 file found
        if len(found_files) == 1:
            selected = found_files[0]
            size_mb = selected.stat().st_size / (1024 * 1024)
            console.print(f"\n[bold green][OK] Auto-selected single file: {selected.name} ({size_mb:.2f} MB)[/bold green]")
            return selected, found_files
        
        # Multiple files found -> Display clean table
        file_table = Table(
            title=f"[bold cyan]Available Files in {target_path.name}[/bold cyan]",
            show_header=True,
            header_style="bold cyan",
            box=ROUNDED,
            border_style="dim cyan",
            expand=True
        )
        file_table.add_column("Index", style="bold yellow", justify="center", width=8)
        file_table.add_column("Filename", style="bold white", justify="left")
        file_table.add_column("Size", style="dim white", justify="right", width=12)
        
        for i, f in enumerate(found_files, 1):
            size_mb = f.stat().st_size / (1024 * 1024)
            file_table.add_row(str(i), f.name, f"{size_mb:.2f} MB")
        
        file_table.add_row("C", "Change folder or cancel", "-")
        
        console.print()
        console.print(file_table)
        
        choice = safe_input(f"-> Select file number (1-{len(found_files)}) or 'C': ").strip().upper()
        
        if choice == 'C':
            current_path_str = str(target_path)
            continue
        
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(found_files):
                selected = found_files[idx]
                size_mb = selected.stat().st_size / (1024 * 1024)
                console.print(f"[bold green][OK] Selected: {selected.name} ({size_mb:.2f} MB)[/bold green]")
                return selected, found_files
            else:
                console.print(f"[bold red][X] Selection out of range (1-{len(found_files)})[/bold red]")
        except ValueError:
            console.print("[bold red][X] Invalid input. Enter a number or 'C'[/bold red]")

def display_file_selector(title, folder_path, file_pattern="*.pak"):
    """Backward compatibility alias for pick_file_from_folder"""
    exts = [file_pattern.replace('*', '')] if file_pattern else [".pak", ".obb"]
    return pick_file_from_folder(title, Path(folder_path), extensions=exts)

# ==================== INTEGRATED FEATURE MODULES ====================

class UE4StringTool:
    """Extracts and repacks string literals in .uasset / .uexp binary files."""
    def __init__(self):
        self.MIN_STRING_LEN = 2
        self.MAX_STRING_LEN = 8000

    def read_int(self, f):
        data = f.read(4)
        if len(data) < 4:
            return None
        return struct.unpack('<i', data)[0]

    def is_garbage_text(self, text):
        if not text or len(text.strip()) == 0:
            return True
        allowed_control = {'\n', '\r', '\t'}
        for char in text:
            code = ord(char)
            if code == 0:
                return True
            if code < 32 and char not in allowed_control:
                return True
            if char == '\ufffd':
                return True
        return False

    def is_valid_string_start(self, f, current_pos):
        f.seek(current_pos)
        length = self.read_int(f)
        if length is None or length == 0:
            return False
        if not (self.MIN_STRING_LEN <= abs(length) <= self.MAX_STRING_LEN):
            return False

        try:
            if length < 0:
                read_len = -length * 2
                data = f.read(read_len)
                if len(data) != read_len or data[-2:] != b'\x00\x00':
                    return False
                text = data[:-2].decode('utf-16le')
            else:
                read_len = length
                data = f.read(read_len)
                if len(data) != read_len or data[-1:] != b'\x00':
                    return False
                text = data[:-1].decode('utf-8')

            if self.is_garbage_text(text):
                return False
            return True
        except Exception:
            return False

    def extract_strings(self, file_path: Path) -> Tuple[bool, str]:
        if not file_path.exists():
            return False, f"File not found: {file_path.name}"

        json_path = file_path.with_suffix(file_path.suffix + ".json")
        console.print(f"[bold cyan][+] Extracting readable strings from {file_path.name}...[/bold cyan]")

        try:
            with open(file_path, 'rb') as f:
                f.seek(0, 2)
                file_size = f.tell()
                f.seek(0)

                entries = []
                cursor = 0

                while cursor < file_size - 4:
                    if self.is_valid_string_start(f, cursor):
                        f.seek(cursor)
                        length = self.read_int(f)
                        is_utf16 = length < 0
                        abs_len = abs(length)

                        if is_utf16:
                            raw_data = f.read(abs_len * 2)
                            text = raw_data[:-2].decode('utf-16le')
                            total_size = 4 + (abs_len * 2)
                        else:
                            raw_data = f.read(abs_len)
                            text = raw_data[:-1].decode('utf-8')
                            total_size = 4 + abs_len

                        entries.append({
                            "offset": cursor,
                            "original_len_int": length,
                            "text": text
                        })
                        cursor += total_size
                    else:
                        cursor += 1

            if not entries:
                return False, "No valid readable string entries found."

            with open(json_path, 'w', encoding='utf-8') as jf:
                json.dump(entries, jf, indent=4, ensure_ascii=False)

            return True, f"Extracted {len(entries)} string(s) -> {json_path.name}"
        except Exception as e:
            return False, str(e)

    def repack_strings(self, file_path: Path, json_path: Path) -> Tuple[bool, str]:
        if not file_path.exists():
            return False, f"Missing source file: {file_path.name}"
        if not json_path.exists():
            return False, f"Missing JSON file: {json_path.name}"

        output_path = file_path.parent / f"{file_path.stem}_repacked{file_path.suffix}"
        console.print(f"[bold cyan][+] Repacking strings into {file_path.name}...[/bold cyan]")

        try:
            with open(json_path, 'r', encoding='utf-8') as jf:
                entries = json.load(jf)

            entries.sort(key=lambda x: x['offset'])

            with open(file_path, 'rb') as f_orig, open(output_path, 'wb') as f_out:
                cursor_orig = 0
                count_modified = 0

                for i, entry in enumerate(entries):
                    gap_size = entry['offset'] - cursor_orig
                    if gap_size > 0:
                        f_out.write(f_orig.read(gap_size))
                    elif gap_size < 0:
                        f_orig.seek(entry['offset'])

                    new_text = entry['text']
                    old_len_int = entry['original_len_int']
                    is_utf16 = old_len_int < 0

                    if is_utf16:
                        max_byte_size = abs(old_len_int) * 2
                    else:
                        max_byte_size = abs(old_len_int)

                    f_orig.seek(entry['offset'] + 4)
                    old_raw = f_orig.read(max_byte_size)
                    try:
                        if is_utf16:
                            old_text = old_raw[:-2].decode('utf-16le')
                        else:
                            old_text = old_raw[:-1].decode('utf-8')
                    except Exception:
                        old_text = "<decode_err>"

                    if new_text != old_text:
                        console.print(f"  [dim cyan]Old:[/dim cyan] \"{old_text}\" -> [bold yellow]New:[/bold yellow] \"{new_text}\"")
                        count_modified += 1

                    if is_utf16:
                        new_bytes = new_text.encode('utf-16le') + b'\x00\x00'
                    else:
                        new_bytes = new_text.encode('utf-8') + b'\x00'

                    current_byte_size = len(new_bytes)

                    if current_byte_size > max_byte_size:
                        f_out.close()
                        f_orig.close()
                        if output_path.exists():
                            output_path.unlink()
                        return False, f"String '{new_text}' exceeds max byte length ({current_byte_size} > {max_byte_size})"

                    f_out.write(struct.pack('<i', old_len_int))
                    f_out.write(new_bytes)

                    pad_len = max_byte_size - current_byte_size
                    if pad_len > 0:
                        f_out.write(b'\x00' * pad_len)

                    f_orig.seek(entry['offset'])
                    len_check = self.read_int(f_orig)
                    skip_len = 4 + (abs(len_check) * 2 if len_check < 0 else abs(len_check))
                    f_orig.seek(entry['offset'] + skip_len)
                    cursor_orig = f_orig.tell()

                f_out.write(f_orig.read())

            return True, f"Repacked successfully! Modified {count_modified} string(s) -> {output_path.name}"
        except Exception as e:
            return False, str(e)

def run_ue4_string_tool(data_path: Path) -> None:
    console.print(Panel(
        "[bold cyan]⚡ FEATURESTIC LEAKS — UE4 ASSET STRING TOOL ⚡[/bold cyan]\n"
        "[dim white]Extract readable string literals from .uasset / .uexp files to JSON & Repack JSON back to binary.[/dim white]",
        border_style="cyan",
        box=ROUNDED,
        padding=(0, 2)
    ))
    
    console.print("[bold yellow]1.[/bold yellow] [bold white]Unpack Strings to JSON[/bold white]")
    console.print("[bold yellow]2.[/bold yellow] [bold white]Repack Strings from JSON[/bold white]")
    console.print("[bold yellow]0.[/bold yellow] [dim white]Back to Main Menu[/dim white]")
    
    choice = safe_input("\n-> Select Mode (0-2): ").strip()
    tool = UE4StringTool()
    
    if choice == '1':
        target_dir = data_path / "UNPACK"
        if not target_dir.exists():
            target_dir.mkdir(parents=True, exist_ok=True)
        file_p, _ = pick_file_from_folder("Unpack Strings", target_dir, extensions=[".uasset", ".uexp"])
        if file_p:
            ok, msg = tool.extract_strings(file_p)
            if ok:
                console.print(f"[bold green][OK] {msg}[/bold green]")
            else:
                console.print(f"[bold red][X] {msg}[/bold red]")
                
    elif choice == '2':
        target_dir = data_path / "UNPACK"
        if not target_dir.exists():
            target_dir.mkdir(parents=True, exist_ok=True)
        file_p, _ = pick_file_from_folder("Repack Strings Source", target_dir, extensions=[".uasset", ".uexp"])
        if file_p:
            json_p = file_p.with_suffix(file_p.suffix + ".json")
            if not json_p.exists():
                console.print(f"[bold red][X] JSON file not found: {json_p.name}[/bold red]")
                console.print("[yellow][!] Please unpack strings to JSON first (Option 1).[/yellow]")
                return
            ok, msg = tool.repack_strings(file_p, json_p)
            if ok:
                console.print(f"[bold green][OK] {msg}[/bold green]")
            else:
                console.print(f"[bold red][X] {msg}[/bold red]")

def run_white_body_mod(data_path: Path) -> None:
    console.print(Panel(
        "[bold cyan]⚡ FEATURESTIC LEAKS — ONE CLICK WHITE BODY MOD ⚡[/bold cyan]\n"
        "[dim white]Scans extracted assets, copies target meshes & textures to EDIT folder, and nulls them.[/dim white]",
        border_style="cyan",
        box=ROUNDED,
        padding=(0, 2)
    ))
    
    unpack_dir = data_path / "UNPACK"
    if not unpack_dir.exists() or not any(unpack_dir.iterdir()):
        console.print("[bold red][X] Extracted UNPACK folder is empty or not found.[/bold red]")
        console.print("[yellow][!] Please unpack a PAK / OBB package first using Option 1.[/yellow]")
        return
    
    edit_dir = data_path / "PAK TOOL" / "EDIT"
    edit_dir.mkdir(parents=True, exist_ok=True)
    
    target_patterns = [
        "/Game/Arts_Player/Characters/Mesh/Equip/Bag/Mat/M_Bag_",
        "Materials/T_M_Bag",
        "/Game/Arts/UI/TableIcons/ItemIcon/Equipment/Icon_Shoes",
        "/Game/Arts_Player/Characters/Mesh/Equip/Helmet/",
        "/Game/Arts_Player/Weapon/MainWeapon/Rifle/M416/Texture/",
        "/Game/Arts_Player/Characters/Mesh/Female/Body/Mesh/F_Leg_Bare/Tex/",
        "/Game/Arts_Player/Characters/Mesh/MaleBody/Mesh/F_Leg_Bare/Tex/",
        "/Game/Arts_Player/Characters/Mesh/Equip/Helmet_New/Mat/T_",
        "/Game/Arts_Player/Characters/Mesh/Equip/Helmet/Mat/T_",
        "/Game/Arts_Player/Characters/Mesh/Equip/Armor/Mat/M_Armor_",
        "/Game/Arts_Player/Characters/Mesh/Female/Avatar/Cloth/Tex/",
        "/Game/Arts_Player/Characters/Mesh/Male/Avatar/Cloth/Tex/T_Jacket_",
        "/Game/Arts_Player/Characters/Mesh/Female/Body/Tex/",
        "/Game/Arts_Player/Characters/Mesh/Male/Body/Tex/",
        "/Game/Arts_Player/Characters/Mesh/Male/Head/Tex/"
    ]
    
    console.print("[bold cyan][+] Scanning workspace for character & gear assets...[/bold cyan]")
    found_files = []
    
    for root, _, files in os.walk(unpack_dir):
        for file in files:
            if file.endswith(".uasset") or file.endswith(".uexp"):
                file_p = Path(root) / file
                file_str = str(file_p).replace('\\', '/')
                
                matched = False
                for pattern in target_patterns:
                    if pattern.lower() in file_str.lower() or pattern.lower() in file.lower():
                        matched = True
                        break
                
                if matched:
                    found_files.append(file_p)
    
    if not found_files:
        console.print("[bold yellow][!] No matching White Body assets found in UNPACK directory.[/bold yellow]")
        return
    
    console.print(f"[bold green][OK] Found {len(found_files)} White Body asset(s). Copying & nulling...[/bold green]")
    
    copied_count = 0
    for src in found_files:
        try:
            rel_path = src.relative_to(unpack_dir)
            parts = rel_path.parts
            if len(parts) > 1:
                rel_path = Path(*parts[1:])
            
            dest = edit_dir / rel_path
            dest.parent.mkdir(parents=True, exist_ok=True)
            
            shutil.copy2(src, dest)
            
            with open(dest, "wb") as f:
                f.write(b"# FEATURESTIC LEAKS WHITE BODY MOD\n")
            
            copied_count += 1
            console.print(f"  [dim green]Nulled:[/dim green] [cyan]{dest.name}[/cyan]")
        except Exception as e:
            console.print(f"  [bold red]Error on {src.name}: {e}[/bold red]")
    
    summary_panel = Panel(
        f"[bold green][OK] White Body Mod Complete![/bold green]\n"
        f"[white]Total nulled assets:[/white] [bold yellow]{copied_count}[/bold yellow]\n"
        f"[white]Output directory:[/white] [cyan]{edit_dir}[/cyan]\n"
        f"[dim white]You can now use Option 3 (Replace Files) or Option 2 (Repack) to build your PAK.[/dim white]",
        border_style="green",
        box=ROUNDED,
        padding=(0, 2)
    )
    console.print(summary_panel)

def run_file_finder_tool(data_path: Path) -> None:
    console.print(Panel(
        "[bold cyan]🔍 FEATURESTIC LEAKS — ADVANCED FILE FINDER 🔍[/bold cyan]\n"
        "[dim white]Search .uasset, .uexp, .ubulk, .lua files by keyword in workspace.[/dim white]",
        border_style="cyan",
        box=ROUNDED,
        padding=(0, 2)
    ))
    
    unpack_dir = data_path / "UNPACK"
    if not unpack_dir.exists():
        unpack_dir.mkdir(parents=True, exist_ok=True)
    
    console.print(f"[dim]Default search directory: {unpack_dir}[/dim]")
    custom_dir = safe_input("-> Enter search directory [Press Enter for default]: ").strip().strip('"\'')
    
    search_dir = Path(custom_dir) if custom_dir else unpack_dir
    if not search_dir.exists():
        console.print(f"[bold red][X] Directory not found: {search_dir}[/bold red]")
        return
    
    pattern = safe_input("-> Enter search keyword/pattern (e.g. M416, Jacket, Bag, or press Enter for all): ").strip().lower()
    
    extensions = [".uasset", ".uexp", ".ubulk", ".lua", ".json", ".png"]
    
    console.print("\n[bold cyan][+] Scanning directory for files...[/bold cyan]")
    found_files = []
    
    for root, _, files in os.walk(search_dir):
        for file in files:
            if any(file.lower().endswith(ext) for ext in extensions):
                if not pattern or pattern in file.lower() or pattern in root.lower():
                    found_files.append(Path(root) / file)
    
    if not found_files:
        console.print(f"[bold yellow][!] No matching files found in {search_dir}[/bold yellow]")
        return
    
    file_table = Table(
        title=f"[bold cyan]FOUND FILES ({len(found_files)})[/bold cyan]",
        border_style="dim cyan",
        box=ROUNDED,
        show_header=True
    )
    file_table.add_column("#", style="bold yellow", justify="center", width=6)
    file_table.add_column("Filename", style="bold white")
    file_table.add_column("Size", style="dim white", justify="right", width=12)
    
    for i, f in enumerate(found_files[:15], 1):
        file_table.add_row(str(i), f.name, human_size(f.stat().st_size))
    
    if len(found_files) > 15:
        file_table.add_row("...", f"and {len(found_files) - 15} more files", "")
    
    console.print(file_table)
    
    copy_choice = safe_input("\n-> Copy found files to output folder? (y/N): ").strip().lower()
    if copy_choice == 'y':
        out_dir = data_path / "FOUND_FILES"
        out_dir.mkdir(parents=True, exist_ok=True)
        
        flat_choice = safe_input("-> Preserve directory paths? (y/N - 'N' copies flat): ").strip().lower()
        preserve_paths = (flat_choice == 'y')
        
        copied_count = 0
        for f in found_files:
            try:
                if preserve_paths:
                    rel_p = f.relative_to(search_dir)
                    dest = out_dir / rel_p
                    dest.parent.mkdir(parents=True, exist_ok=True)
                else:
                    dest = out_dir / f.name
                    counter = 1
                    original_dest = dest
                    while dest.exists():
                        dest = out_dir / f"{original_dest.stem}_{counter}{original_dest.suffix}"
                        counter += 1
                
                shutil.copy2(f, dest)
                copied_count += 1
            except Exception as e:
                console.print(f"[bold red]Error copying {f.name}: {e}[/bold red]")
        
        console.print(f"[bold green][OK] Successfully copied {copied_count} file(s) to: {out_dir}[/bold green]")

def run_skin_id_modder(data_path: Path) -> None:
    console.print(Panel(
        "[bold cyan]⚡ FEATURESTIC LEAKS — SKIN ID SWAP MODDER ⚡[/bold cyan]\n"
        "[dim white]Swap skin IDs & offset indexes for Lobby, Ingame, Accessories, Hit Effect, Deadbox.[/dim white]",
        border_style="cyan",
        box=ROUNDED,
        padding=(0, 2)
    ))
    
    console.print("[bold yellow]1.[/bold yellow] [bold white]Skin Lobby ID Swap[/bold white]")
    console.print("[bold yellow]2.[/bold yellow] [bold white]Skin Ingame ID Swap[/bold white]")
    console.print("[bold yellow]3.[/bold yellow] [bold white]Gun Accessories ID Swap[/bold white]")
    console.print("[bold yellow]4.[/bold yellow] [bold white]Hit Effect ID Swap[/bold white]")
    console.print("[bold yellow]5.[/bold yellow] [bold white]Deadbox Weapon ID Swap[/bold white]")
    console.print("[bold yellow]0.[/bold yellow] [dim white]Back to Main Menu[/dim white]")
    
    choice = safe_input("\n-> Select Skin Category (0-5): ").strip()
    if choice == '0' or not choice:
        return
    
    orig_id_str = safe_input("-> Enter Original Skin ID (decimal, e.g. 101001): ").strip()
    new_id_str = safe_input("-> Enter Target/Replacement Skin ID (decimal, e.g. 101002): ").strip()
    
    if not orig_id_str.isdigit() or not new_id_str.isdigit():
        console.print("[bold red][X] Invalid Skin IDs. Both must be numeric decimal numbers.[/bold red]")
        return
    
    orig_id = int(orig_id_str)
    new_id = int(new_id_str)
    
    orig_hex = struct.pack('<I', orig_id)
    new_hex = struct.pack('<I', new_id)
    
    search_dir = data_path / "UNPACK"
    if not search_dir.exists() or not any(search_dir.iterdir()):
        search_dir = data_path / "PAK"
    
    if not search_dir.exists() or not any(search_dir.iterdir()):
        console.print(f"[bold red][X] No workspace files found in {search_dir}. Please unpack a PAK file first.[/bold red]")
        return
    
    console.print(f"\n[bold cyan][+] Scanning workspace files for Skin ID {orig_id} ({orig_hex.hex().upper()})...[/bold cyan]")
    
    modified_files = 0
    for root, _, files in os.walk(search_dir):
        for file in files:
            file_p = Path(root) / file
            if file_p.suffix in ['.uasset', '.uexp', '.dat', '.pak']:
                try:
                    with open(file_p, 'rb') as f:
                        data = f.read()
                    
                    if orig_hex in data:
                        new_data = data.replace(orig_hex, new_hex)
                        with open(file_p, 'wb') as f:
                            f.write(new_data)
                        modified_files += 1
                        console.print(f"  [bold green][OK] Swapped ID in:[/bold green] [cyan]{file_p.name}[/cyan]")
                except Exception as e:
                    pass
    
    if modified_files > 0:
        console.print(f"\n[bold green][OK] Skin ID swap complete! Modified {modified_files} file(s).[/bold green]")
    else:
        console.print(f"\n[bold yellow][!] Skin ID {orig_id} not found in workspace binary files.[/bold yellow]")

def run_obb_manager(data_path: Path) -> None:
    console.print(Panel(
        "[bold cyan]📦 FEATURESTIC LEAKS — OBB PACKAGE MANAGER 📦[/bold cyan]\n"
        "[dim white]Unzip OBB archive & Rezip OBB with byte-exact padding matching original size.[/dim white]",
        border_style="cyan",
        box=ROUNDED,
        padding=(0, 2)
    ))
    
    console.print("[bold yellow]1.[/bold yellow] [bold white]Unzip OBB Package[/bold white]")
    console.print("[bold yellow]2.[/bold yellow] [bold white]Rezip OBB Package (with exact size padding)[/bold white]")
    console.print("[bold yellow]0.[/bold yellow] [dim white]Back to Main Menu[/dim white]")
    
    choice = safe_input("\n-> Select Option (0-2): ").strip()
    
    if choice == '1':
        obb_dir = data_path / "PAK"
        obb_dir.mkdir(parents=True, exist_ok=True)
        obb_file, _ = pick_file_from_folder("Unzip OBB", obb_dir, extensions=[".obb", ".zip"])
        if not obb_file:
            return
        
        orig_size = obb_file.stat().st_size
        out_unpack = data_path / "UNPACK" / obb_file.stem
        out_unpack.mkdir(parents=True, exist_ok=True)
        
        size_ini = data_path / f"size_{obb_file.stem}.ini"
        size_ini.write_text(str(orig_size), encoding='utf-8')
        
        console.print(f"[bold cyan][+] Extracting OBB ({human_size(orig_size)})...[/bold cyan]")
        try:
            with zipfile.ZipFile(obb_file, 'r') as zf:
                zf.extractall(out_unpack)
            console.print(f"[bold green][OK] Successfully extracted OBB to: {out_unpack}[/bold green]")
        except Exception as e:
            handle_exception(e, "Unzip OBB", data_path)
            
    elif choice == '2':
        unpack_dir = data_path / "UNPACK"
        if not unpack_dir.exists() or not any(unpack_dir.iterdir()):
            console.print("[bold red][X] No extracted OBB folders found in UNPACK directory.[/bold red]")
            return
        
        folders = [item for item in unpack_dir.iterdir() if item.is_dir()]
        if not folders:
            console.print("[bold red][X] No subfolders found in UNPACK.[/bold red]")
            return
        
        folder_table = Table(
            title="[bold cyan]EXTRACTED OBB FOLDERS[/bold cyan]",
            border_style="dim cyan",
            box=ROUNDED
        )
        folder_table.add_column("Index", style="bold yellow", justify="center", width=8)
        folder_table.add_column("Folder Name", style="bold white")
        for i, f in enumerate(folders, 1):
            folder_table.add_row(str(i), f.name)
        
        console.print(folder_table)
        sel_idx = safe_input(f"-> Select folder number (1-{len(folders)}): ").strip()
        if not sel_idx.isdigit() or not (1 <= int(sel_idx) <= len(folders)):
            console.print("[bold red][X] Invalid selection.[/bold red]")
            return
        
        target_folder = folders[int(sel_idx) - 1]
        
        size_ini = data_path / f"size_{target_folder.name}.ini"
        target_orig_size = 0
        if size_ini.exists():
            try:
                target_orig_size = int(size_ini.read_text(encoding='utf-8').strip())
            except Exception:
                pass
        
        result_dir = data_path / "RESULT"
        result_dir.mkdir(parents=True, exist_ok=True)
        out_obb = result_dir / f"{target_folder.name}.obb"
        
        console.print(f"[bold cyan][+] Rezips OBB package: {out_obb.name}...[/bold cyan]")
        try:
            with zipfile.ZipFile(out_obb, 'w', compression=zipfile.ZIP_STORED) as zf:
                for root, _, files in os.walk(target_folder):
                    for file in files:
                        full_p = Path(root) / file
                        rel_p = full_p.relative_to(target_folder)
                        zf.write(full_p, arcname=str(rel_p).replace('\\', '/'))
            
            curr_size = out_obb.stat().st_size
            if target_orig_size > 0:
                if curr_size < target_orig_size:
                    pad_bytes = target_orig_size - curr_size
                    with open(out_obb, 'ab') as f:
                        f.write(b'\x00' * pad_bytes)
                    console.print(f"[bold green][OK] Added {pad_bytes} padding bytes to match original size ({human_size(target_orig_size)})![/bold green]")
                elif curr_size > target_orig_size:
                    console.print(f"[yellow][!] Repacked OBB size ({human_size(curr_size)}) exceeds original size ({human_size(target_orig_size)}).[/yellow]")
            
            console.print(f"[bold green][OK] OBB successfully created: {out_obb}[/bold green]")
        except Exception as e:
            handle_exception(e, "Rezip OBB", data_path)

def run_pak_compare_dumper(data_path: Path) -> None:
    console.print(Panel(
        "[bold bright_cyan]🔍 PAK COMPARE & DUMP TOOL (PAK DUMPER) 🔍[/bold bright_cyan]\n"
        "[dim white]Compare two .pak/.obb files or dump detailed internal file lists, offsets, sizes, hashes, and encryption modes.[/dim white]",
        border_style="bright_cyan",
        box=ROUNDED,
        padding=(0, 2)
    ))

    console.print("\n[bold yellow]Select PAK Compare / Dump Mode:[/bold yellow]")
    console.print("  [bold cyan][1][/bold cyan] Dump Single PAK/OBB Index & Hashes to Text/JSON")
    console.print("  [bold cyan][2][/bold cyan] Compare Two PAK/OBB Files (Added, Modified, Removed Assets)")
    console.print("  [bold cyan][0][/bold cyan] Cancel / Back")

    sub_choice = safe_input('\n-> Select option (0-2): ').strip()
    
    if sub_choice == '1':
        pak_dir = data_path / "PAK"
        pak_dir.mkdir(parents=True, exist_ok=True)
        pak_file, _ = pick_file_from_folder("PAK Dump", pak_dir)
        if not pak_file:
            return
        try:
            console.print(f"\n[bold cyan][+] Reading PAK index for {pak_file.name}...[/bold cyan]")
            pak = TencentPakFile(pak_file)
            entries = []
            for dir_p, files in pak._index.items():
                for fname, entry in files.items():
                    rel_path = (pak._mount_point / dir_p / fname).as_posix()
                    enc_m = pak._get_method_str(entry.encryption_method, True)
                    comp_m = pak._get_method_str(entry.compression_method, False)
                    entries.append({
                        "file_path": rel_path,
                        "size": entry.size,
                        "uncompressed_size": entry.uncompressed_size,
                        "offset": entry.offset,
                        "encrypted": entry.encrypted,
                        "encryption_method": enc_m,
                        "compression_method": comp_m,
                        "hash": entry.hash.hex() if hasattr(entry.hash, 'hex') else str(entry.hash)
                    })

            dump_dir = data_path / "DUMP_LOGS"
            dump_dir.mkdir(parents=True, exist_ok=True)
            txt_dump = dump_dir / f"Dump_{pak_file.stem}.txt"
            json_dump = dump_dir / f"Dump_{pak_file.stem}.json"

            with open(txt_dump, "w", encoding="utf-8") as f:
                f.write(f"=== FEATURESTIC LEAKS PAK INDEX DUMP ===\n")
                f.write(f"PAK File: {pak_file.name}\n")
                f.write(f"Mount Point: {pak._mount_point}\n")
                f.write(f"Total Files: {len(entries)}\n")
                f.write("="*60 + "\n\n")
                for e in entries:
                    f.write(f"Path: {e['file_path']}\n")
                    f.write(f"  Size: {e['size']} bytes (Uncompressed: {e['uncompressed_size']} bytes)\n")
                    f.write(f"  Offset: {e['offset']} | Compression: {e['compression_method']} | Encryption: {e['encryption_method']}\n")
                    f.write(f"  Hash: {e['hash']}\n\n")

            with open(json_dump, "w", encoding="utf-8") as f:
                json.dump({"pak_file": pak_file.name, "mount_point": str(pak._mount_point), "total_files": len(entries), "files": entries}, f, indent=2)

            console.print(f"\n[bold green][OK] Dump created successfully![/bold green]")
            console.print(f"  📄 [bold white]Text Dump:[/bold white] {txt_dump}")
            console.print(f"  📄 [bold white]JSON Dump:[/bold white] {json_dump}")

            sd_dump = Path("/sdcard/FeaturesticLeaks/DUMP_LOGS")
            if sd_dump.parent.exists():
                sd_dump.mkdir(parents=True, exist_ok=True)
                shutil.copy2(txt_dump, sd_dump / txt_dump.name)
                shutil.copy2(json_dump, sd_dump / json_dump.name)
                console.print(f"  📲 [bold green]Saved to SDCard:[/bold green] /sdcard/FeaturesticLeaks/DUMP_LOGS/")

        except Exception as e:
            handle_exception(e, "PAK Dump", data_path)

    elif sub_choice == '2':
        pak_dir = data_path / "PAK"
        pak_dir.mkdir(parents=True, exist_ok=True)
        console.print("\n[bold cyan][1/2] Select Original / Old PAK file:[/bold cyan]")
        pak_file_1, _ = pick_file_from_folder("Select First PAK", pak_dir)
        if not pak_file_1:
            return

        console.print("\n[bold cyan][2/2] Select New / Modified PAK file:[/bold cyan]")
        pak_file_2, _ = pick_file_from_folder("Select Second PAK", pak_dir)
        if not pak_file_2:
            return

        try:
            console.print(f"\n[bold cyan][+] Reading PAK 1 ({pak_file_1.name})...[/bold cyan]")
            pak1 = TencentPakFile(pak_file_1)
            map1 = {}
            for dir_p, files in pak1._index.items():
                for fname, entry in files.items():
                    rel_p = (pak1._mount_point / dir_p / fname).as_posix()
                    map1[rel_p] = entry

            console.print(f"[bold cyan][+] Reading PAK 2 ({pak_file_2.name})...[/bold cyan]")
            pak2 = TencentPakFile(pak_file_2)
            map2 = {}
            for dir_p, files in pak2._index.items():
                for fname, entry in files.items():
                    rel_p = (pak2._mount_point / dir_p / fname).as_posix()
                    map2[rel_p] = entry

            keys1, keys2 = set(map1.keys()), set(map2.keys())
            added = keys2 - keys1
            removed = keys1 - keys2
            common = keys1 & keys2

            modified = []
            for k in common:
                e1, e2 = map1[k], map2[k]
                if e1.size != e2.size or e1.uncompressed_size != e2.uncompressed_size or getattr(e1, 'hash', None) != getattr(e2, 'hash', None):
                    modified.append((k, e1, e2))

            summary_table = Table(title="[bold yellow]PAK COMPARE RESULT SUMMARY[/bold yellow]", box=ROUNDED, border_style="cyan")
            summary_table.add_column("Category", style="bold white")
            summary_table.add_column("Count", style="bold yellow", justify="right")

            summary_table.add_row("Total Files in PAK 1", str(len(keys1)))
            summary_table.add_row("Total Files in PAK 2", str(len(keys2)))
            summary_table.add_row("🆕 Added Assets", f"[bold green]{len(added)}[/bold green]")
            summary_table.add_row("✏️ Modified / Changed Assets", f"[bold yellow]{len(modified)}[/bold yellow]")
            summary_table.add_row("🗑️ Removed / Missing Assets", f"[bold red]{len(removed)}[/bold red]")
            summary_table.add_row("✅ Unchanged Common Assets", str(len(common) - len(modified)))

            console.print(summary_table)

            dump_dir = data_path / "DUMP_LOGS"
            dump_dir.mkdir(parents=True, exist_ok=True)
            diff_log = dump_dir / f"Compare_{pak_file_1.stem}_vs_{pak_file_2.stem}.txt"

            with open(diff_log, "w", encoding="utf-8") as f:
                f.write(f"=== FEATURESTIC LEAKS PAK COMPARISON LOG ===\n")
                f.write(f"PAK 1 (Original): {pak_file_1.name} ({len(keys1)} files)\n")
                f.write(f"PAK 2 (Modified): {pak_file_2.name} ({len(keys2)} files)\n")
                f.write("="*60 + "\n\n")

                f.write(f"--- ADDED ASSETS ({len(added)}) ---\n")
                for a in sorted(added):
                    f.write(f"+ {a} ({map2[a].size} bytes)\n")

                f.write(f"\n--- MODIFIED ASSETS ({len(modified)}) ---\n")
                for k, e1, e2 in sorted(modified, key=lambda x: x[0]):
                    f.write(f"* {k}\n  PAK1: {e1.size} bytes | PAK2: {e2.size} bytes\n")

                f.write(f"\n--- REMOVED ASSETS ({len(removed)}) ---\n")
                for r in sorted(removed):
                    f.write(f"- {r}\n")

            console.print(f"\n[bold green][OK] Comparison log saved:[/bold green] {diff_log}")

            sd_dump = Path("/sdcard/FeaturesticLeaks/DUMP_LOGS")
            if sd_dump.parent.exists():
                sd_dump.mkdir(parents=True, exist_ok=True)
                shutil.copy2(diff_log, sd_dump / diff_log.name)
                console.print(f"📲 [bold green]Saved to SDCard:[/bold green] /sdcard/FeaturesticLeaks/DUMP_LOGS/{diff_log.name}")

            # Option to extract modified and added assets automatically
            diff_count = len(modified) + len(added)
            if diff_count > 0:
                console.print(f"\n[bold yellow]💡 Found {diff_count} modified/added files in PAK 2.[/bold yellow]")
                extract_choice = safe_input("-> Do you want to extract these modified/added files to RESULT/Modified_Files? (y/n): ").strip().lower()
                if extract_choice == 'y':
                    mod_out_dir = data_path / "RESULT" / "Modified_Files"
                    mod_out_dir.mkdir(parents=True, exist_ok=True)
                    console.print(f"\n[bold cyan][+] Extracting {diff_count} modified/added files from PAK 2...[/bold cyan]")
                    
                    extracted_cnt = 0
                    # Extract added assets
                    for rel_p in sorted(added):
                        entry = map2[rel_p]
                        dest_file = mod_out_dir / rel_p.lstrip('/')
                        dest_file.parent.mkdir(parents=True, exist_ok=True)
                        try:
                            pak2._write_to_disk(dest_file, entry)
                            extracted_cnt += 1
                        except Exception:
                            pass

                    # Extract modified assets
                    for rel_p, e1, e2 in sorted(modified, key=lambda x: x[0]):
                        dest_file = mod_out_dir / rel_p.lstrip('/')
                        dest_file.parent.mkdir(parents=True, exist_ok=True)
                        try:
                            pak2._write_to_disk(dest_file, e2)
                            extracted_cnt += 1
                        except Exception:
                            pass

                    console.print(f"[bold green]✅ Extracted {extracted_cnt}/{diff_count} files to:[/bold green] {mod_out_dir}")
                    
                    sd_mod = Path("/sdcard/FeaturesticLeaks/RESULT/Modified_Files")
                    if sd_mod.parent.parent.exists():
                        try:
                            if sd_mod.exists():
                                shutil.rmtree(sd_mod)
                            shutil.copytree(mod_out_dir, sd_mod)
                            console.print(f"📲 [bold green]Synced to SDCard:[/bold green] /sdcard/FeaturesticLeaks/RESULT/Modified_Files/")
                        except Exception:
                            pass

        except Exception as e:
            handle_exception(e, "PAK Compare", data_path)

def pak_obb_tools_menu(data_path: Path):
    while True:
        print_banner()
        menu_table = Table(
            title="[bold green]📦 PAK / OBB TOOLS 📦[/bold green]",
            show_header=True,
            header_style="bold green",
            box=ROUNDED,
            border_style="green",
            expand=True
        )
        menu_table.add_column("OPT", justify="center", width=8, style="bold green")
        menu_table.add_column("COMMAND", justify="left", width=22, style="bold white")
        menu_table.add_column("DESCRIPTION", justify="left", style="green")

        menu_table.add_row("[1]", "Unpack", "Extract PAK / OBB package contents")
        menu_table.add_row("[2]", "Repack", "Rebuild workspace to PAK / OBB")
        menu_table.add_row("[3]", "Replace Files", "Inject edited files into existing structure")
        menu_table.add_row("[4]", "Inject Path", "Inject files into custom PAK target path")
        menu_table.add_row("[5]", "White Body Mod", "One-click character & gear asset nuller")
        menu_table.add_row("[6]", "Skin ID Swap", "Swap Lobby, Ingame & Weapon skin IDs")
        menu_table.add_row("[7]", "OBB Manager", "Unzip & Rezip OBB with size padding")
        menu_table.add_row("[8]", "PAK Compare & Dumper", "Compare 2 PAKs or dump index/offsets/hashes")
        menu_table.add_row("[0]", "EXIT ✗", "Return to Main Menu")

        console.print(menu_table)
        console.print()
        choice = safe_input('\033[1;32mSELECT OPTION [1-8] [0]: \033[0m').strip()

        if choice == '1':
            pak_dir = data_path / "PAK"
            pak_dir.mkdir(parents=True, exist_ok=True)
            pak_file, _ = pick_file_from_folder("Unpack", pak_dir)
            if not pak_file:
                safe_input('\nPress Enter to continue...')
                continue
            try:
                console.print(f'[bold cyan][+] Unpacking {pak_file.name}...[/bold cyan]')
                pak = TencentPakFile(pak_file)
                unpack_path = data_path / "UNPACK" / pak_file.stem
                repack_path = data_path / "REPACK" / pak_file.stem
                pak.dump(unpack_path)

                sd_unpack = Path("/sdcard/FeaturesticLeaks/UNPACK") / pak_file.stem
                if sd_unpack.parent.exists() and sd_unpack != unpack_path:
                    try:
                        pak.dump(sd_unpack)
                    except Exception:
                        pass

                log_path = unpack_path / f'Debug_{pak_file.stem}.log'
                dump_unpacking_log(pak, log_path)
                for dir_path, _ in pak._index.items():
                    current_repack_path = repack_path / pak._mount_point / dir_path
                    current_repack_path.mkdir(parents=True, exist_ok=True)
                console.print(f'[bold green][OK] Successfully extracted to: {unpack_path}[/bold green]')
                if sd_unpack.parent.exists():
                    console.print(f'[bold green][+] Also extracted to SDCard: {sd_unpack}[/bold green]')
            except Exception as e:
                handle_exception(e, "Unpack", data_path)
            safe_input('\nPress Enter to continue...')

        elif choice == '2':
            pak_dir = data_path / "PAK"
            pak_dir.mkdir(parents=True, exist_ok=True)
            pak_file, _ = pick_file_from_folder("Repack", pak_dir)
            if not pak_file:
                safe_input('\nPress Enter to continue...')
                continue
            repack_dir = data_path / "REPACK" / pak_file.stem
            if not repack_dir.exists():
                console.print(f'[bold red][X] Error: {repack_dir} not found.[/bold red]')
                console.print('[yellow][!] Please unpack first using Option 1.[/yellow]')
                safe_input('\nPress Enter to continue...')
                continue
            try:
                console.print(f'[bold cyan][+] Repacking {pak_file.name}...[/bold cyan]')
                pak = TencentPakFile(pak_file)
                result_dir = data_path / "RESULT"
                output_pak = result_dir / pak_file.name
                mode = detect_repack_mode(pak_file)
                if mode == 'MINI_OBB':
                    repack_mini_obb(pak, repack_dir, output_pak)
                elif mode == 'GAMEPATCH':
                    repack_gamepatch(pak, repack_dir, output_pak)
                else:
                    repack_obbzsdic(pak, repack_dir, output_pak)

                sd_res = Path("/sdcard/FeaturesticLeaks/RESULT")
                if sd_res.exists():
                    try:
                        shutil.copy2(output_pak, sd_res / pak_file.name)
                        console.print(f'[bold green][+] Saved to SDCard: {sd_res / pak_file.name}[/bold green]')
                    except Exception:
                        pass
                console.print('[bold green][OK] Repack completed successfully![/bold green]')
            except Exception as e:
                handle_exception(e, "Repack", data_path)
            safe_input('\nPress Enter to continue...')

        elif choice == '3':
            pak_dir = data_path / "PAK"
            pak_file, _ = pick_file_from_folder("Replace Files", pak_dir)
            if not pak_file:
                safe_input('\nPress Enter to continue...')
                continue

            cand_dirs = [
                data_path / "REPLACE",
                Path("/sdcard/FeaturesticLeaks/REPLACE"),
                data_path / "PAK TOOL" / "EDIT",
                Path("/sdcard/FeaturesticLeaks/PAK TOOL/EDIT")
            ]
            actual_edit_path = None
            for cd in cand_dirs:
                if cd.exists() and any(cd.iterdir()):
                    actual_edit_path = cd
                    break

            if not actual_edit_path:
                console.print('[yellow][!] REPLACE source folder me koi file nahi mili![/yellow]')
                console.print('[cyan]👉 Pehle edited files ko /sdcard/FeaturesticLeaks/REPLACE/ me daalo.[/cyan]')
                custom_edit = safe_input('-> Enter custom source folder path (or press Enter to cancel): ').strip().strip('"\'')
                if not custom_edit:
                    safe_input('\nPress Enter to continue...')
                    continue
                custom_p = Path(custom_edit)
                if not custom_p.exists():
                    console.print(f'[bold red][X] Path does not exist: {custom_p}[/bold red]')
                    safe_input('\nPress Enter to continue...')
                    continue
                actual_edit_path = custom_p

            try:
                console.print(f'[bold cyan][+] Replacing files using source: {actual_edit_path}[/bold cyan]')
                pak = TencentPakFile(pak_file)
                result_dir = data_path / "RESULT"
                result_dir.mkdir(parents=True, exist_ok=True)
                output_pak = result_dir / pak_file.name

                count = repack_pak_file_full(pak, actual_edit_path, output_pak)

                sd_res = Path("/sdcard/FeaturesticLeaks/RESULT")
                if sd_res.exists():
                    try:
                        shutil.copy2(output_pak, sd_res / pak_file.name)
                        console.print(f'[bold green][+] Saved to SDCard: {sd_res / pak_file.name}[/bold green]')
                    except Exception:
                        pass

                if count > 0:
                    console.print(f'[bold green][OK] Repacked {count} file(s) successfully![/bold green]')
                    console.print(f'[bold green][+] Output: {output_pak}[/bold green]')
                    if pak_file.parent != pak_dir and pak_file.parent.exists():
                        copy_back = safe_input('\n-> Copy repacked PAK back to original directory? (y/N): ').strip().lower()
                        if copy_back == 'y':
                            shutil.copy2(output_pak, pak_file)
                            console.print(f'[bold green][OK] Updated original file at {pak_file}[/bold green]')
                else:
                    console.print('[bold red][X] No files repacked.[/bold red]')

            except Exception as e:
                handle_exception(e, "Replace Files", data_path)
            safe_input('\nPress Enter to continue...')

        elif choice == '4':
            pak_dir = data_path / "PAK"
            pak_file, _ = pick_file_from_folder("Inject Path", pak_dir)
            if not pak_file:
                safe_input('\nPress Enter to continue...')
                continue

            cand_dirs = [
                data_path / "INJECT",
                Path("/sdcard/FeaturesticLeaks/INJECT"),
                data_path / "REPLACE",
                Path("/sdcard/FeaturesticLeaks/REPLACE"),
                data_path / "PAK TOOL" / "EDIT"
            ]
            actual_edit_path = None
            for cd in cand_dirs:
                if cd.exists() and any(cd.iterdir()):
                    actual_edit_path = cd
                    break

            if not actual_edit_path:
                console.print('[yellow][!] INJECT source folder me koi file nahi mili![/yellow]')
                console.print('[cyan]👉 Pehle source files ko /sdcard/FeaturesticLeaks/INJECT/ me daalo.[/cyan]')
                custom_edit = safe_input('-> Enter custom source folder path (or press Enter to cancel): ').strip().strip('"\'')
                if not custom_edit:
                    safe_input('\nPress Enter to continue...')
                    continue
                custom_p = Path(custom_edit)
                if not custom_p.exists():
                    console.print(f'[bold red][X] Path does not exist: {custom_p}[/bold red]')
                    safe_input('\nPress Enter to continue...')
                    continue
                actual_edit_path = custom_p

            console.print(f"\n[bold green][OK] Source files selected from:[/bold green] [cyan]{actual_edit_path}[/cyan]\n")
            console.print(Panel(
                "[bold bright_cyan]📂 ENTER TARGET PATH INSIDE PAK CONTAINER[/bold bright_cyan]\n"
                "[dim white]PAK ke andar kis folder path par files inject karni hain woh path yahan write/paste karein.[/dim white]\n\n"
                "[bold yellow]📌 Examples:[/bold yellow]\n"
                "  [bold cyan]Example 1:[/bold cyan] [bold white]Content/Lua/GameLua/Mod/BRMod/Gameplay/Core[/bold white]\n"
                "  [bold cyan]Example 2:[/bold cyan] [bold white]ShadowTrackerExtra/Saved/Paks[/bold white]\n"
                "  [bold cyan]Example 3:[/bold cyan] [bold white]ShadowTrackerExtra/Content/Paks[/bold white]",
                title="[bold yellow]💡 TARGET PATH HELP & EXAMPLES[/bold yellow]",
                border_style="cyan",
                box=ROUNDED,
                padding=(0, 2)
            ))
            target_path = safe_input('\n-> Enter Target Path (or "C" to cancel): ').strip().strip('"\'')
            if not target_path or target_path.upper() == 'C':
                console.print('[bold yellow][!] Path injection cancelled.[/bold yellow]')
                safe_input('\nPress Enter to continue...')
                continue

            try:
                pak = TencentPakFile(pak_file)
                result_dir = data_path / "RESULT"
                result_dir.mkdir(parents=True, exist_ok=True)
                output_pak = result_dir / pak_file.name

                count = repack_pak_file_full(pak, actual_edit_path, output_pak, target_path=target_path, force_add=True)

                sd_res = Path("/sdcard/FeaturesticLeaks/RESULT")
                if sd_res.exists():
                    try:
                        shutil.copy2(output_pak, sd_res / pak_file.name)
                        console.print(f'[bold green][+] Saved to SDCard: {sd_res / pak_file.name}[/bold green]')
                    except Exception:
                        pass

                if count > 0:
                    console.print(f'[bold green][OK] Injected {count} file(s) successfully -> {output_pak.name}[/bold green]')
                    console.print(f'[bold green][+] Full Output Path: {output_pak}[/bold green]')
                    if pak_file.parent != pak_dir and pak_file.parent.exists():
                        copy_back = safe_input('\n-> Copy repacked PAK back to original directory? (y/N): ').strip().lower()
                        if copy_back == 'y':
                            shutil.copy2(output_pak, pak_file)
                            console.print(f'[bold green][OK] Updated original file at {pak_file}[/bold green]')
                else:
                    console.print('[bold red][X] No files were injected.[/bold red]')

            except Exception as e:
                handle_exception(e, "Inject Path", data_path)
            safe_input('\nPress Enter to continue...')

        elif choice == '5':
            run_white_body_mod(data_path)
            safe_input('\nPress Enter to continue...')

        elif choice == '6':
            run_skin_id_modder(data_path)
            safe_input('\nPress Enter to continue...')

        elif choice == '7':
            run_obb_manager(data_path)
            safe_input('\nPress Enter to continue...')

        elif choice == '8':
            run_pak_compare_dumper(data_path)
            safe_input('\nPress Enter to continue...')

        elif choice == '0':
            break
        else:
            console.print('[bold red][X] Invalid choice.[/bold red]')
            time.sleep(1)

def lua_tools_menu(data_path: Path):
    while True:
        print_banner()
        menu_table = Table(
            title="[bold green]🌙 LUA TOOLS 🌙[/bold green]",
            show_header=True,
            header_style="bold green",
            box=ROUNDED,
            border_style="green",
            expand=True
        )
        menu_table.add_column("OPT", justify="center", width=8, style="bold green")
        menu_table.add_column("COMMAND", justify="left", width=22, style="bold white")
        menu_table.add_column("DESCRIPTION", justify="left", style="green")

        menu_table.add_row("[1]", "Compile Lua", "Convert .lua source to .luac bytecode")
        menu_table.add_row("[2]", "Decompile Lua", "Convert .luac bytecode to .lua source")
        menu_table.add_row("[3]", "Extract PAK from Lua", "Extract embedded PAK/Hex/Base64 payload from GG script")
        menu_table.add_row("[4]", "Embed PAK into Lua", "Convert PAK to Base64 & embed in GG Lua installer script")
        menu_table.add_row("[0]", "EXIT ✗", "Return to Main Menu")

        console.print(menu_table)
        console.print()
        choice = safe_input('\033[1;32mSELECT OPTION [1-4] [0]: \033[0m').strip()

        if choice == '1':
            run_lua_compiler(data_path)
            safe_input('\nPress Enter to continue...')
        elif choice == '2':
            run_lua_decompiler(data_path)
            safe_input('\nPress Enter to continue...')
        elif choice == '3':
            run_lua_pak_extractor(data_path)
            safe_input('\nPress Enter to continue...')
        elif choice == '4':
            run_pak_lua_embedder(data_path)
            safe_input('\nPress Enter to continue...')
        elif choice == '0':
            break
        else:
            console.print('[bold red][X] Invalid choice.[/bold red]')
            time.sleep(1)

def utilities_menu(data_path: Path):
    while True:
        print_banner()
        menu_table = Table(
            title="[bold green]🛠️ UTILITIES & HELP 🛠️[/bold green]",
            show_header=True,
            header_style="bold green",
            box=ROUNDED,
            border_style="green",
            expand=True
        )
        menu_table.add_column("OPT", justify="center", width=8, style="bold green")
        menu_table.add_column("COMMAND", justify="left", width=22, style="bold white")
        menu_table.add_column("DESCRIPTION", justify="left", style="green")

        menu_table.add_row("[1]", "UE4 String Tool", "Extract & repack .uasset/.uexp strings")
        menu_table.add_row("[2]", "File Finder", "Search .uasset/.uexp/.ubulk by pattern")
        menu_table.add_row("[3]", "Workspace Summary", "Folder guide & live file count summary")
        menu_table.add_row("[4]", "Termux Auto-Setup", "Setup 'leak' direct command & SDCard folders")
        menu_table.add_row("[5]", "Cleanup Workspace", "Delete workspace folders")
        menu_table.add_row("[0]", "EXIT ✗", "Return to Main Menu")

        console.print(menu_table)
        console.print()
        choice = safe_input('\033[1;32mSELECT OPTION [1-5] [0]: \033[0m').strip()

        if choice == '1':
            run_ue4_string_tool(data_path)
            safe_input('\nPress Enter to continue...')
        elif choice == '2':
            run_file_finder_tool(data_path)
            safe_input('\nPress Enter to continue...')
        elif choice == '3':
            print_banner()
            display_workspace_summary(data_path)
            show_workflow_guide()
            safe_input('\nPress Enter to continue...')
        elif choice == '4':
            install_termux_shortcut_and_sdcard(data_path)
            safe_input('\nPress Enter to continue...')
        elif choice == '5':
            delete_folder(data_path)
            safe_input('\nPress Enter to continue...')
        elif choice == '0':
            break
        else:
            console.print('[bold red][X] Invalid choice.[/bold red]')
            time.sleep(1)

_BOOTED = False

def main_menu():
    global _BOOTED
    if not _BOOTED:
        boot_sequence()
        _BOOTED = True

    play_welcome_audio()
    if getattr(sys, 'frozen', False):
        data_path = Path(sys.executable).parent
    else:
        data_path = Path(__file__).parent
    ensure_directories(data_path)
    try:
        install_termux_shortcut_and_sdcard(data_path)
    except Exception:
        pass
    check_and_auto_update()

    while True:
        print_banner()
        display_workspace_summary(data_path)
        menu_table = Table(
            title="[bold green]🟢 MAIN MENU 🟢[/bold green]",
            show_header=True,
            header_style="bold green",
            box=ROUNDED,
            border_style="green",
            expand=True
        )
        menu_table.add_column("OPT", justify="center", width=8, style="bold green")
        menu_table.add_column("COMMAND", justify="left", width=22, style="bold white")
        menu_table.add_column("DESCRIPTION", justify="left", style="green")

        menu_table.add_row("[1]", "PAK TOOL ✓", "Extract, Repack, Replace & Inject PAK/OBB")
        menu_table.add_row("[2]", "LUA TOOL ✓", "Compile, Decompile & PAK/Lua Embedder")
        menu_table.add_row("[3]", "UTILITIES ✓", "UE4 String Tool, File Finder & Setup")
        menu_table.add_row("[0]", "EXIT ✗", "Close application")

        console.print(menu_table)
        console.print()
        choice = safe_input('\033[1;32mSELECT OPTION [1-3] [0]: \033[0m').strip()

        if choice == '1':
            pak_obb_tools_menu(data_path)
        elif choice == '2':
            lua_tools_menu(data_path)
        elif choice == '3':
            utilities_menu(data_path)
        elif choice == '0':
            console.print("[dim white]Exiting Featurestic Leaks. Goodbye![/dim white]")
            time.sleep(1)
            break
        else:
            console.print('[bold red][X] Invalid category choice.[/bold red]')
            time.sleep(1)

if __name__ == '__main__':
    try:
        main_menu()
    except KeyboardInterrupt:
        console.print('\n[yellow][!] Interrupted. Exiting...[/yellow]')
        sys.exit(0)
    except Exception as e:
        handle_exception(e, "Fatal", Path(__file__).parent)
        safe_input('\nPress Enter to exit...')
        sys.exit(1)
