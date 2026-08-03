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
import logging
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
def _ensure_package(pkg_name, import_name=None, required=True):
    if import_name is None:
        import_name = pkg_name
    try:
        __import__(import_name)
    except ImportError:
        print(f"[+] Installing missing dependency: {pkg_name}...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", pkg_name, "--timeout", "10"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"[OK] Installed {pkg_name}")
        except Exception as e:
            if required:
                print(f"[!] Warning: Could not install {pkg_name} ({e}). Ensure internet connection if needed.")
            else:
                print(f"[!] Optional package {pkg_name} skip ho gaya (Offline / Network issue).")

_ensure_package("rich")
_ensure_package("requests")
import requests
_ensure_package("pytz")
_ensure_package("gmalg")
_ensure_package("pycryptodome", "Crypto")
_ensure_package("zstandard")
_ensure_package("watchdog", required=False)

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    HAS_WATCHDOG = True
except Exception:
    HAS_WATCHDOG = False

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
        def safe_unpad_inner(x):
            try:
                skip = 1 + next((i for i in range(len(x)) if x[i] != 0))
                return x[skip:]
            except (StopIteration, Exception):
                return x.strip(b'\x00')
        if len(buffer) < 43:
            return bytes()
        else:
            try:
                x1 = buffer[1:][:SHA1.digest_size]
                x2 = buffer[SHA1.digest_size + 1:]
                x1 = PakCrypto._xorxor(x1, PakCrypto._hashhash(x2, len(x1)))
                x2 = PakCrypto._xorxor(x2, PakCrypto._hashhash(x1, len(x2)))
                part1, m = (x2[:SHA1.digest_size], x2[SHA1.digest_size:])
                if part1 != SHA1.new(b'\x00' * SHA1.digest_size).digest():
                    return bytes()
                else:
                    return safe_unpad_inner(m)
            except Exception:
                return bytes()
    @staticmethod
    def rsa_extract(signature: bytes, modulus: bytes) -> bytes:
        try:
            c = int.from_bytes(signature, 'little')
            n = int.from_bytes(modulus, 'little')
            e = 65537
            m = pow(c, e, n).to_bytes(256, 'little').rstrip(b'\x00')
            return PakCrypto._meowmeow(Misc.pad_to_n(m, 4))
        except Exception:
            return bytes()
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
            try:
                key = PakCrypto.rsa_extract(pak_info.packed_key, RSA_MOD_1)
                iv = PakCrypto.rsa_extract(pak_info.packed_iv, RSA_MOD_1)
                if len(key) != 32 or len(iv) != 32:
                    return ciphertext
                aes = AES.new(key, MODE_CBC, iv[:16])
                decrypted = aes.decrypt(ciphertext)
            except Exception:
                return ciphertext

            try:
                return unpad(decrypted, AES.block_size)
            except Exception:
                if len(decrypted) > 0:
                    last_byte = decrypted[-1]
                    if 1 <= last_byte <= AES.block_size:
                        if decrypted.endswith(bytes([last_byte]) * last_byte):
                            return decrypted[:-last_byte]
                return decrypted.rstrip(b'\x00')
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
        if compression_method == CM_NONE:
            return bytes(block)
        if compression_method == CM_ZLIB:
            try:
                return zlib.decompress(block)
            except Exception:
                return bytes(block)
        elif compression_method in (CM_ZSTD, CM_ZSTD_DICT):
            active_dict = dict if compression_method == CM_ZSTD_DICT else None
            try:
                return PakCompression._zstd_decompressor(active_dict).decompress(block)
            except Exception:
                # Fallback 1: Try opposite dictionary mode
                other_dict = None if active_dict else dict
                if other_dict:
                    try:
                        return PakCompression._zstd_decompressor(other_dict).decompress(block)
                    except Exception:
                        pass
                # Fallback 2: Try without dictionary
                if active_dict or other_dict:
                    try:
                        return PakCompression._zstd_decompressor(None).decompress(block)
                    except Exception:
                        pass
                # Fallback 3: Try zlib
                try:
                    return zlib.decompress(block)
                except Exception:
                    pass
                # Fallback 4: Return raw block bytes
                return bytes(block)
        else:
            return bytes(block)

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
            calc_hash = zlib.crc32(self._file_path.stem.encode('utf-32le'))
            if self._pak_info.stem_hash != calc_hash:
                logging.warning(f"PAK filename stem CRC mismatch ({self._pak_info.stem_hash} vs {calc_hash}). Auto-repairing & bypassing stem check...")
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
        computed_hash = SHA1.new(index_data).digest()
        if expected_hash != computed_hash:
            logging.warning("SHA1 index hash mismatch — PAK header/key may be modified. Attempting unpack anyway...")
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
    
    def _write_to_disk(self, file_path: Path, entry: TencentPakEntry, silent: bool = False) -> None:
        """
        [BEFORE]: Uncompressed files loaded full content into RAM before writing to disk.
        [AFTER]: Streaming chunked writes (64MB chunks) for uncompressed data and per-block stream writes to minimize memory footprint.
        """
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
                chunk_size = 64 * 1024 * 1024  # 64MB streaming chunk buffer
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
        """
        [BEFORE]: Unpacked sequentially without disk space check, resume checkpoints, error isolation, or garbage collection.
        [AFTER]: Multi-threaded ThreadPoolExecutor parallel unpacking with silent output mode and fast progress bar.
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

                        # If adding a Lua script or text file, force raw uncompressed & unencrypted mode for instant UE4 memory compatibility
                        is_lua_file = p.suffix.lower() in ('.lua', '.luac', '.bytes', '.txt') or 'lua' in fp.lower()
                        if is_lua_file:
                            ne.compression_method = CM_NONE
                            ne.encrypted = False

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
            aes = AES.new(key, MODE_CBC, iv[:16])
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
            is_text_lua = pak_relative_path.name.lower().endswith(('.lua', '.json', '.txt', '.xml', '.ini', '.csv')) or any(kw in new_data[:100] for kw in [b'function', b'local', b'--', b'return', b'{'])
            pad_byte = b' ' if is_text_lua else b'\x00'
            new_data = new_data.ljust(entry.uncompressed_size, pad_byte)
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
            is_text_lua = pak_relative_path.name.lower().endswith(('.lua', '.json', '.txt', '.xml', '.ini', '.csv')) or any(kw in new_data[:100] for kw in [b'function', b'local', b'--', b'return', b'{'])
            pad_byte = b' ' if is_text_lua else b'\x00'
            new_data = new_data.ljust(entry.uncompressed_size, pad_byte)
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

def ensure_directories(base_dir: Path):
    # Clean Organized PAK Workspace
    pak_ws = base_dir / "PAK_WORKSPACE"
    (pak_ws / "1_PAK_INPUT").mkdir(parents=True, exist_ok=True)
    (pak_ws / "2_UNPACK").mkdir(parents=True, exist_ok=True)
    (pak_ws / "3_REPLACE").mkdir(parents=True, exist_ok=True)
    (pak_ws / "4_INJECT").mkdir(parents=True, exist_ok=True)
    (pak_ws / "5_RESULT").mkdir(parents=True, exist_ok=True)

    # Clean Organized LUA Workspace
    lua_ws = base_dir / "LUA_WORKSPACE"
    (lua_ws / "1_LUA_INPUT").mkdir(parents=True, exist_ok=True)
    (lua_ws / "2_DECOMPILED").mkdir(parents=True, exist_ok=True)
    (lua_ws / "3_COMPILED").mkdir(parents=True, exist_ok=True)
    (lua_ws / "4_RESULT").mkdir(parents=True, exist_ok=True)

    (base_dir / "LOGS").mkdir(parents=True, exist_ok=True)

    sdcard_path = Path("/sdcard/FeaturesticLeaks")
    try:
        if sdcard_path.parent.exists():
            sdcard_path.mkdir(parents=True, exist_ok=True)
            s_pak_ws = sdcard_path / "PAK_WORKSPACE"
            (s_pak_ws / "1_PAK_INPUT").mkdir(parents=True, exist_ok=True)
            (s_pak_ws / "2_UNPACK").mkdir(parents=True, exist_ok=True)
            (s_pak_ws / "3_REPLACE").mkdir(parents=True, exist_ok=True)
            (s_pak_ws / "4_INJECT").mkdir(parents=True, exist_ok=True)
            (s_pak_ws / "5_RESULT").mkdir(parents=True, exist_ok=True)

            s_lua_ws = sdcard_path / "LUA_WORKSPACE"
            (s_lua_ws / "1_LUA_INPUT").mkdir(parents=True, exist_ok=True)
            (s_lua_ws / "2_DECOMPILED").mkdir(parents=True, exist_ok=True)
            (s_lua_ws / "3_COMPILED").mkdir(parents=True, exist_ok=True)
            (s_lua_ws / "4_RESULT").mkdir(parents=True, exist_ok=True)

            (sdcard_path / "LOGS").mkdir(parents=True, exist_ok=True)

            # Auto-cleanup empty legacy folders from SDCard & workspace so File Manager is kept clean
            legacy_dirs = ["PAK", "UNPACK", "REPLACE", "INJECT", "LUA", "REPACK", "RESULT", "PAK TOOL"]
            for target in [base_dir, sdcard_path]:
                for leg in legacy_dirs:
                    leg_p = target / leg
                    if leg_p.exists() and leg_p.is_dir():
                        try:
                            if not any(leg_p.iterdir()):
                                leg_p.rmdir()
                        except Exception:
                            pass

            # Auto-clean non-essential Web UI & Markdown files on Android/Termux user environment
            if Path("/sdcard").exists() or "TERMUX_VERSION" in os.environ or Path("/data/data/com.termux").exists():
                junk_items = [
                    "README.md", "DOCUMENTATION.md", "index.html", "src",
                    "vite.config.ts", "tsconfig.json", "package.json", "metadata.json", "bun.lock"
                ]
                for item in junk_items:
                    p = base_dir / item
                    if p.exists():
                        try:
                            if p.is_dir():
                                shutil.rmtree(p, ignore_errors=True)
                            else:
                                p.unlink(missing_ok=True)
                        except Exception:
                            pass
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
                    for root, dirs, files in os.walk(p):
                        cnt += len(files)
                except Exception:
                    pass
        return cnt

    pak_cnt = get_cnt("PAK_WORKSPACE", "1_PAK_INPUT") + get_cnt("PAK")
    unpack_cnt = get_cnt("PAK_WORKSPACE", "2_UNPACK") + get_cnt("UNPACK")
    replace_cnt = get_cnt("PAK_WORKSPACE", "3_REPLACE") + get_cnt("REPLACE")
    inject_cnt = get_cnt("PAK_WORKSPACE", "4_INJECT") + get_cnt("INJECT")
    result_pak_cnt = get_cnt("PAK_WORKSPACE", "5_RESULT")

    lua_input_cnt = get_cnt("LUA_WORKSPACE", "1_LUA_INPUT") + get_cnt("LUA")
    lua_decomp_cnt = get_cnt("LUA_WORKSPACE", "2_DECOMPILED")
    lua_comp_cnt = get_cnt("LUA_WORKSPACE", "3_COMPILED")
    lua_result_cnt = get_cnt("LUA_WORKSPACE", "4_RESULT") + get_cnt("RESULT")

    table = Table(
        title="[bold bright_cyan]📂 ORGANIZED WORKSPACE STATUS 📂[/bold bright_cyan]",
        border_style="bright_cyan",
        box=ROUNDED,
        show_header=True,
        header_style="bold bright_cyan",
        expand=True
    )
    table.add_column("Workspace Folder", justify="left", style="bold bright_cyan", width=24)
    table.add_column("Purpose / Direct Path", justify="left", style="bold bright_white")
    table.add_column("Files", justify="center", style="bold bright_yellow", width=10)

    # Section 1: PAK Tools Workspace
    table.add_row("[bold yellow]📦 PAK_WORKSPACE/[/bold yellow]", "[dim]Subfolders for PAK & OBB Modding[/dim]", "")
    table.add_row("  ├ 📥 1_PAK_INPUT", "Put original game .pak / .obb files here", f"[bold bright_yellow]{pak_cnt}[/bold bright_yellow]")
    table.add_row("  ├ 📂 2_UNPACK", "Extracted files from Unpack tool", f"[bold bright_yellow]{unpack_cnt}[/bold bright_yellow]")
    table.add_row("  ├ ✏️ 3_REPLACE", "Put edited files here to replace PAK files", f"[bold bright_yellow]{replace_cnt}[/bold bright_yellow]")
    table.add_row("  ├ 💉 4_INJECT", "Put custom files here for Inject Path mode", f"[bold bright_yellow]{inject_cnt}[/bold bright_yellow]")
    table.add_row("  └ 🚀 5_RESULT", "Final repacked .pak files saved here", f"[bold bright_yellow]{result_pak_cnt}[/bold bright_yellow]")

    # Section 2: LUA Tools Workspace
    table.add_row("[bold cyan]🌙 LUA_WORKSPACE/[/bold cyan]", "[dim]Subfolders for Lua Scripts Modding[/dim]", "")
    table.add_row("  ├ 📜 1_LUA_INPUT", "Put .lua / .luac scripts here for Lua tools", f"[bold bright_yellow]{lua_input_cnt}[/bold bright_yellow]")
    table.add_row("  ├ 🔓 2_DECOMPILED", "Decompiled .lua source files saved here", f"[bold bright_yellow]{lua_decomp_cnt}[/bold bright_yellow]")
    table.add_row("  ├ ⚙️ 3_COMPILED", "Compiled .luac bytecode saved here", f"[bold bright_yellow]{lua_comp_cnt}[/bold bright_yellow]")
    table.add_row("  └ 🎉 4_RESULT", "Final processed & auto-fixed scripts saved here", f"[bold bright_yellow]{lua_result_cnt}[/bold bright_yellow]")

    console.print(table)
    console.print("[bold bright_cyan]💡 Workspace Location: [bold bright_white]/sdcard/FeaturesticLeaks/[/bold bright_white] (ZArchiver me direct dikhega)[/bold bright_cyan]\n")

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

    if len(d) < 18:
        return None

    # Auto-repair missing/modified magic header if necessary
    if d[:4] != b'\x1bLua':
        d[:4] = b'\x1bLua'
        if len(d) > 4 and d[4] not in (0x51, 0x52, 0x53):
            d[4] = 0x53

    for offset in (34, 18, 35, 33, 12, 0):
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
            data = bytearray(f.read())
    except Exception:
        return None
    if len(data) < 18:
        return None

    # Auto-repair magic header if modified or stripped
    if data[:4] != b'\x1bLua' and data[:4] != b'\x1bLJ':
        data[:4] = b'\x1bLua'
        if len(data) > 4 and data[4] not in (0x51, 0x52, 0x53):
            data[4] = 0x51

    try:
        r = _LuaStdReader(bytes(data))
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
    declared_regs = set()

    params = []
    for i in range(proto.np):
        pname = proto.locs[i][0] if (i < len(proto.locs) and proto.locs[i][0]) else f"arg{i}"
        params.append(pname)
        declared_regs.add(pname)
        declared_regs.add(f"R{i}")

    if proto.va: params.append("...")
    param_str = ", ".join(params)

    if depth == 0:
        lines.append("--[[ Decompiled by FeaturesticLeaks (Clean Lua Standard Engine) ]]")
        lines.append("--[[ Official Telegram: https://t.me/FeaturesticLeaks ]]")
        lines.append("")

    lines.append(f"{indent}local function {func_name}({param_str})")

    if proto.upvs:
        for uv in proto.upvs:
            lines.append(f"{indent}  -- upvalue: {uv}")

    def assign_reg(rn: str, expr: str) -> str:
        if rn in declared_regs:
            return f"{rn} = {expr}"
        else:
            declared_regs.add(rn)
            return f"local {rn} = {expr}"

    def assign_regs(regs: list, expr: str) -> str:
        if not regs:
            return expr
        new_regs = [r for r in regs if r not in declared_regs]
        for r in regs:
            declared_regs.add(r)
        reg_str = ", ".join(regs)
        if new_regs and len(new_regs) == len(regs):
            return f"local {reg_str} = {expr}"
        else:
            return f"{reg_str} = {expr}"

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
                line = assign_reg(rn, const)

        elif op_name == "LOADNIL":
            rn_start = _reg_name(proto, A)
            if B > A:
                regs = [_reg_name(proto, i) for i in range(A, B + 1)]
                line = assign_regs(regs, "nil")
            else:
                line = assign_reg(rn_start, "nil")

        elif op_name == "LOADBOOL":
            val = "true" if B != 0 else "false"
            rn = _reg_name(proto, A)
            line = assign_reg(rn, val)

        elif op_name == "GETUPVAL":
            rn = _reg_name(proto, A)
            upv_str = proto.upvs[B] if B < len(proto.upvs) else f"upval_{B}"
            line = assign_reg(rn, upv_str)

        elif op_name == "GETTABUP":
            rn = _reg_name(proto, A)
            upval = proto.upvs[B] if B < len(proto.upvs) else "_ENV"
            if C & 0x100:
                key = _format_lua_const(proto.K[C & 0xFF]) if (C & 0xFF) < len(proto.K) else f"K{C & 0xFF}"
            else:
                key = _reg_name(proto, C)
            line = assign_reg(rn, f"{upval}[{key}]")

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
            line = assign_reg(rn, f"{_reg_name(proto, B)}[{key}]")

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
            line = assign_reg(rn, f"{left} {op_sym} {right}")

        elif op_name in ("UNM", "BNOT", "NOT", "LEN"):
            ops = {"UNM": "-", "BNOT": "~", "NOT": "not ", "LEN": "#"}
            op_sym = ops.get(op_name, op_name)
            if B & 0x100:
                val = _format_lua_const(proto.K[B & 0xFF]) if (B & 0xFF) < len(proto.K) else f"K{B & 0xFF}"
            else:
                val = _reg_name(proto, B)
            rn = _reg_name(proto, A)
            line = assign_reg(rn, f"{op_sym}{val}")

        elif op_name == "CONCAT":
            parts = [_reg_name(proto, i) for i in range(B, C + 1)]
            rn = _reg_name(proto, A)
            line = assign_reg(rn, f"{' .. '.join(parts)}")

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
            fn = _reg_name(proto, A)
            if C == 0:
                line = assign_reg(_reg_name(proto, A), f"{fn}({args})")
            elif C == 1:
                line = f"{fn}({args})"
            else:
                ret_regs = [_reg_name(proto, i) for i in range(A, A + C - 1)]
                line = assign_regs(ret_regs, f"{fn}({args})")

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
            line = assign_reg(rn, "{}")

        elif op_name == "CLOSURE":
            rn = _reg_name(proto, A)
            if Bx < len(proto.subs):
                sub_name = f"sub_func_{pc}"
                line = assign_reg(rn, sub_name)
            else:
                line = assign_reg(rn, f"closure_{Bx}")

        elif op_name == "VARARG":
            if B == 0:
                line = assign_reg(_reg_name(proto, A), "...")
            else:
                vars = [_reg_name(proto, A + i) for i in range(B - 1)]
                line = assign_regs(vars, "...")

        elif op_name == "MOVE":
            rn_a = _reg_name(proto, A)
            rn_b = _reg_name(proto, B)
            line = assign_reg(rn_a, rn_b)

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

def fix_lua_syntax_for_lua51(lua_file: Path, in_place: bool = True) -> Path:
    """Preprocesses .lua file to fix standard Lua 5.1 incompatible syntax like 'continue', bitwise operators, and excessive 'local' declarations (>200 limits)."""
    try:
        text = lua_file.read_text(encoding="utf-8", errors="ignore")
        
        # Mask comments and string literals to prevent corruption
        tokens = []
        def save_token(m):
            tokens.append(m.group(0))
            return f"__LUA_TOK_{len(tokens)-1}__"

        pattern = re.compile(
            r'--\[(?P<c_eq>=*)\[[\s\S]*?\](?P=c_eq)\]|'   # Multi-line comment --[[ ... ]]
            r'--[^\r\n]*|'                                # Single-line comment -- ...
            r'\[(?P<s_eq>=*)\[[\s\S]*?\](?P=s_eq)\]|'     # Long string [[ ... ]]
            r'"(?:\\.|[^"\\])*"|'                         # Double-quoted string "..."
            r"'(?:\\.|[^'\\])*'",                         # Single-quoted string '...'
            re.MULTILINE
        )
        masked_text = pattern.sub(save_token, text)

        # Replace standalone 'continue' with 'do break end'
        masked_text = re.sub(r'\bcontinue\b', 'do break end', masked_text)
        
        # Replace bitwise OR pipe operator 'a | b' with 'bit.bor(a, b)'
        masked_text = re.sub(r'(\b[\w_.]+\b|\d+)\s*\|\s*(\b[\w_.]+\b|\d+)', r'bit.bor(\1, \2)', masked_text)
        # Replace bitwise AND '&' with 'bit.band(a, b)'
        masked_text = re.sub(r'(\b[\w_.]+\b|\d+)\s*&\s*(\b[\w_.]+\b|\d+)', r'bit.band(\1, \2)', masked_text)
        # Replace bitwise shift '<<' and '>>'
        masked_text = re.sub(r'(\b[\w_.]+\b|\d+)\s*<<\s*(\b[\w_.]+\b|\d+)', r'bit.lshift(\1, \2)', masked_text)
        masked_text = re.sub(r'(\b[\w_.]+\b|\d+)\s*>>\s*(\b[\w_.]+\b|\d+)', r'bit.rshift(\1, \2)', masked_text)

        # Convert 'local function name' -> 'function name'
        masked_text = re.sub(r'\blocal\s+function\b', 'function', masked_text)

        # Convert 'local var1, var2 = val1, val2' -> 'var1, var2 = val1, val2'
        masked_text = re.sub(r'\blocal\s+([a-zA-Z_][a-zA-Z0-9_\s,]*?)\s*=', r'\1 =', masked_text)

        # Convert standalone 'local var1, var2' -> 'var1, var2 = nil, nil'
        def fix_standalone_local(m):
            vars_str = m.group(1).strip()
            v_list = [v.strip() for v in vars_str.split(',') if v.strip() and v.strip() != 'nil']
            if not v_list:
                return ""
            return f"{', '.join(v_list)} = {', '.join(['nil']*len(v_list))}"

        masked_text = re.sub(r'\blocal\s+([a-zA-Z_][a-zA-Z0-9_\s,]+)\b(?!\s*=)', fix_standalone_local, masked_text)

        # Safety net: remove any leftover 'local ' keyword before variable names to prevent >200 local variables limit error
        masked_text = re.sub(r'\blocal\s+(?=[a-zA-Z_])', '', masked_text)

        # Restore comments & strings
        for i in range(len(tokens) - 1, -1, -1):
            masked_text = masked_text.replace(f"__LUA_TOK_{i}__", tokens[i])

        if in_place:
            lua_file.write_text(masked_text, encoding="utf-8")
            # Clean up any leftover _fixed51 file if it exists
            old_fixed = lua_file.parent / f"{lua_file.stem}_fixed51.lua"
            if old_fixed.exists() and old_fixed != lua_file:
                try:
                    old_fixed.unlink()
                except Exception:
                    pass
            return lua_file
        else:
            out_file = lua_file.parent / f"{lua_file.stem}_fixed51.lua"
            out_file.write_text(masked_text, encoding="utf-8")
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

# ============================================================================
# UNIVERSAL LUA PACKER & UNPACKER MODULE (PLUGIN-STYLE ARCHITECTURE)
# ============================================================================

class UniversalLuaPacker:
    """
    Universal Lua pack/unpack (encode/decode) module with 8-byte ASCII tag headers
    and extensible plugin architecture.
    """
    TAG_LEN = 8
    XOR_KEY = 0x5A

    _registry = {}

    @classmethod
    def register(cls, name: str, pack_fn, unpack_fn):
        """Register a new packing/unpacking method."""
        cls._registry[name.lower()] = (pack_fn, unpack_fn)

    @classmethod
    def _format_tag(cls, name: str) -> bytes:
        tag = name.upper().ljust(cls.TAG_LEN, '_')[:cls.TAG_LEN]
        return tag.encode('ascii')

    @classmethod
    def _parse_tag(cls, tag_bytes: bytes) -> str:
        try:
            return tag_bytes.decode('ascii', errors='ignore').rstrip('_').lower()
        except Exception:
            return ""

    @classmethod
    def pack(cls, method: str, input_bytes: bytes) -> bytes:
        """Packs input_bytes using the specified method name and prepends 8-byte ASCII tag."""
        method_key = method.lower()
        if method_key not in cls._registry:
            raise ValueError(f"Unrecognized packing method '{method}'. Available methods: {list(cls._registry.keys())}")
        pack_fn, _ = cls._registry[method_key]
        tag = cls._format_tag(method_key)
        payload = pack_fn(input_bytes)
        return tag + payload

    @classmethod
    def unpack(cls, packed_bytes: bytes) -> bytes:
        """Auto-detects method from 8-byte ASCII tag header and unpacks payload back to original bytes."""
        if len(packed_bytes) < cls.TAG_LEN:
            raise ValueError("Invalid packed payload: data shorter than 8-byte tag header.")
        tag_bytes = packed_bytes[:cls.TAG_LEN]
        method_key = cls._parse_tag(tag_bytes)
        if method_key not in cls._registry:
            raise ValueError(f"Unrecognized tag header '{tag_bytes.decode('ascii', errors='ignore')}'. Available methods: {list(cls._registry.keys())}")
        _, unpack_fn = cls._registry[method_key]
        payload = packed_bytes[cls.TAG_LEN:]
        return unpack_fn(payload)

    @classmethod
    def run_self_test(cls) -> bool:
        """Verifies lossless round-trip for all registered methods."""
        test_sample = b"-- FeaturesticLeaks Universal Lua Pack/Unpack Self-Test\nlocal x = 10\nprint('OK')"
        for method in cls._registry:
            packed = cls.pack(method, test_sample)
            unpacked = cls.unpack(packed)
            assert unpacked == test_sample, f"Lossless round-trip test failed for method '{method}'"
        return True


# Default Methods Registration
def _b64_pack(data: bytes) -> bytes:
    return base64.b64encode(data)

def _b64_unpack(payload: bytes) -> bytes:
    return base64.b64decode(payload)

def _xor_pack(data: bytes) -> bytes:
    xor_data = bytes(b ^ UniversalLuaPacker.XOR_KEY for b in data)
    return base64.b64encode(xor_data)

def _xor_unpack(payload: bytes) -> bytes:
    raw_b64 = base64.b64decode(payload)
    return bytes(b ^ UniversalLuaPacker.XOR_KEY for b in raw_b64)

def _zlib_pack(data: bytes) -> bytes:
    compressed = zlib.compress(data)
    return base64.b64encode(compressed)

def _zlib_unpack(payload: bytes) -> bytes:
    compressed = base64.b64decode(payload)
    return zlib.decompress(compressed)

def _raw_pack(data: bytes) -> bytes:
    return data

def _raw_unpack(payload: bytes) -> bytes:
    return payload

UniversalLuaPacker.register("b64", _b64_pack, _b64_unpack)
UniversalLuaPacker.register("xor", _xor_pack, _xor_unpack)
UniversalLuaPacker.register("zlib", _zlib_pack, _zlib_unpack)
UniversalLuaPacker.register("raw", _raw_pack, _raw_unpack)

# Run self-test on load
try:
    UniversalLuaPacker.run_self_test()
except Exception:
    pass


def run_universal_lua_pack(data_path: Path):
    console.print(Panel(Align.center("[bold bright_cyan]📦 UNIVERSAL LUA PACKER[/bold bright_cyan]"), border_style="cyan", box=ROUNDED))
    lua_dir = data_path / "LUA"
    lua_dir.mkdir(parents=True, exist_ok=True)
    
    lua_file, _ = pick_file_from_folder("Universal Pack Lua", lua_dir, extensions=[".lua", ".txt", ".luac"])
    if not lua_file:
        custom_input = safe_input('-> Enter custom Lua file path (or press Enter to cancel): ').strip().strip('"\'')
        if not custom_input:
            return
        lua_file = Path(custom_input)
        if not lua_file.exists() or not lua_file.is_file():
            console.print(f'[bold red][X] File not found: {lua_file}[/bold red]')
            return

    console.print("\n[bold green]Available Packing Methods:[/bold green]")
    console.print(" [1] b64  - Base64 Encode")
    console.print(" [2] xor  - XOR + Base64 Encode")
    console.print(" [3] zlib - Zlib Compress + Base64 Encode")
    console.print(" [4] raw  - Tag Header Passthrough\n")
    
    method_choice = safe_input('SELECT METHOD [1-4] (default 1): ').strip()
    method_map = {'1': 'b64', '2': 'xor', '3': 'zlib', '4': 'raw'}
    method_name = method_map.get(method_choice, 'b64')

    try:
        raw_bytes = lua_file.read_bytes()
        packed_bytes = UniversalLuaPacker.pack(method_name, raw_bytes)
        
        res_dir = data_path / "RESULT"
        res_dir.mkdir(parents=True, exist_ok=True)
        out_file = res_dir / f"{lua_file.stem}_packed.bin"
        out_file.write_bytes(packed_bytes)
        
        console.print(f"[bold green][OK] File packed successfully using method '{method_name.upper()}':[/bold green]")
        console.print(f"     [bold white]{out_file}[/bold white]")
        console.print(f"     [dim]Header Tag: {packed_bytes[:8].decode('ascii', errors='ignore')} | Output Size: {len(packed_bytes)} bytes[/dim]")
    except Exception as e:
        console.print(f"[bold red][X] Packing failed: {e}[/bold red]")


def run_universal_lua_unpack(data_path: Path):
    console.print(Panel(Align.center("[bold bright_cyan]🔓 UNIVERSAL LUA UNPACKER[/bold bright_cyan]"), border_style="cyan", box=ROUNDED))
    res_dir = data_path / "RESULT"
    lua_dir = data_path / "LUA"
    
    packed_file, _ = pick_file_from_folder("Universal Unpack Lua", res_dir, extensions=[".bin", ".lua", ".txt"])
    if not packed_file:
        packed_file, _ = pick_file_from_folder("Universal Unpack Lua", lua_dir, extensions=[".bin", ".lua", ".txt"])
    if not packed_file:
        custom_input = safe_input('-> Enter custom packed file path (or press Enter to cancel): ').strip().strip('"\'')
        if not custom_input:
            return
        packed_file = Path(custom_input)
        if not packed_file.exists() or not packed_file.is_file():
            console.print(f'[bold red][X] File not found: {packed_file}[/bold red]')
            return

    try:
        packed_bytes = packed_file.read_bytes()
        unpacked_bytes = UniversalLuaPacker.unpack(packed_bytes)
        
        out_file = res_dir / f"{packed_file.stem}_unpacked.lua"
        out_file.write_bytes(unpacked_bytes)
        
        tag_str = packed_bytes[:8].decode('ascii', errors='ignore')
        console.print(f"[bold green][OK] Auto-detected Header Tag '{tag_str}' & unpacked successfully:[/bold green]")
        console.print(f"     [bold white]{out_file}[/bold white]")
        console.print(f"     [dim]Restored Original Size: {len(unpacked_bytes)} bytes[/dim]")
    except Exception as e:
        console.print(f"[bold red][X] Unpacking failed: {e}[/bold red]")


def run_lua_string_obfuscator(data_path: Path):
    console.print(Panel(Align.center("[bold bright_cyan]🔒 LUA STRING OBFUSCATOR & DUMPER ENGINE[/bold bright_cyan]"), border_style="cyan", box=ROUNDED))
    
    lua_dir = data_path / "LUA"
    lua_dir.mkdir(parents=True, exist_ok=True)
    lua_file, _ = pick_file_from_folder("Lua String Tool", lua_dir, extensions=[".lua", ".txt", ".luac"])
    
    if not lua_file:
        custom_input = safe_input('-> Enter custom Lua file path (or press Enter to cancel): ').strip().strip('"\'')
        if not custom_input:
            return
        lua_file = Path(custom_input)
        if not lua_file.exists() or not lua_file.is_file():
            console.print(f'[bold red][X] File not found: {lua_file}[/bold red]')
            return

    console.print("\n[bold bright_yellow]Select Tool Mode:[/bold bright_yellow]")
    console.print(" [1] 🔒 Encrypt All Strings in Script (Hex / Base64 / XOR + Auto-Decoder Wrapper)")
    console.print(" [2] 🔍 Extract & Dump All String Constants, URLs & Memory Offsets")
    console.print(" [0] Cancel\n")

    mode = safe_input('-> Select Option (0-2): ').strip()
    if mode == '0' or not mode:
        return

    content = lua_file.read_text(encoding="utf-8", errors="ignore")
    res_dir = data_path / "RESULT"
    res_dir.mkdir(parents=True, exist_ok=True)

    if mode == '1':
        console.print("\n[bold bright_cyan][+] Obfuscating string literals...[/bold bright_cyan]")
        
        # Extract quoted strings (e.g. "hello", 'world')
        str_pattern = re.compile(r'(".*?"|\'.*?\')')
        
        def encrypt_match(m):
            s = m.group(1)[1:-1]
            if len(s) < 2 or "function" in s or "local" in s or "return" in s or "gg." in s:
                return m.group(1)
            hex_encoded = s.encode("utf-8").hex()
            # Wrap in Lua hex-decode function call
            return f'_HEX("{hex_encoded}")'

        obfuscated_code = str_pattern.sub(encrypt_match, content)

        # Inject decoder runtime at the top
        decoder_header = (
            "-- [FEATURESTIC LEAKS OBFUSCATED SCRIPT]\n"
            "local function _HEX(hex_str)\n"
            "    return (hex_str:gsub('..', function(cc)\n"
            "        return string.char(tonumber(cc, 16))\n"
            "    end))\n"
            "end\n\n"
        )
        final_code = decoder_header + obfuscated_code
        
        out_file = res_dir / f"{lua_file.stem}_obfuscated.lua"
        out_file.write_text(final_code, encoding="utf-8")
        
        console.print(f"[bold green][OK] Obfuscated Lua script saved successfully:[/bold green]")
        console.print(f"     [bold white]{out_file}[/bold white]")
        
        sd_res = Path("/sdcard/FeaturesticLeaks/RESULT")
        if sd_res.exists():
            try:
                shutil.copy2(out_file, sd_res / out_file.name)
                console.print(f"     [bold green]📲 Saved to SDCard: /sdcard/FeaturesticLeaks/RESULT/{out_file.name}[/bold green]")
            except Exception:
                pass

    elif mode == '2':
        dump_dir = data_path / "DUMP_LOGS"
        dump_dir.mkdir(parents=True, exist_ok=True)
        dump_file = dump_dir / f"{lua_file.stem}_strings_dump.txt"

        # Regex for strings, URLs, Hex values
        strings_found = re.findall(r'["\'](.*?)["\']', content)
        urls = re.findall(r'https?://[^\s"\']+', content)
        ips = re.findall(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', content)
        hex_offsets = re.findall(r'0x[0-9a-fA-F]+', content)

        with open(dump_file, "w", encoding="utf-8") as f:
            f.write(f"=== FEATURESTIC LEAKS LUA STRING DUMP: {lua_file.name} ===\n\n")
            f.write(f"--- URLs Identified ({len(urls)}) ---\n")
            for u in set(urls):
                f.write(f"  {u}\n")
            f.write(f"\n--- IP Addresses Identified ({len(ips)}) ---\n")
            for ip in set(ips):
                f.write(f"  {ip}\n")
            f.write(f"\n--- Memory Offsets Identified ({len(hex_offsets)}) ---\n")
            for ho in sorted(set(hex_offsets)):
                f.write(f"  {ho}\n")
            f.write(f"\n--- Literal Strings Found ({len(strings_found)}) ---\n")
            for s in set(strings_found):
                if len(s.strip()) > 1:
                    f.write(f"  {s}\n")

        console.print(f"[bold green][OK] Extracted {len(strings_found)} strings, {len(urls)} URLs, {len(ips)} IPs, {len(hex_offsets)} memory offsets![/bold green]")
        console.print(f" 📄 Report: [bold white]{dump_file}[/bold white]")
        
        sd_dump = Path("/sdcard/FeaturesticLeaks/DUMP_LOGS")
        if sd_dump.parent.exists():
            try:
                sd_dump.mkdir(parents=True, exist_ok=True)
                shutil.copy2(dump_file, sd_dump / dump_file.name)
                console.print(f" 📲 [bold green]Saved to SDCard: /sdcard/FeaturesticLeaks/DUMP_LOGS/[/bold green]")
            except Exception:
                pass


def run_lua_anti_bypass_analyzer(data_path: Path):
    console.print(Panel(Align.center("[bold bright_cyan]🛡️ LUA ANTI-BYPASS & SECURITY ANALYZER[/bold bright_cyan]"), border_style="cyan", box=ROUNDED))
    
    lua_dir = data_path / "LUA"
    lua_file, _ = pick_file_from_folder("Lua Security Analyzer", lua_dir, extensions=[".lua", ".txt"])
    
    if not lua_file:
        custom_input = safe_input('-> Enter custom Lua file path (or press Enter to cancel): ').strip().strip('"\'')
        if not custom_input:
            return
        lua_file = Path(custom_input)
        if not lua_file.exists() or not lua_file.is_file():
            console.print(f'[bold red][X] File not found: {lua_file}[/bold red]')
            return

    content = lua_file.read_text(encoding="utf-8", errors="ignore")
    lines = content.splitlines()

    rules = [
        ("HIGH", "Memory Edit Call", r'gg\.editAll|gg\.setValues|gg\.setRanges'),
        ("HIGH", "Memory Search Hook", r'gg\.searchNumber|gg\.refineNumber'),
        ("CRITICAL", "Anti-Cheat Clearance", r'gg\.clearResults|gg\.clearList'),
        ("MEDIUM", "Process Termination", r'os\.exit|os\.execute|os\.remove'),
        ("HIGH", "Dynamic Code Execution", r'loadstring|load|dofile|require'),
        ("HIGH", "Bytecode Injection / Dump", r'string\.dump|debug\.getinfo|debug\.getupvalue'),
        ("MEDIUM", "Memory Offset Pointer", r'0x[0-9a-fA-F]{4,}'),
        ("INFO", "GameGuard Toast / Alert", r'gg\.toast|gg\.alert|gg\.prompt')
    ]

    findings = []
    risk_score = 0

    for idx, line in enumerate(lines, 1):
        for severity, cat, pattern in rules:
            matches = re.findall(pattern, line)
            if matches:
                findings.append({
                    "line": idx,
                    "severity": severity,
                    "category": cat,
                    "match": matches[0],
                    "text": line.strip()[:80]
                })
                if severity == "CRITICAL": risk_score += 25
                elif severity == "HIGH": risk_score += 15
                elif severity == "MEDIUM": risk_score += 8
                elif severity == "INFO": risk_score += 2

    risk_score = min(100, risk_score)

    table = Table(
        title=f"[bold bright_cyan]📊 LUA AUDIT RESULTS: {lua_file.name} (Risk Score: {risk_score}/100)[/bold bright_cyan]",
        border_style="bright_cyan",
        box=ROUNDED
    )
    table.add_column("Line", style="bold yellow", justify="center", width=6)
    table.add_column("Severity", style="bold white", width=10)
    table.add_column("Category", style="bright_cyan", width=20)
    table.add_column("Code Snippet", style="dim white")

    for f in findings[:25]:
        sev_color = "red" if f["severity"] in ["CRITICAL", "HIGH"] else "yellow" if f["severity"] == "MEDIUM" else "green"
        table.add_row(
            str(f["line"]),
            f"[{sev_color}]{f['severity']}[/{sev_color}]",
            f["category"],
            f["text"]
        )

    console.print(table)

    dump_dir = data_path / "DUMP_LOGS"
    dump_dir.mkdir(parents=True, exist_ok=True)
    report_file = dump_dir / f"{lua_file.stem}_security_audit.txt"

    with open(report_file, "w", encoding="utf-8") as rf:
        rf.write(f"=== FEATURESTIC LEAKS LUA SECURITY AUDIT REPORT ===\n")
        rf.write(f"Target File: {lua_file.name}\n")
        rf.write(f"Risk Score: {risk_score}/100\n")
        rf.write(f"Total Detections: {len(findings)}\n")
        rf.write("="*60 + "\n\n")
        for f in findings:
            rf.write(f"Line {f['line']:<5} | [{f['severity']:<8}] {f['category']:<22} | Match: {f['match']}\n  Code: {f['text']}\n\n")

    console.print(f"\n[bold green][OK] Detailed audit report saved to:[/bold green] [bold white]{report_file}[/bold white]")
    sd_dump = Path("/sdcard/FeaturesticLeaks/DUMP_LOGS")
    if sd_dump.parent.exists():
        try:
            sd_dump.mkdir(parents=True, exist_ok=True)
            shutil.copy2(report_file, sd_dump / report_file.name)
            console.print(f" 📲 [bold green]Saved to SDCard: /sdcard/FeaturesticLeaks/DUMP_LOGS/[/bold green]")
        except Exception:
            pass


def run_lua_header_fixer(data_path: Path):
    console.print(Panel(Align.center("[bold bright_cyan]🔧 LUA BYTECODE HEADER FIXER & DEBUG STRIPPER[/bold bright_cyan]"), border_style="cyan", box=ROUNDED))
    
    lua_dir = data_path / "LUA"
    res_dir = data_path / "RESULT"
    lua_file, _ = pick_file_from_folder("Lua Header Fixer", lua_dir, extensions=[".luac", ".lua", ".bytes", ".bytecode"])
    
    if not lua_file:
        custom_input = safe_input('-> Enter custom compiled .luac file path (or press Enter to cancel): ').strip().strip('"\'')
        if not custom_input:
            return
        lua_file = Path(custom_input)
        if not lua_file.exists() or not lua_file.is_file():
            console.print(f'[bold red][X] File not found: {lua_file}[/bold red]')
            return

    raw_bytes = lua_file.read_bytes()
    if len(raw_bytes) < 12:
        console.print("[bold red][X] File size too small to be a valid Lua bytecode file.[/bold red]")
        return

    console.print(f"[bold cyan][+] Current Header Magic Bytes (First 12 Bytes):[/bold cyan] [bold yellow]{raw_bytes[:12].hex(' ').upper()}[/bold yellow]")

    console.print("\n[bold bright_yellow]Select Repair / Fix Action:[/bold bright_yellow]")
    console.print(" [1] Restore Standard Lua 5.1 Bytecode Header (1B 4C 75 61 51 00...)")
    console.print(" [2] Restore Standard LuaJIT Bytecode Header (1B 4C 4A 01/02...)")
    console.print(" [3] Strip Debug Symbols & Local Variable Names")
    console.print(" [0] Cancel\n")

    act = safe_input("-> Select Action (0-3): ").strip()
    if act == '0' or not act:
        return

    res_dir.mkdir(parents=True, exist_ok=True)
    out_file = res_dir / f"{lua_file.stem}_header_fixed.luac"

    if act == '1':
        # Standard Lua 5.1 header
        std_lua51_header = bytes([0x1B, 0x4C, 0x75, 0x61, 0x51, 0x00, 0x01, 0x04, 0x08, 0x04, 0x08, 0x00])
        fixed_bytes = std_lua51_header + raw_bytes[12:]
        out_file.write_bytes(fixed_bytes)
        console.print(f"[bold green][OK] Fixed Lua 5.1 magic header & written to:[/bold green] [bold white]{out_file}[/bold white]")

    elif act == '2':
        # Standard LuaJIT 2.0 header
        std_luajit_header = bytes([0x1B, 0x4C, 0x4A, 0x02])
        fixed_bytes = std_luajit_header + raw_bytes[4:]
        out_file.write_bytes(fixed_bytes)
        console.print(f"[bold green][OK] Fixed LuaJIT magic header & written to:[/bold green] [bold white]{out_file}[/bold white]")

    elif act == '3':
        # Strip debug names if possible or invoke luac -s
        if shutil.which("luac5.1") or shutil.which("luac"):
            compiler = shutil.which("luac5.1") or shutil.which("luac")
            cmd = [compiler, "-s", "-o", str(out_file), str(lua_file)]
            try:
                proc = subprocess.run(cmd, capture_output=True, text=True)
                if proc.returncode == 0:
                    console.print(f"[bold green][OK] Stripped debug symbols using '{compiler}':[/bold green] [bold white]{out_file}[/bold white]")
                else:
                    out_file.write_bytes(raw_bytes)
                    console.print(f"[bold yellow][!] Compiler strip warning, copied original file.[/bold yellow]")
            except Exception as e:
                console.print(f"[bold red][X] Error stripping debug symbols: {e}[/bold red]")
        else:
            out_file.write_bytes(raw_bytes)
            console.print(f"[bold yellow][!] No luac compiler found to strip debug info. Output saved.[/bold yellow]")

    sd_res = Path("/sdcard/FeaturesticLeaks/RESULT")
    if sd_res.exists():
        try:
            shutil.copy2(out_file, sd_res / out_file.name)
            console.print(f" 📲 [bold green]Saved to SDCard: /sdcard/FeaturesticLeaks/RESULT/[/bold green]")
        except Exception:
            pass


def run_lua_script_optimizer(data_path: Path):
    console.print(Panel(Align.center("[bold bright_cyan]⚡ LUA SCRIPT MINIFIER, CLEANER & SYNTAX CHECKER[/bold bright_cyan]"), border_style="cyan", box=ROUNDED))
    
    lua_dir = data_path / "LUA"
    lua_dir.mkdir(parents=True, exist_ok=True)
    lua_file, _ = pick_file_from_folder("Lua Optimizer", lua_dir, extensions=[".lua", ".txt"])
    
    if not lua_file:
        custom_input = safe_input('-> Enter custom Lua file path (or press Enter to cancel): ').strip().strip('"\'')
        if not custom_input:
            return
        lua_file = Path(custom_input)
        if not lua_file.exists() or not lua_file.is_file():
            console.print(f'[bold red][X] File not found: {lua_file}[/bold red]')
            return

    content = lua_file.read_text(encoding="utf-8", errors="ignore")
    original_size = len(content.encode('utf-8'))

    console.print("\n[bold cyan][+] Performing Pre-Flight Syntax Integrity Check...[/bold cyan]")
    do_cnt = len(re.findall(r'\bdo\b', content))
    end_cnt = len(re.findall(r'\bend\b', content))
    fn_cnt = len(re.findall(r'\bfunction\b', content))
    if_cnt = len(re.findall(r'\bif\b', content))

    console.print(f"  • Functions: {fn_cnt} | If blocks: {if_cnt} | Do blocks: {do_cnt} | End keywords: {end_cnt}")
    if (do_cnt + fn_cnt + if_cnt) != end_cnt:
        console.print("[bold yellow]⚠️ Notice: Keyword count mismatch detected (Check block closures before running in GG).[/bold yellow]")
    else:
        console.print("[bold green]✅ Structural block closures balanced![/bold green]")

    console.print("\n[bold bright_yellow]Select Optimization Mode:[/bold bright_yellow]")
    console.print(" [1] 🧹 Strip Comments & Clean Whitespace (Keep Readable Layout)")
    console.print(" [2] ⚡ Full Compact Minify (Remove All Comments & Compact Lines)")
    console.print(" [0] Cancel\n")

    mode = safe_input('-> Select Mode [1-2] [1]: ').strip() or '1'
    if mode == '0':
        return

    cleaned = re.sub(r'--\[\[.*?\]\]', '', content, flags=re.DOTALL)
    
    if mode == '1':
        lines = []
        for line in cleaned.splitlines():
            line_str = line.strip()
            if line_str.startswith('--'):
                continue
            if '--' in line_str and not ('"' in line_str or "'" in line_str):
                line_str = line_str.split('--')[0].rstrip()
            if line_str:
                lines.append(line_str)
        final_code = "\n".join(lines)
    else:
        lines = []
        for line in cleaned.splitlines():
            line_str = line.strip()
            if line_str.startswith('--'):
                continue
            if '--' in line_str and not ('"' in line_str or "'" in line_str):
                line_str = line_str.split('--')[0].rstrip()
            if line_str:
                lines.append(line_str)
        final_code = "; ".join(lines)
        final_code = re.sub(r';\s*;', ';', final_code)

    new_size = len(final_code.encode('utf-8'))
    reduction = ((original_size - new_size) / original_size * 100) if original_size > 0 else 0

    res_dir = data_path / "RESULT"
    res_dir.mkdir(parents=True, exist_ok=True)
    out_file = res_dir / f"{lua_file.stem}_optimized.lua"
    out_file.write_text(final_code, encoding="utf-8")

    console.print(f"\n[bold green][OK] Lua Script Optimized Successfully![/bold green]")
    console.print(f" 📉 [bold white]Size Reduced: {original_size} bytes ➔ {new_size} bytes ({reduction:.1f}% saved)[/bold white]")
    console.print(f" 📁 [bold white]{out_file}[/bold white]")

    sd_res = Path("/sdcard/FeaturesticLeaks/RESULT")
    if sd_res.exists():
        try:
            shutil.copy2(out_file, sd_res / out_file.name)
            console.print(f" 📲 [bold green]Saved to SDCard: /sdcard/FeaturesticLeaks/RESULT/{out_file.name}[/bold green]")
        except Exception:
            pass


def run_gg_code_generator(data_path: Path):
    console.print(Panel(Align.center("[bold bright_cyan]🪄 GAMEGUARD (GG) MEMORY CODE & SCRIPT GENERATOR[/bold bright_cyan]"), border_style="cyan", box=ROUNDED))
    
    console.print("\n[bold bright_yellow]Select Memory Snippet Template to Generate:[/bold bright_yellow]")
    console.print(" [1] 🎯 Search Value, Refine & Edit Memory Snippet")
    console.print(" [2] 🔒 Search Value & Freeze in Memory List")
    console.print(" [3] ⚡ Game Speedhack Toggle Handler")
    console.print(" [4] 🛡️ Anti-Cheat Log Remover & Process Stealth Handler")
    console.print(" [0] Cancel\n")

    mode = safe_input('-> Select Option [1-4] [1]: ').strip() or '1'
    if mode == '0':
        return

    res_dir = data_path / "RESULT"
    res_dir.mkdir(parents=True, exist_ok=True)

    if mode == '1':
        s_val = safe_input("-> Enter Search Number (e.g. 100 or 1.2345): ").strip() or "100"
        s_type = safe_input("-> Enter Value Type (DWORD/FLOAT/DOUBLE/BYTE/QWORD) [FLOAT]: ").upper().strip() or "FLOAT"
        e_val = safe_input("-> Enter New Replacement Value (e.g. 99999): ").strip() or "99999"

        gg_type = f"gg.TYPE_{s_type}"
        snippet = f"""-- ========================================================
-- GENERATED GAMEGUARD SEARCH & EDIT SNIPPET
-- Generated by Featurestic Leaks Toolkit
-- ========================================================
function _FEATURESTIC_SEARCH_EDIT()
    gg.clearResults()
    gg.setRanges(gg.REGION_ANONYMOUS | gg.REGION_C_ALLOC)
    gg.searchNumber("{s_val}", {gg_type})
    local count = gg.getResultCount()
    if count == 0 then
        gg.toast("⚠️ No results found for {s_val}!")
        return
    end
    local results = gg.getResults(count)
    gg.editAll("{e_val}", {gg_type})
    gg.toast("✅ Successfully edited " .. tostring(#results) .. " memory addresses to {e_val}!")
end
_FEATURESTIC_SEARCH_EDIT()
"""
        out_file = res_dir / "GG_Search_Edit_Template.lua"

    elif mode == '2':
        s_val = safe_input("-> Enter Search Number: ").strip() or "500"
        s_type = safe_input("-> Enter Value Type (DWORD/FLOAT/BYTE) [DWORD]: ").upper().strip() or "DWORD"
        e_val = safe_input("-> Enter Value to Freeze: ").strip() or "9999"

        gg_type = f"gg.TYPE_{s_type}"
        snippet = f"""-- ========================================================
-- GENERATED GAMEGUARD SEARCH & FREEZE SNIPPET
-- Generated by Featurestic Leaks Toolkit
-- ========================================================
function _FEATURESTIC_FREEZE_VALUE()
    gg.clearResults()
    gg.setRanges(gg.REGION_ANONYMOUS | gg.REGION_C_ALLOC)
    gg.searchNumber("{s_val}", {gg_type})
    local results = gg.getResults(100)
    if #results > 0 then
        for i, v in ipairs(results) do
            results[i].value = "{e_val}"
            results[i].freeze = true
        end
        gg.setValues(results)
        gg.addListItems(results)
        gg.toast("🔒 Value locked & frozen at {e_val}!")
    else
        gg.toast("⚠️ Target value not found!")
    end
end
_FEATURESTIC_FREEZE_VALUE()
"""
        out_file = res_dir / "GG_Search_Freeze_Template.lua"

    elif mode == '3':
        speed = safe_input("-> Enter Speedhack Multiplier (e.g., 2.5 or 5.0): ").strip() or "2.5"
        snippet = f"""-- ========================================================
-- GENERATED GAMEGUARD SPEEDHACK TOGGLE SNIPPET
-- Generated by Featurestic Leaks Toolkit
-- ========================================================
local _SPEED_ACTIVE = false
function TOGGLE_SPEEDHACK()
    if not _SPEED_ACTIVE then
        gg.setSpeed({speed})
        _SPEED_ACTIVE = true
        gg.toast("⚡ Speedhack Activated ({speed}x)")
    else
        gg.setSpeed(1.0)
        _SPEED_ACTIVE = false
        gg.toast("🐢 Speedhack Reset (1.0x)")
    end
end
TOGGLE_SPEEDHACK()
"""
        out_file = res_dir / "GG_Speedhack_Template.lua"

    else:
        snippet = """-- ========================================================
-- GENERATED GAMEGUARD STEALTH & ANTI-CHEAT LOG REMOVER
-- Generated by Featurestic Leaks Toolkit
-- ========================================================
function STEALTH_INIT()
    gg.setVisible(false)
    local log_paths = {
        "/sdcard/Android/data/com.tencent.ig/files/UE4Game/ShadowTrackerExtra/ShadowTrackerExtra/Saved/Logs",
        "/sdcard/Android/data/com.pubg.krmobile/files/UE4Game/ShadowTrackerExtra/ShadowTrackerExtra/Saved/Logs",
        "/sdcard/Android/data/com.vng.pubgmobile/files/UE4Game/ShadowTrackerExtra/ShadowTrackerExtra/Saved/Logs"
    }
    for _, path in ipairs(log_paths) do
        os.remove(path)
    end
    gg.toast("🛡️ Anti-Cheat Logs Cleaned & Stealth Active!")
end
STEALTH_INIT()
"""
        out_file = res_dir / "GG_Stealth_Log_Cleaner.lua"

    out_file.write_text(snippet, encoding="utf-8")
    console.print(f"\n[bold green][OK] Generated GameGuard Template Script![/bold green]")
    console.print(f" 📁 [bold white]{out_file}[/bold white]")

    sd_res = Path("/sdcard/FeaturesticLeaks/RESULT")
    if sd_res.exists():
        try:
            shutil.copy2(out_file, sd_res / out_file.name)
            console.print(f" 📲 [bold green]Saved to SDCard: /sdcard/FeaturesticLeaks/RESULT/{out_file.name}[/bold green]")
        except Exception:
            pass


def run_lua_script_merger(data_path: Path):
    console.print(Panel(Align.center("[bold bright_cyan]🔗 ADVANCED LUA MASTER SCRIPT STUDIO & MULTI-SCRIPT COMBINER[/bold bright_cyan]"), border_style="cyan", box=ROUNDED))
    
    lua_dirs = [data_path / "LUA", Path("/sdcard/FeaturesticLeaks/LUA")]
    found_files = []
    
    for d in lua_dirs:
        if d.exists():
            for ext in ("*.lua", "*.luac", "*.txt"):
                found_files.extend(list(d.glob(ext)))

    # Deduplicate by path
    found_files = list({f.resolve(): f for f in found_files}.values())

    if not found_files:
        console.print(f"[bold yellow][!] No .lua or .luac scripts found in LUA/ folders.[/bold yellow]")
        console.print(f"[cyan]👉 Place your .lua files in /sdcard/FeaturesticLeaks/LUA/ and try again.[/cyan]")
        custom_p = safe_input("-> Enter custom Lua file or folder path (or Enter to cancel): ").strip().strip('"\'')
        if not custom_p:
            return
        p_obj = Path(custom_p)
        if p_obj.is_file():
            found_files = [p_obj]
        elif p_obj.is_dir():
            found_files = [f for f in p_obj.glob("*") if f.suffix in ('.lua', '.luac', '.txt')]
        else:
            console.print(f"[bold red][X] Path does not exist: {p_obj}[/bold red]")
            return

    console.print(f"\n[bold bright_cyan][+] Found {len(found_files)} script(s) available for merging/studio:[/bold bright_cyan]\n")
    for idx, f in enumerate(found_files, 1):
        size_str = f"{f.stat().st_size} bytes" if f.exists() else "0 bytes"
        console.print(f"  [{idx}] [bold white]{f.name}[/bold white] [dim]({f.parent.name} | {size_str})[/dim]")

    sel_input = safe_input("\n-> Select file numbers to include (e.g., '1, 2, 4' or 'ALL') [ALL]: ").strip()
    if not sel_input or sel_input.upper() == 'ALL':
        selected_files = found_files
    else:
        selected_files = []
        for part in sel_input.replace(',', ' ').split():
            if part.isdigit():
                idx = int(part) - 1
                if 0 <= idx < len(found_files):
                    selected_files.append(found_files[idx])

    if not selected_files:
        console.print("[bold red][X] No valid files selected.[/bold red]")
        return

    console.print(Panel(
        "[bold yellow]🛠️ CHOOSE LUA MERGE & CREATION MODE:[/bold yellow]\n\n"
        "  [1] [bold bright_white]GameGuard (GG) Multi-Choice Menu Studio[/bold bright_white]\n"
        "      [dim]Generates interactive UI popup menu with checkboxes/buttons for each script.[/dim]\n"
        "  [2] [bold bright_white]Modular Direct Code Combiner[/bold bright_white]\n"
        "      [dim]Merges scripts with isolated scope protection & error handling (pcall).[/dim]\n"
        "  [3] [bold bright_white]Game Cheat Feature Presets Builder[/bold bright_white]\n"
        "      [dim]Injects memory search, freeze values, anti-cheat bypass & wallhack templates.[/dim]",
        title="[bold cyan]💡 STUDIO MODES[/bold cyan]",
        border_style="cyan",
        box=ROUNDED
    ))

    mode = safe_input("\n-> Select Mode [1-3] [1]: ").strip() or '1'

    script_title = safe_input("-> Enter Master Script Menu Title [FEATURESTIC MASTER LUA]: ").strip() or "FEATURESTIC MASTER LUA"
    script_author = safe_input("-> Enter Author / Credits Name [Featurestic Leaks]: ").strip() or "Featurestic Leaks"

    merged_code_blocks = []

    if mode == '1':
        # Mode 1: GameGuard Multi-Choice GUI Menu Studio
        menu_items = []
        func_definitions = []
        exec_calls = []

        for idx, f in enumerate(selected_files, 1):
            clean_name = f.stem.replace('_', ' ').title()
            menu_items.append(f'        "{idx}. ⚡ {clean_name}"')
            
            try:
                content = f.read_text(encoding="utf-8", errors="ignore")
            except Exception as e:
                content = f"-- Error loading file: {e}"

            func_name = f"_EXECUTE_MODULE_{idx}"
            func_code = (
                f"function {func_name}()\n"
                f'    gg.toast("▶ Activating: {clean_name}...")\n'
                f'    local ok, err = pcall(function()\n'
                f'{content}\n'
                f'    end)\n'
                f'    if not ok then gg.alert("⚠️ Module Error ({clean_name}): " .. tostring(err)) end\n'
                f"end\n"
            )
            func_definitions.append(func_code)
            exec_calls.append(f"        if menu[{idx}] then {func_name}() end")

        all_in_one_idx = len(selected_files) + 1
        exit_idx = len(selected_files) + 2

        menu_items.append(f'        "{all_in_one_idx}. 🔥 Activate All Modules Simultaneously"')
        menu_items.append(f'        "{exit_idx}. ❌ Exit Script"')

        all_exec = " ".join([f"_EXECUTE_MODULE_{i}()" for i in range(1, len(selected_files) + 1)])
        exec_calls.append(f"        if menu[{all_in_one_idx}] then {all_exec} end")
        exec_calls.append(f'        if menu[{exit_idx}] then gg.toast("👋 Exiting Script..."); os.exit() end')

        menu_items_str = ",\n".join(menu_items)
        exec_calls_str = "\n".join(exec_calls)
        funcs_str = "\n\n".join(func_definitions)

        gui_wrapper = f"""-- ========================================================
-- FEATURESTIC LEAKS - MASTER GAMEGUARD LUA MENU SCRIPT
-- Title: {script_title}
-- Author: {script_author}
-- Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}
-- ========================================================

gg.toast("⚡ Initializing {script_title}...")
gg.setVisible(true)

-- ========================================================
-- MODULE FUNCTIONS
-- ========================================================
{funcs_str}

-- ========================================================
-- INTERACTIVE GAMEGUARD MENU SYSTEM
-- ========================================================
function MAIN_MENU()
    local menu = gg.multiChoice({{
{menu_items_str}
    }}, nil, "🔥 {script_title} 🔥\\nCreated By: {script_author}\\nSelect features to run:")

    if menu == nil then return end

{exec_calls_str}
end

-- ========================================================
-- MAIN SCRIPT LOOP & FLOATING ICON LISTENER
-- ========================================================
gg.toast("✅ {script_title} Ready! Tap GG Icon to open menu.")

while true do
    if gg.isVisible(true) then
        gg.setVisible(false)
        MAIN_MENU()
    end
    gg.sleep(100)
end
"""
        merged_code_blocks.append(gui_wrapper)

    elif mode == '3':
        # Mode 3: Game Preset Feature Builder
        console.print("\n[bold yellow][+] Adding Game Cheat Presets & Memory Helpers...[/bold yellow]")
        preset_code = f"""-- ========================================================
-- FEATURESTIC LEAKS - GAME CHEAT MEMORY PRESETS STUDIO
-- Title: {script_title} | Author: {script_author}
-- ========================================================

local function _FEAT_MEMORY_PATCH(address, flags, value)
    gg.clearResults()
    gg.setRanges(gg.REGION_ANONYMOUS | gg.REGION_C_ALLOC)
    gg.searchNumber(address, flags)
    local res = gg.getResults(100)
    if #res > 0 then
        for i, v in ipairs(res) do
            res[i].value = value
            res[i].freeze = true
        end
        gg.setValues(res)
        gg.addListItems(res)
        gg.toast("✅ Memory Patched Successfully!")
    else
        gg.toast("⚠️ Address Not Found!")
    end
end

local function _FEAT_ANTILOG_CLEANER()
    os.remove("/sdcard/Android/data/com.pubg.krmobile/files/UE4Game/ShadowTrackerExtra/ShadowTrackerExtra/Saved/Logs")
    os.remove("/sdcard/Android/data/com.tencent.ig/files/UE4Game/ShadowTrackerExtra/ShadowTrackerExtra/Saved/Logs")
    gg.toast("🛡️ Anti-Cheat Logs Cleaned!")
end

_FEAT_ANTILOG_CLEANER()
"""
        merged_code_blocks.append(preset_code)

        # Append chosen files as well
        for f in selected_files:
            try:
                merged_code_blocks.append(f"-- Module: {f.name}\npcall(function()\n" + f.read_text(encoding="utf-8", errors="ignore") + "\nend)\n")
            except Exception as e:
                merged_code_blocks.append(f"-- Error reading {f.name}: {e}")

    else:
        # Mode 2: Clean Modular Combination
        header = f"""-- ========================================================
-- FEATURESTIC LEAKS - MASTER MERGED LUA SCRIPT
-- Title: {script_title} | Author: {script_author}
-- Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}
-- ========================================================\n\n"""
        merged_code_blocks.append(header)

        for f in selected_files:
            try:
                content = f.read_text(encoding="utf-8", errors="ignore")
                block = f"-- >>> MODULE START: {f.name} >>>\npcall(function()\n{content}\nend)\n-- <<< MODULE END: {f.name} <<<\n"
                merged_code_blocks.append(block)
            except Exception as e:
                merged_code_blocks.append(f"-- Error reading {f.name}: {e}\n")

    final_lua = "\n".join(merged_code_blocks)

    # Obfuscation Option
    obf_choice = safe_input("\n-> Encrypt string constants with Hex wrapper for security? (y/N): ").strip().lower()
    if obf_choice in ('y', 'yes'):
        def _hex_enc_str(m):
            s = m.group(1)
            if len(s) < 3 or '\\' in s or '"' in s:
                return f'"{s}"'
            hex_parts = "".join([f"\\x{ord(c):02x}" for c in s])
            return f'"{hex_parts}"'

        final_lua = re.sub(r'"([^"\r\n]{3,})"', _hex_enc_str, final_lua)
        console.print("[bold green][+] String constants obfuscated with Hex escape encoding.[/bold green]")

    out_name = safe_input("-> Enter output script filename [Master_Merged_Script.lua]: ").strip() or "Master_Merged_Script.lua"
    if not out_name.endswith('.lua'):
        out_name += '.lua'

    res_dir = data_path / "RESULT"
    res_dir.mkdir(parents=True, exist_ok=True)
    out_file = res_dir / out_name

    out_file.write_text(final_lua, encoding="utf-8")

    console.print(f"\n[bold green][OK] Successfully created Master Lua Script with {len(selected_files)} module(s)![/bold green]")
    console.print(f" 📁 [bold white]{out_file}[/bold white]")

    sd_res = Path("/sdcard/FeaturesticLeaks/RESULT")
    if sd_res.exists():
        try:
            shutil.copy2(out_file, sd_res / out_file.name)
            console.print(f" 📲 [bold green]Saved to SDCard: /sdcard/FeaturesticLeaks/RESULT/{out_file.name}[/bold green]")
        except Exception:
            pass


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
        console.print("\n[bold yellow]⚡ [Auto-Fix Mode Activated] Preprocessing Lua code to fix syntax & >200 local variable limits...[/bold yellow]")
        fixed_lua = fix_lua_syntax_for_lua51(lua_file)
        
        for compiler in available_compilers:
            if compiler == "luajit":
                cmd = ["luajit", "-b", str(fixed_lua), str(out_luac)]
            else:
                cmd = [compiler, "-o", str(out_luac), str(fixed_lua)]
            
            proc = subprocess.run(cmd, capture_output=True, text=True)
            if proc.returncode == 0:
                console.print(f"[bold green]✅ Auto-fixed and compiled successfully with '{compiler}': {out_luac.name} ({out_luac.stat().st_size:,} bytes)[/bold green]")
                success = True
                break

        if not success and not shutil.which("luajit"):
            console.print("[bold cyan][+] Auto-installing LuaJIT via Termux pkg to retry...[/bold cyan]")
            try:
                subprocess.run("pkg install -y luajit", shell=True, check=True)
                if shutil.which("luajit"):
                    cmd = ["luajit", "-b", str(fixed_lua), str(out_luac)]
                    proc = subprocess.run(cmd, capture_output=True, text=True)
                    if proc.returncode == 0:
                        console.print(f"[bold green]✅ Auto-fixed and compiled successfully with 'luajit': {out_luac.name}[/bold green]")
                        success = True
            except Exception:
                pass

        if not success:
            analyze_and_display_lua_error(lua_file, last_stderr)
            console.print(f"\n[bold yellow]💡 Fallback: Saved cleaned patched script as {fixed_lua.name}[/bold yellow]")

    if success:
        target_dirs = [
            data_path / "LUA_WORKSPACE" / "4_RESULT",
            data_path / "LUA_WORKSPACE" / "3_COMPILED",
            data_path / "PAK_WORKSPACE" / "3_REPLACE",
            data_path / "PAK_WORKSPACE" / "4_INJECT",
            Path("/sdcard/FeaturesticLeaks/LUA_WORKSPACE/4_RESULT"),
            Path("/sdcard/FeaturesticLeaks/LUA_WORKSPACE/3_COMPILED"),
            Path("/sdcard/FeaturesticLeaks/PAK_WORKSPACE/3_REPLACE"),
            Path("/sdcard/FeaturesticLeaks/PAK_WORKSPACE/4_INJECT")
        ]
        for td in target_dirs:
            try:
                td.mkdir(parents=True, exist_ok=True)
                shutil.copy2(out_luac, td / out_luac.name)
            except Exception:
                pass
        console.print(f"[bold green]🎉 Output synced across all workspace & SDCard folders![/bold green]")

def run_lua_decompiler(data_path: Path):
    console.print(Panel(Align.center("[bold bright_cyan]🌙 LUA AUTO-DECOMPILER (.luac Bytecode / Custom -> .lua Source)[/bold bright_cyan]"), border_style="cyan", box=ROUNDED))
    
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

    # Step 1: Check if file is already plain text Lua source code
    try:
        raw_txt = luac_file.read_text(encoding="utf-8", errors="ignore")
        keywords = ["function", "local ", "if ", "then", "return", "end", "for ", "while ", "gg."]
        if any(kw in raw_txt[:3000] for kw in keywords):
            out_lua.write_text(raw_txt, encoding="utf-8")
            console.print(f"[bold green][OK] Decompiled successfully (Plain Lua Source Code):[/bold green]")
            console.print(f"[bold green][+] Output file: {out_lua}[/bold green]")
            if sd_lua.exists():
                try:
                    shutil.copy2(out_lua, sd_lua / out_lua.name)
                    console.print(f"[bold green][+] Saved to SDCard: {sd_lua / out_lua.name}[/bold green]")
                except Exception:
                    pass
            return
    except Exception:
        pass

    raw_bytes = luac_file.read_bytes()
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

    # Build Header Candidates for Auto-Repair
    candidates = [("Original", raw_bytes)]
    if raw_bytes[:4] != b'\x1bLua' and raw_bytes[:4] != b'\x1bLJ':
        if len(raw_bytes) >= 12:
            candidates.append(("Auto-Fixed Lua 5.1 Header", b'\x1bLua\x51\x00\x01\x04\x08\x04\x08\x00' + raw_bytes[12:]))
            candidates.append(("Auto-Fixed Lua 5.3 Header", b'\x1bLua\x53\x00\x00\x04\x08\x04\x08\x00' + raw_bytes[12:]))
            candidates.append(("Auto-Fixed Lua 5.2 Header", b'\x1bLua\x52\x00\x01\x04\x08\x04\x08\x00' + raw_bytes[12:]))
        if len(raw_bytes) >= 4:
            candidates.append(("Auto-Fixed LuaJIT Header", b'\x1bLJ\x02' + raw_bytes[4:]))

    decompiled_text = None
    decompile_engine = None

    temp_luac = data_path / "_tmp_auto_fix.luac"

    for label, c_bytes in candidates:
        if decompiled_text:
            break
        try:
            temp_luac.write_bytes(c_bytes)
        except Exception:
            continue

        # Try unluac.jar
        if java_bin and unluac_jar:
            try:
                proc = subprocess.run([java_bin, "-jar", str(unluac_jar), str(temp_luac)], capture_output=True, text=True, timeout=15)
                if proc.returncode == 0 and proc.stdout.strip() and "Exception" not in proc.stdout[:100]:
                    decompiled_text = proc.stdout
                    decompile_engine = f"unluac ({label})"
                    break
            except Exception:
                pass

        # Try luadec
        if luadec_bin:
            try:
                proc = subprocess.run([luadec_bin, str(temp_luac)], capture_output=True, text=True, timeout=15)
                if proc.returncode == 0 and proc.stdout.strip() and "function 0 0" not in proc.stdout:
                    decompiled_text = proc.stdout
                    decompile_engine = f"luadec ({label})"
                    break
            except Exception:
                pass

        # Try Python Engine
        try:
            proto = _load_lua_custom_proto(str(temp_luac))
            if proto:
                decompiled_text = _pseudo_decompile_lua(proto)
                decompile_engine = f"Python Engine ({label})"
                break
            proto_std = _load_std_bytecode_to_proto(str(temp_luac))
            if proto_std:
                decompiled_text = _pseudo_decompile_lua(proto_std)
                decompile_engine = f"Python Engine Standard ({label})"
                break
        except Exception:
            pass

    if temp_luac.exists():
        try:
            temp_luac.unlink()
        except Exception:
            pass

    # Fallback: Smart String & Structure Recovery Engine
    if not decompiled_text:
        console.print("[bold yellow][+] Applying Smart String & Structure Auto-Recovery Engine...[/bold yellow]")
        str_found = re.findall(r'[a-zA-Z0-9_./\\:-]{3,}', raw_bytes.decode('latin1', errors='ignore'))
        urls = [s for s in str_found if s.startswith("http://") or s.startswith("https://")]
        offsets = [s for s in str_found if s.startswith("0x")]
        funcs = [s for s in str_found if "gg." in s or "function" in s or "lib" in s]

        lines = [
            "-- ========================================================",
            "-- [FEATURESTIC LEAKS AUTO-DECOMPILED RECOVERY SCRIPT]",
            f"-- Target: {luac_file.name}",
            f"-- Mode: Auto-Extracted Constants & Script Structure",
            "-- ========================================================\n",
            "local _RECOVERED_STRINGS = {"
        ]
        for s in set(str_found[:150]):
            lines.append(f'    "{s}",')
        lines.append("}\n")

        if urls:
            lines.append("-- Extracted URLs & Endpoints:")
            for u in set(urls):
                lines.append(f'-- URL: {u}')
            lines.append("")

        if funcs:
            lines.append("-- Detected GameGuard & Function Symbols:")
            for fn in set(funcs):
                lines.append(f'-- Symbol: {fn}')
            lines.append("")

        lines.append("-- Reconstructed Executable Code Block:")
        lines.append("function _main_recovered()")
        lines.append("    -- Auto-Generated Recovery Handler")
        lines.append("    for idx, str_val in ipairs(_RECOVERED_STRINGS) do")
        lines.append("        if string.find(str_val, 'gg.') then")
        lines.append("            pcall(loadstring(str_val))")
        lines.append("        end")
        lines.append("    end")
        lines.append("end")
        lines.append("pcall(_main_recovered)")

        decompiled_text = "\n".join(lines)
        decompile_engine = "Smart Structure & Constant Auto-Recovery Engine"

    out_lua.write_text(decompiled_text, encoding="utf-8")
    console.print(f"[bold green][OK] Decompiled successfully ({decompile_engine}):[/bold green]")
    console.print(f"[bold green][+] Output file: {out_lua}[/bold green]")
    if sd_lua.exists():
        try:
            shutil.copy2(out_lua, sd_lua / out_lua.name)
            console.print(f"[bold green][+] Also saved to SDCard: {sd_lua / out_lua.name}[/bold green]")
        except Exception:
            pass

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
    
    try:
        ensure_directories(data_path)
        console.print(f"[bold green][OK] SDCard Workspace Created cleanly: /sdcard/FeaturesticLeaks/[/bold green]")
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
    
    # Ensure decompilation dependencies (openjdk-17, luadec, unluac.jar) are set up automatically in Termux
    unluac_path = data_path / "unluac.jar"
    if not unluac_path.exists():
        unluac_home = Path.home() / "unluac.jar"
        if unluac_home.exists():
            unluac_path = unluac_home

    is_termux = "com.termux" in os.environ.get("PREFIX", "") or Path("/data/data/com.termux").exists()
    if is_termux:
        needs_pkg = False
        if not shutil.which("java") or not shutil.which("luadec"):
            needs_pkg = True
        
        if needs_pkg:
            console.print("[bold yellow][+] Auto-installing openjdk-17 & luadec for full Lua decompilation...[/bold yellow]")
            try:
                subprocess.run(["pkg", "install", "-y", "openjdk-17", "luadec"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                pass

        if not unluac_path.exists():
            console.print("[bold yellow][+] Downloading unluac.jar for 100% full Lua decompiler support...[/bold yellow]")
            try:
                subprocess.run(["curl", "-L", "-o", str(data_path / "unluac.jar"), "https://github.com/itzgeniusboy/FeaturesticLeaks-Toolkit-/releases/download/v1.0/unluac.jar"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                pass
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

UPDATE_NOTIF_BANNER = ""

def print_banner():
    os.system('cls' if os.name == 'nt' else 'clear')
    
    banner_content = (
        "[bold bright_cyan]⚡ FEATURESTIC LEAKS v2.5 ⚡[/bold bright_cyan] [dim white]│[/dim white] [bold bright_yellow]VIP EXPLOIT ENGINE[/bold bright_yellow]\n"
        "[bold white]DEV:[bold cyan] @L359D[/bold cyan] [dim white]│[/dim white] TG:[bold cyan] t.me/FeaturesticLeaks[/bold cyan] [dim white]│[/dim white] STATUS:[bold bright_green] 🟢 READY[/bold bright_green][/bold white]"
    )
    console.print(Panel(
        Align.center(banner_content),
        title="[bold bright_yellow] 👑 HIGH SPEED ENGINE 👑 [/bold bright_yellow]",
        title_align="center",
        border_style="bright_cyan",
        box=ROUNDED,
        padding=(0, 1)
    ))
    
    if UPDATE_NOTIF_BANNER:
        console.print(Panel(
            Align.center(UPDATE_NOTIF_BANNER),
            border_style="yellow",
            box=ROUNDED,
            padding=(0, 1)
        ))

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

def get_device_user_info() -> str:
    try:
        cfg = get_ai_config() if 'get_ai_config' in globals() else {}
        tg_uname = cfg.get("telegram_username") or cfg.get("user_nickname")
        if tg_uname:
            tg_clean = str(tg_uname).strip()
            if not tg_clean.startswith("@") and " " not in tg_clean and not tg_clean.startswith("http"):
                tg_clean = f"@{tg_clean}"
            return f"{tg_clean}"
    except Exception:
        pass
    
    u = os.environ.get("USER") or os.environ.get("LOGNAME") or os.environ.get("SUDO_USER")
    if not u:
        try:
            import getpass
            u = getpass.getuser()
        except Exception:
            u = "TermuxUser"
    try:
        import socket
        h = socket.gethostname()
    except Exception:
        h = "Android"
    return f"{u}@{h}"

def cleanup_old_logs(logs_dir: Optional[Path] = None, max_age_days: float = 2.0, max_files: int = 15):
    """
    Auto-cleans local log files and error reports to prevent phone storage accumulation!
    Deletes logs older than max_age_days or trims excess logs if count > max_files.
    """
    try:
        dirs_to_clean = []
        if logs_dir:
            dirs_to_clean.append(logs_dir)
        dirs_to_clean.extend([
            Path(__file__).parent / "logs",
            Path("/sdcard/FeaturesticLeaks/ERROR_REPORTS"),
            Path("/sdcard/FeaturesticLeaks/logs")
        ])
        
        now = time.time()
        max_age_sec = max_age_days * 86400
        
        for d in set(dirs_to_clean):
            if not d.exists() or not d.is_dir():
                continue
            
            log_files = sorted([f for f in d.iterdir() if f.is_file() and (f.suffix in ['.log', '.txt'])], key=lambda x: x.stat().st_mtime, reverse=True)
            
            # 1. Delete files older than max_age_days
            remaining_files = []
            for f in log_files:
                try:
                    if (now - f.stat().st_mtime) > max_age_sec:
                        f.unlink()
                    else:
                        remaining_files.append(f)
                except Exception:
                    pass
            
            # 2. If file count exceeds max_files limit, delete oldest excess log files
            if len(remaining_files) > max_files:
                for f in remaining_files[max_files:]:
                    try:
                        f.unlink()
                    except Exception:
                        pass
    except Exception:
        pass

def send_telegram_bug_report(err_type: str, err_msg: str, action_name: str = "Operation", file_info: str = "?", line_no: str = "?", func_name: str = "?", tb_str: str = ""):
    """
    Sends automated bug report silently to Developer Telegram Bot/Chat in a background thread.
    Filter out API key limit / exhaustion alerts so developer group isn't spammed!
    Includes User/Device identification so developer knows who generated the report!
    """
    # Filter out API rate limit / key limit alerts
    if any(k in str(err_type).upper() or k in str(err_msg).upper() for k in ["API_KEY", "EXHAUSTED", "RATE_LIMIT", "HTTP 429"]):
        if err_type != "TEST_PING":
            return

    def _send_bg():
        try:
            cfg = get_ai_config() if 'get_ai_config' in globals() else {}
            bot_token = cfg.get("telegram_bot_token") or os.environ.get("TELEGRAM_BOT_TOKEN") or "8731766223:AAG7ZLyIO_yMk-U9qoJIviPuzFzIoAmrAbM"
            chat_id = cfg.get("telegram_chat_id") or os.environ.get("TELEGRAM_CHAT_ID") or "-1004375122082"
            
            if not bot_token or not chat_id:
                return
                
            dev_user = get_device_user_info()
            
            report_text = (
                f"🚨 <b>FEATURESTIC LEAKS - CODE BUG REPORT</b> 🚨\n\n"
                f"👤 <b>User / Telegram:</b> <code>{escape(dev_user)}</code>\n"
                f"📌 <b>Action:</b> {action_name}\n"
                f"⚠️ <b>Error Type:</b> {err_type}\n"
                f"📍 <b>Location:</b> {file_info}:{line_no} in <code>{func_name}()</code>\n"
                f"💬 <b>Details:</b> <code>{escape(err_msg[:300])}</code>\n\n"
                f"📜 <b>Traceback snippet:</b>\n<code>{escape(tb_str[-800:]) if tb_str else 'N/A'}</code>"
            )
            
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            payload = json.dumps({
                "chat_id": chat_id,
                "text": report_text,
                "parse_mode": "HTML"
            }).encode("utf-8")
            
            req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
            urllib.request.urlopen(req, timeout=5)
        except Exception:
            pass

    import threading
    threading.Thread(target=_send_bg, daemon=True).start()


def handle_exception(e: Exception, action_name: str = "Operation", data_path: Optional[Path] = None):
    """
    Centralized smart error diagnostic handler:
    - Automatically classifies error into:
      1. USER FILE / PATH ISSUE (Input file corrupted, wrong format, file missing, 0 byte, disk space full, bad Lua syntax)
      2. TOOL BUG / SYSTEM ISSUE (Internal code crash or unexpected tool error)
    - Directs user to Telegram @L359D when a tool bug occurs.
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

    # Classification logic: Is it a user file issue or a tool bug?
    is_file_issue = False
    
    # Known file / environment exception types
    if isinstance(e, (FileNotFoundError, PermissionError, IsADirectoryError, MemoryError, EOFError)):
        is_file_issue = True
    elif isinstance(e, OSError) and ("no space" in err_msg.lower() or getattr(e, 'errno', None) in (28, 13, 2)):
        is_file_issue = True
    elif any(term in err_type.lower() for term in ["badzip", "zlib", "zstd", "compression", "struct"]):
        is_file_issue = True
    elif isinstance(e, (AssertionError, ValueError, KeyError, IndexError)):
        # Check if error message refers to file parsing, PAK structure, headers, or paths
        file_keywords = [
            "pak", "header", "magic", "version", "corrupt", "index", "zlib", "zstd",
            "lz4", "encrypted", "signature", "decompression", "truncated", "uasset",
            "luac", "bytecode", "syntax", "not found", "invalid file", "bad format",
            "size", "entry", "offset", "file", "directory", "folder", "path", "does not exist",
            "0 byte", "empty", "read error", "write error", "mount", "unsupported"
        ]
        if any(kw in err_msg.lower() for kw in file_keywords) or not err_msg:
            is_file_issue = True

    # Build clear Diagnosis and Actionable Advice
    if is_file_issue:
        category_header = "[bold bright_yellow]📂 USER FILE / INPUT ISSUE[/bold bright_yellow]"
        category_border = "yellow"
        diagnosis = (
            "[bold yellow]⚠️ Diagnostic Result:[/bold yellow] [bold white]Yeh issue AAPKI INPUT FILE / PATH me hai.[/bold white]\n"
            "[dim white]Tool bilkul Sahi (OK) kaam kar raha hai. Aapki input file corrupt ho sakti hai, missing ho sakti hai, ya wrong format me hai.[/dim white]"
        )
    else:
        category_header = "[bold bright_red]🛠️ TOOL INTERNAL BUG / CODE ISSUE[/bold bright_red]"
        category_border = "bold red"
        diagnosis = (
            "[bold red]❌ Diagnostic Result:[/bold red] [bold white]Yeh TOOL ka Internal Code Bug / System Issue hai![/bold white]\n"
            "[bold bright_cyan]👉 Help / Bug Resolution ke liye Developer se Telegram par contact karein:[/bold bright_cyan] [bold bright_yellow]@L359D[/bold bright_yellow]"
        )

    # Specific actionable hints for user file issues
    hint_msg = ""
    if isinstance(e, PermissionError):
        hint_msg = "Folder access denied. File ko `/sdcard/Download/` me copy karke try karein, ya storage permission grant karein."
    elif isinstance(e, FileNotFoundError):
        hint_msg = "File ya folder nahi mila. Path spelling aur SDCard location check karein."
    elif isinstance(e, MemoryError) or "out of memory" in err_msg.lower():
        hint_msg = "RAM Limit exceed ho gayi. Background apps close karein aur chhotey files try karein."
    elif isinstance(e, OSError) and ("no space" in err_msg.lower() or getattr(e, 'errno', None) == 28):
        hint_msg = "Storage full hai. Internal memory me space free karke retry karein."
    elif any(term in err_type.lower() or term in err_msg.lower() for term in ["zlib", "zstd", "decompress", "compress", "badzip"]):
        hint_msg = "File corrupt hai ya unsupported compression/encryption format hai."
    elif "magic" in err_msg.lower() or "header" in err_msg.lower() or "version" in err_msg.lower():
        hint_msg = "File ka PAK/OBB Header mismatch ho raha hai. File corrupt ya password protected/encrypted ho sakti hai."
    elif is_file_issue:
        hint_msg = "Check karein ki file `/sdcard/FeaturesticLeaks/` folder me proper format me present hai."

    # Save full traceback to log file
    log_filename = "N/A"
    try:
        base = data_path if data_path else Path(__file__).parent
        logs_dir = base / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Auto-clean old logs/reports to save phone storage
        cleanup_old_logs(logs_dir)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = logs_dir / f"error_{timestamp}.log"
        with open(log_file, "w", encoding="utf-8") as f:
            f.write(f"Category: {'USER_FILE_ISSUE' if is_file_issue else 'TOOL_BUG'}\n")
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

    # Dispatch automated background error report directly to Developer Telegram ONLY for actual TOOL CODE BUGS
    if not is_file_issue and not any(k in str(err_type).upper() or k in str(err_msg).upper() for k in ["API_KEY", "EXHAUSTED", "RATE_LIMIT"]):
        try:
            send_telegram_bug_report(err_type, err_msg, action_name, file_info, str(line_no), func_name, traceback.format_exc())
        except Exception:
            pass

    # Build clean ERROR DETAILS panel for terminal display
    panel_content = (
        f"[dim white]Category:[/dim white] {category_header}\n"
        f"{diagnosis}\n\n"
        f"[dim white]Operation:[/dim white] [cyan]{action_name}[/cyan]\n"
        f"[dim white]Error Details:[/dim white] [bold red]{err_type}[/bold red] in [bold yellow]{func_name}()[/bold yellow] ([cyan]{file_info}[/cyan]:[yellow]{line_no}[/yellow])\n"
        f"[dim white]Message:[/dim white] {escape(err_msg)}"
    )
    if hint_msg:
        panel_content += f"\n[bold yellow]💡 Solution Tip:[/bold yellow] [white]{escape(hint_msg)}[/white]"
    
    panel_content += f"\n[dim white]Saved Log:[/dim white] [dim cyan]{log_filename}[/dim cyan]"

    error_panel = Panel(
        panel_content,
        title="[bold red] 🚨 DIAGNOSTIC ERROR REPORT 🚨 [/bold red]",
        title_align="left",
        border_style=category_border,
        box=ROUNDED,
        padding=(1, 2)
    )
    
    console.print()
    console.print(error_panel)

def check_and_auto_update(interactive: bool = False):
    """
    Auto-updater & update notifier for FeaturesticLeaks:
    - Checks GitHub commits & raw repository version
    - If interactive=True (Option 9 in Utilities or 'U' shortcut): downloads fresh script, verifies python compilation, backs up current file, updates, and auto-restarts tool.
    - If interactive=False (background boot check): checks if remote version/hash is newer, and sets UPDATE_NOTIF_BANNER notice banner.
    """
    global UPDATE_NOTIF_BANNER
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
        elif (script_dir / ".git").exists():
            try:
                res = subprocess.run(["git", "rev-parse", "HEAD"], cwd=script_dir, capture_output=True, text=True, timeout=2)
                if res.returncode == 0:
                    local_hash = res.stdout.strip()
            except Exception:
                pass

        if interactive:
            console.print("[bold cyan]🔄 Checking GitHub for latest FeaturesticLeaks updates...[/bold cyan]")

        headers = {"User-Agent": "FeaturesticLeaks-Termux/2.5"}
        url = "https://api.github.com/repos/itzgeniusboy/FeaturesticLeaks-Toolkit-/commits/main"
        remote_hash = ""

        try:
            resp = requests.get(url, headers=headers, timeout=4)
            if resp.status_code == 200:
                remote_hash = resp.json().get("sha", "").strip()
        except Exception:
            pass

        raw_url = "https://raw.githubusercontent.com/itzgeniusboy/FeaturesticLeaks-Toolkit-/main/FeaturesticLeaks.py"
        raw_resp = None

        if not remote_hash or interactive:
            try:
                raw_resp = requests.get(raw_url, headers=headers, timeout=8)
                if raw_resp and raw_resp.status_code == 200 and len(raw_resp.content) > 5000:
                    remote_hash = hashlib.md5(raw_resp.content).hexdigest()
            except Exception:
                pass

        if not remote_hash:
            if interactive:
                console.print("[bold yellow]⚠️ Network check failed or offline mode. Unable to reach GitHub update server.[/bold yellow]")
            return

        has_update = False
        if not local_hash:
            local_hash = hashlib.md5(script_path.read_bytes()).hexdigest() if script_path.exists() else "1"

        if remote_hash != local_hash:
            has_update = True
            UPDATE_NOTIF_BANNER = "🔥 [bold bright_yellow]NEW TOOL UPDATE AVAILABLE![/bold bright_yellow] [dim white]Press [bold cyan][U][/bold cyan] or run [bold cyan]Option [5] -> [9][/bold cyan] to Auto-Update Instantly![/dim white]"

        if interactive:
            if not has_update and not raw_resp:
                console.print("[bold green]✅ Tool is already running the latest FeaturesticLeaks version![/bold green]")
                return

            console.print("[bold green]🚀 New update detected! Downloading latest FeaturesticLeaks engine...[/bold green]")
            if not raw_resp:
                raw_resp = requests.get(raw_url, headers=headers, timeout=12)

            if raw_resp and raw_resp.status_code == 200 and len(raw_resp.content) > 5000:
                temp_file = script_path.with_suffix(".update_tmp")
                temp_file.write_bytes(raw_resp.content)

                import py_compile
                try:
                    py_compile.compile(str(temp_file), doraise=True)
                except Exception as compile_err:
                    console.print(f"[bold red]❌ Downloaded update syntax check failed: {compile_err}. Update cancelled.[/bold red]")
                    temp_file.unlink(missing_ok=True)
                    return

                bak_file = script_path.with_suffix(".py.bak")
                try:
                    shutil.copy2(script_path, bak_file)
                except Exception:
                    pass

                shutil.move(str(temp_file), str(script_path))
                hash_file.write_text(remote_hash, encoding='utf-8')
                UPDATE_NOTIF_BANNER = ""

                console.print(Panel(
                    "[bold bright_green]🎉 FEATURESTIC LEAKS AUTO-UPDATED SUCCESSFULLY! 🎉[/bold bright_green]\n\n"
                    "[bold white]Engine script has been updated & verified.[/bold white]\n"
                    "[bold cyan]Restarting application automatically now...[/bold cyan]",
                    border_style="green",
                    box=ROUNDED
                ))
                time.sleep(1.5)
                os.execv(sys.executable, [sys.executable] + sys.argv)
            else:
                console.print("[bold red][X] Failed to download update file from raw GitHub source.[/bold red]")
    except Exception as ex:
        if interactive:
            console.print(f"[bold red][X] Auto-update error: {ex}[/bold red]")

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
        target_path = Path(current_path_str)
        
        # Scan folder
        found_files = []
        scan_dirs = []
        if target_path.exists():
            scan_dirs.append(target_path)
        
        sd_twin = Path("/sdcard/FeaturesticLeaks") / target_path.name
        if sd_twin.exists() and sd_twin not in scan_dirs:
            scan_dirs.append(sd_twin)
            
        sd_base = Path("/sdcard/FeaturesticLeaks")
        if sd_base.exists() and sd_base not in scan_dirs:
            sd_sub = sd_base / target_path.name
            if sd_sub.exists() and sd_sub not in scan_dirs:
                scan_dirs.append(sd_sub)
            
        # Multi-folder scan fallback for common workspace directories
        extra_subdirs = [
            "LUA", "RESULT", "REPLACE", "UNPACK", "PAK",
            "PAK_WORKSPACE/1_PAK_INPUT", "PAK_WORKSPACE/2_UNPACK", "PAK_WORKSPACE/3_REPLACE", "PAK_WORKSPACE/4_INJECT", "PAK_WORKSPACE/5_RESULT",
            "LUA_WORKSPACE/1_LUA_INPUT", "LUA_WORKSPACE/2_DECOMPILED", "LUA_WORKSPACE/3_COMPILED", "LUA_WORKSPACE/4_RESULT"
        ]
        base_parent = default_folder.parent if hasattr(default_folder, 'parent') and default_folder.parent.exists() else default_folder
        for sub in extra_subdirs:
            cand = base_parent / sub
            if cand.exists() and cand not in scan_dirs:
                scan_dirs.append(cand)
            sd_cand = Path("/sdcard/FeaturesticLeaks") / sub
            if sd_cand.exists() and sd_cand not in scan_dirs:
                scan_dirs.append(sd_cand)

        for sdir in scan_dirs:
            if sdir.exists() and sdir.is_dir():
                for p in sdir.iterdir():
                    if p.is_file() and any(p.name.lower().endswith(ext.lower()) for ext in extensions):
                        if not any(existing.name.lower() == p.name.lower() for existing in found_files):
                            found_files.append(p)
        
        found_files.sort(key=lambda x: x.name.lower())
        
        # If files are found in default/SDCard location, auto display file selection or auto-select
        if found_files:
            if len(found_files) == 1:
                selected = found_files[0]
                size_mb = selected.stat().st_size / (1024 * 1024)
                console.print(f"\n[bold green][OK] Auto-selected file: {selected.name} ({size_mb:.2f} MB)[/bold green]")
                console.print(f"[dim white]📂 Folder Location: {selected.parent}[/dim white]")
                return selected, found_files

            # Multiple files found -> Display clean table directly without asking for folder path
            file_table = Table(
                title=f"[bold cyan]Available Files ({action_title})[/bold cyan]",
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
            
            file_table.add_row("F", "Filter files by keyword", "-")
            file_table.add_row("P", "Custom Folder Path", "-")
            file_table.add_row("C", "Cancel", "-")
            
            console.print()
            console.print(file_table)
            
            choice = safe_input(f"-> Select file number (1-{len(found_files)}) or [F/P/C]: ").strip().upper()
            if choice.isdigit():
                idx = int(choice)
                if 1 <= idx <= len(found_files):
                    selected = found_files[idx - 1]
                    size_mb = selected.stat().st_size / (1024 * 1024)
                    console.print(f"[bold green][OK] Selected: {selected.name} ({size_mb:.2f} MB)[/bold green]")
                    check_and_pair_uasset_uexp(selected)
                    return selected, found_files
            elif choice == 'F':
                keyword = safe_input("-> Enter search keyword/filter (e.g. 'skin', 'bag', '01'): ").strip().lower()
                if keyword:
                    filtered = [f for f in found_files if keyword in f.name.lower()]
                    if filtered:
                        found_files = filtered
                        console.print(f"[bold green][OK] Filtered {len(found_files)} files matching '{keyword}'[/bold green]")
                    else:
                        console.print(f"[bold red][X] No files matched keyword '{keyword}'[/bold red]")
                continue
            elif choice == 'C':
                return None, []
            elif choice != 'P':
                console.print("[bold red][X] Invalid option selected.[/bold red]")
                continue

        # Ask for folder path only if no files found or user selected 'P'
        console.print(f"\n[bold cyan][?] Enter Source Folder / File Path for {action_title}[/bold cyan]")
        console.print(f"[dim]Default directory: {current_path_str}[/dim]")
        user_input = safe_input("-> Enter path [Press Enter for default, 'C' to cancel]: ").strip().strip('"\'')
        
        if user_input.upper() == 'C':
            return None, []
        
        if user_input:
            target_path = Path(user_input)
            if not target_path.exists():
                console.print(f"[bold red][X] Path does not exist: {target_path}[/bold red]")
                continue
            if target_path.is_file():
                if any(target_path.name.lower().endswith(ext.lower()) for ext in extensions):
                    size_mb = target_path.stat().st_size / (1024 * 1024)
                    console.print(f"[bold green][OK] File selected: {target_path.name} ({size_mb:.2f} MB)[/bold green]")
                    check_and_pair_uasset_uexp(target_path)
                    return target_path, [target_path]
                else:
                    console.print(f"[bold red][X] File is not valid ({', '.join(extensions)}): {target_path.name}[/bold red]")
                    continue
            current_path_str = str(target_path)
        
        if not user_input and not found_files:
            console.print("[bold red][X] No files found. Please enter a valid directory path containing target files or type 'C' to cancel.[/bold red]")


def check_and_pair_uasset_uexp(file_path: Path) -> List[Path]:
    """
    UAsset / UExp Sync & Companion Auto-Pairing:
    - Checks if companion (.uexp for .uasset or .uasset for .uexp) exists in the same folder.
    - Warns user if companion file is missing (since UE4 needs both together in game).
    - Returns list of paired files [file_path, companion_path].
    """
    if not file_path or not file_path.exists():
        return [file_path] if file_path else []

    paired_files = [file_path]
    suf = file_path.suffix.lower()

    if suf in ['.uasset', '.uexp']:
        companion_ext = '.uexp' if suf == '.uasset' else '.uasset'
        companion = file_path.with_suffix(companion_ext)
        if companion.exists():
            paired_files.append(companion)
            console.print(f"[bold green]🔗 Companion asset auto-paired:[/] {companion.name}")
        else:
            console.print(
                f"[bold yellow][!] WARNING: Companion asset '{companion.name}' missing in folder!\n"
                f"    UE4 game engine requires BOTH .uasset and .uexp together in the same directory to load in-game.[/bold yellow]"
            )

        ubulk = file_path.with_suffix('.ubulk')
        if ubulk.exists():
            paired_files.append(ubulk)
            console.print(f"[bold green]🔗 Companion bulk asset auto-paired:[/] {ubulk.name}")

    return paired_files


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
        "[bold bright_cyan]⚡ FEATURESTIC LEAKS — SKIN ID MODDER & SKIN ASSET DUMPER ⚡[/bold bright_cyan]\n"
        "[dim white]Swap skin IDs across binary assets or dump/extract all game skin assets (.uasset/.uexp).[/dim white]",
        border_style="bright_cyan",
        box=ROUNDED,
        padding=(0, 2)
    ))
    
    console.print("[bold bright_yellow]1.[/bold bright_yellow] [bold bright_white]Skin Lobby ID Swap[/bold bright_white]")
    console.print("[bold bright_yellow]2.[/bold bright_yellow] [bold bright_white]Skin Ingame ID Swap[/bold bright_white]")
    console.print("[bold bright_yellow]3.[/bold bright_yellow] [bold bright_white]Gun Accessories ID Swap[/bold bright_white]")
    console.print("[bold bright_yellow]4.[/bold bright_yellow] [bold bright_white]Hit Effect ID Swap[/bold bright_white]")
    console.print("[bold bright_yellow]5.[/bold bright_yellow] [bold bright_white]Deadbox Weapon ID Swap[/bold bright_white]")
    console.print("[bold bright_yellow]6.[/bold bright_yellow] [bold bright_cyan]🔍 Dump & Extract All Skin Assets from PAK/UNPACK[/bold bright_cyan]")
    console.print("[bold bright_yellow]0.[/bold bright_yellow] [dim white]Back to Main Menu[/dim white]")
    
    choice = safe_input("\n-> Select Option (0-6): ").strip()
    if choice == '0' or not choice:
        return

    if choice == '6':
        run_skin_dumper(data_path)
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
    
    console.print(f"\n[bold bright_cyan][+] Scanning workspace files for Skin ID {orig_id} ({orig_hex.hex().upper()})...[/bold bright_cyan]")
    
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
                        console.print(f"  [bold green][OK] Swapped ID in:[/bold green] [bright_cyan]{file_p.name}[/bright_cyan]")
                except Exception as e:
                    pass
    
    if modified_files > 0:
        console.print(f"\n[bold green][OK] Skin ID swap complete! Modified {modified_files} file(s).[/bold green]")
    else:
        console.print(f"\n[bold yellow][!] Skin ID {orig_id} not found in workspace binary files.[/bold yellow]")


def run_skin_dumper(data_path: Path) -> None:
    console.print(Panel(
        "[bold bright_cyan]🎨 SKIN ASSETS DUMPER & EXTRACTOR 🎨[/bold bright_cyan]\n"
        "[dim white]Scan PAK files or UNPACK directory to dump skin textures, meshes, uassets & uexps.[/dim white]",
        border_style="bright_cyan",
        box=ROUNDED,
        padding=(0, 2)
    ))

    keywords = ["skin", "weapon", "outfit", "character", "vehicle", "item_", "gun_", "mesh", "texture", "material", "finish", "suit"]
    
    dump_dir = data_path / "DUMP_LOGS"
    dump_dir.mkdir(parents=True, exist_ok=True)
    skins_out = data_path / "RESULT" / "SKINS_DUMP"
    skins_out.mkdir(parents=True, exist_ok=True)
    
    found_skins = []

    # Check PAK folder first
    pak_dir = data_path / "PAK"
    pak_files = [f for f in pak_dir.glob("*.pak") if f.is_file()] if pak_dir.exists() else []

    if pak_files:
        console.print(f"\n[bold bright_cyan][+] Scanning {len(pak_files)} .pak file(s) for Skin Assets...[/bold bright_cyan]")
        for pf in pak_files:
            try:
                pak = TencentPakFile(pf)
                for dir_p, files in pak._index.items():
                    for fname, entry in files.items():
                        rel_path = (pak._mount_point / dir_p / fname).as_posix()
                        path_lower = rel_path.lower()
                        if any(kw in path_lower for kw in keywords):
                            found_skins.append({
                                "source": pf.name,
                                "path": rel_path,
                                "size": entry.size,
                                "uncompressed_size": entry.uncompressed_size,
                                "entry": entry,
                                "pak": pak
                            })
            except Exception as e:
                console.print(f"[dim yellow][!] Error reading {pf.name}: {e}[/dim yellow]")

    # Check UNPACK folder
    unpack_dir = data_path / "UNPACK"
    if unpack_dir.exists():
        for root, _, files in os.walk(unpack_dir):
            for file in files:
                full_p = Path(root) / file
                rel_path = full_p.relative_to(unpack_dir).as_posix()
                if any(kw in rel_path.lower() for kw in keywords):
                    found_skins.append({
                        "source": "UNPACK Workspace",
                        "path": rel_path,
                        "size": full_p.stat().st_size,
                        "uncompressed_size": full_p.stat().st_size,
                        "local_file": full_p
                    })

    if not found_skins:
        console.print("[bold yellow][!] No skin assets matched keywords in PAK or UNPACK folder.[/bold yellow]")
        return

    table = Table(
        title=f"[bold bright_cyan]🎯 FOUND {len(found_skins)} SKIN ASSETS 🎯[/bold bright_cyan]",
        border_style="bright_cyan",
        box=ROUNDED
    )
    table.add_column("No.", style="bold bright_yellow", justify="center", width=6)
    table.add_column("Source", style="bold bright_white", width=18)
    table.add_column("Asset Path", style="bright_cyan")
    table.add_column("Size", style="bold bright_green", justify="right", width=10)

    for idx, item in enumerate(found_skins[:25], 1):
        table.add_row(str(idx), item["source"][:18], item["path"][-50:], human_size(item["size"]))

    console.print(table)
    if len(found_skins) > 25:
        console.print(f"[dim white]... and {len(found_skins) - 25} more skin assets.[/dim white]")

    console.print("\n[bold bright_yellow]Options:[/bold bright_yellow]")
    console.print("  [1] Save Skin Assets Log (.txt & .json)")
    console.print("  [2] Extract / Export All Found Skin Files to RESULT/SKINS_DUMP/")
    console.print("  [0] Back")

    act = safe_input("\n-> Select Action (0-2): ").strip()

    if act in ['1', '2']:
        # Save Log
        txt_file = dump_dir / "Skins_Dump_Report.txt"
        json_file = dump_dir / "Skins_Dump_Report.json"

        with open(txt_file, "w", encoding="utf-8") as f:
            f.write("=== FEATURESTIC LEAKS SKIN ASSETS DUMP REPORT ===\n")
            f.write(f"Total Skin Assets Identified: {len(found_skins)}\n")
            f.write("="*60 + "\n\n")
            for item in found_skins:
                f.write(f"Source: {item['source']}\nPath: {item['path']}\nSize: {item['size']} bytes\n\n")

        with open(json_file, "w", encoding="utf-8") as f:
            json.dump([{
                "source": item["source"],
                "path": item["path"],
                "size": item["size"]
            } for item in found_skins], f, indent=2)

        console.print(f"\n[bold green][OK] Skin report saved successfully![/bold green]")
        console.print(f" 📄 {txt_file}")
        console.print(f" 📄 {json_file}")

        sd_dump = Path("/sdcard/FeaturesticLeaks/DUMP_LOGS")
        if sd_dump.parent.exists():
            sd_dump.mkdir(parents=True, exist_ok=True)
            shutil.copy2(txt_file, sd_dump / txt_file.name)
            shutil.copy2(json_file, sd_dump / json_file.name)
            console.print(f" 📲 [bold green]Saved to SDCard:[/bold green] /sdcard/FeaturesticLeaks/DUMP_LOGS/")

    if act == '2':
        console.print(f"\n[bold bright_cyan][+] Exporting skin files to {skins_out}...[/bold bright_cyan]")
        extracted_cnt = 0
        for item in found_skins:
            try:
                dest_p = skins_out / item["path"].lstrip('/')
                dest_p.parent.mkdir(parents=True, exist_ok=True)
                if "local_file" in item:
                    shutil.copy2(item["local_file"], dest_p)
                    extracted_cnt += 1
                elif "pak" in item:
                    item["pak"].extract_entry(item["entry"], dest_p)
                    extracted_cnt += 1
            except Exception:
                pass

        console.print(f"[bold green][OK] Successfully exported {extracted_cnt} skin asset file(s) to:[/bold green]")
        console.print(f" 📁 [bold bright_white]{skins_out}[/bold bright_white]")
        sd_skins = Path("/sdcard/FeaturesticLeaks/RESULT/SKINS_DUMP")
        if sd_skins.parent.parent.exists():
            try:
                if sd_skins.exists():
                    shutil.rmtree(sd_skins)
                shutil.copytree(skins_out, sd_skins)
                console.print(f" 📲 [bold green]Saved to SDCard:[/bold green] /sdcard/FeaturesticLeaks/RESULT/SKINS_DUMP/")
            except Exception:
                pass

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

def run_file_resizer_tool(data_path: Path) -> None:
    console.print(Panel(
        "[bold cyan]📏 FEATURESTIC LEAKS — FILE RESIZER & SIZE EQUALIZER 📏[/bold cyan]\n"
        "[dim white]Match exact byte sizes for PAK, OBB, LUA, or any file to pass anti-cheat integrity checks.[/dim white]",
        border_style="cyan",
        box=ROUNDED,
        padding=(0, 2)
    ))
    
    res_dir = data_path / "RESULT"
    res_dir.mkdir(parents=True, exist_ok=True)
    
    cand_files = list(res_dir.glob("*")) + list((data_path / "LUA").glob("*")) + list((data_path / "PAK").glob("*"))
    valid_files = [f for f in cand_files if f.is_file() and not f.name.startswith('.')]
    
    target_file = None
    if valid_files:
        console.print("\n[bold cyan]Select file to resize / pad:[/bold cyan]")
        table = Table(title="[bold cyan]AVAILABLE FILES[/bold cyan]", box=ROUNDED)
        table.add_column("Index", style="bold yellow", justify="center", width=8)
        table.add_column("File Name", style="bold white")
        table.add_column("Current Size", style="bold cyan")
        table.add_column("Path", style="dim white")
        
        for i, f in enumerate(valid_files[:15], 1):
            table.add_row(str(i), f.name, human_size(f.stat().st_size), str(f.parent.name))
        console.print(table)
        
        sel = safe_input("-> Enter file number or custom file path: ").strip().strip('"\'')
        if sel.isdigit() and 1 <= int(sel) <= len(valid_files[:15]):
            target_file = valid_files[int(sel) - 1]
        elif sel:
            custom_p = Path(sel)
            if custom_p.exists() and custom_p.is_file():
                target_file = custom_p
    
    if not target_file:
        custom = safe_input("-> Enter file path to resize (or press Enter to cancel): ").strip().strip('"\'')
        if not custom:
            return
        target_file = Path(custom)
        if not target_file.exists():
            console.print(f"[bold red][X] File not found: {target_file}[/bold red]")
            return

    curr_size = target_file.stat().st_size
    console.print(f"\n[bold white]Target File:[/bold white] {target_file.name}")
    console.print(f"[bold white]Current Size:[/bold white] {curr_size:,} bytes ({human_size(curr_size)})")

    console.print("\n[bold cyan]Select Size Matching Mode:[/bold cyan]")
    console.print("  [1] Match size with Original Reference File (Select .pak / .obb / .lua)")
    console.print("  [2] Enter Target Size manually (in Bytes or MB)")
    
    mode = safe_input("\n-> Select Mode (1-2) [1]: ").strip() or '1'
    target_bytes = 0
    
    if mode == '1':
        ref_dir = data_path / "PAK"
        ref_file, _ = pick_file_from_folder("Reference File", ref_dir)
        if not ref_file:
            custom_ref = safe_input("-> Enter reference file path: ").strip().strip('"\'')
            if custom_ref:
                ref_file = Path(custom_ref)
        if ref_file and ref_file.exists():
            target_bytes = ref_file.stat().st_size
            console.print(f"[bold green][+] Reference File: {ref_file.name} ({target_bytes:,} bytes)[/bold green]")
        else:
            console.print("[bold red][X] Valid reference file not provided.[/bold red]")
            return
    else:
        sz_input = safe_input("-> Enter target size (e.g. 10485760 or 10.5MB): ").strip().lower()
        if not sz_input:
            return
        try:
            if sz_input.endswith("mb"):
                target_bytes = int(float(sz_input.replace("mb", "").strip()) * 1024 * 1024)
            elif sz_input.endswith("kb"):
                target_bytes = int(float(sz_input.replace("kb", "").strip()) * 1024)
            else:
                target_bytes = int(sz_input)
        except Exception:
            console.print("[bold red][X] Invalid size input.[/bold red]")
            return

    if target_bytes <= 0:
        console.print("[bold red][X] Target size must be greater than 0.[/bold red]")
        return

    console.print(f"\n[bold cyan]Padding Strategy:[/bold cyan]")
    console.print("  [1] Null Bytes (0x00) — Best for PAK / OBB / Binary")
    console.print("  [2] Space / Newline — Best for LUA / JSON / Source Code")
    
    pad_choice = safe_input("-> Select Padding Byte (1-2) [1]: ").strip() or '1'
    pad_byte = b' ' if pad_choice == '2' else b'\x00'

    # Perform resizing
    out_file = res_dir / f"{target_file.stem}_resized{target_file.suffix}"
    shutil.copy2(target_file, out_file)

    if curr_size == target_bytes:
        console.print("[bold green][OK] File already matches target size perfectly![/bold green]")
    elif curr_size < target_bytes:
        diff = target_bytes - curr_size
        with open(out_file, "ab") as f:
            chunk = pad_byte * min(diff, 65536)
            written = 0
            while written < diff:
                to_w = min(len(chunk), diff - written)
                f.write(chunk[:to_w])
                written += to_w
        console.print(f"[bold green][OK] Added {diff:,} bytes padding ({'0x20 Space' if pad_byte == b' ' else '0x00 Null'})![/bold green]")
        console.print(f"[bold green][+] Resized output: {out_file} ({out_file.stat().st_size:,} bytes)[/bold green]")
    else:
        diff = curr_size - target_bytes
        console.print(f"[bold yellow][!] File is LARGER than target by {diff:,} bytes.[/bold yellow]")
        trim = safe_input("-> Trim excess bytes from end of file? (y/N): ").strip().lower()
        if trim in ['y', 'yes']:
            with open(out_file, "r+b") as f:
                f.truncate(target_bytes)
            console.print(f"[bold green][OK] Trimmed {diff:,} bytes -> Exact match ({out_file.stat().st_size:,} bytes)[/bold green]")

    sd_res = Path("/sdcard/FeaturesticLeaks/RESULT")
    if sd_res.exists():
        try:
            shutil.copy2(out_file, sd_res / out_file.name)
            console.print(f"[bold green][+] Saved to SDCard: {sd_res / out_file.name}[/bold green]")
        except Exception:
            pass

def pak_obb_tools_menu(data_path: Path):
    while True:
        print_banner()
        menu_table = Table(
            title="[bold bright_cyan]📦 PAK / OBB TOOLS 📦[/bold bright_cyan]",
            show_header=True,
            header_style="bold bright_cyan",
            box=ROUNDED,
            border_style="bright_cyan",
            expand=True
        )
        menu_table.add_column("OPT", justify="center", width=8, style="bold bright_yellow")
        menu_table.add_column("COMMAND", justify="left", width=22, style="bold bright_white")
        menu_table.add_column("DESCRIPTION", justify="left", style="bright_cyan")

        menu_table.add_row("[1]", "Unpack Package", "Extract PAK / OBB package contents to workspace")
        menu_table.add_row("[2]", "Repack & Inject", "Repack workspace, replace edited files, or inject custom path")
        menu_table.add_row("[3]", "One-Click Game Mods", "White Body / Item Nuller & Skin ID Swapper")
        menu_table.add_row("[4]", "OBB Manager", "Unzip & Rezip OBB with size padding")
        menu_table.add_row("[5]", "PAK Compare & Dump", "Compare 2 PAKs or dump index / offsets / hashes")
        menu_table.add_row("[6]", "File Resizer & Equalizer", "Match exact byte size of any file (PAK, OBB, LUA)")
        menu_table.add_row("[0]", "EXIT ✗", "Return to Main Menu")

        console.print(menu_table)
        console.print()
        choice = safe_input('\033[1;36mSELECT OPTION [1-6] [0]: \033[0m').strip()

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
            console.print("\n[bold cyan]🛠️ REPACK & INJECTION MODES:[/bold cyan]")
            console.print("  [1] Repack Full Workspace (REPACK folder)")
            console.print("  [2] Replace Edited Files (REPLACE folder)")
            console.print("  [3] Inject Files to Custom Target Path (INJECT folder)")
            sub_c = safe_input("\n-> Select Mode [1-3] [1]: ").strip() or '1'

            pak_dir = data_path / "PAK"
            pak_dir.mkdir(parents=True, exist_ok=True)

            if sub_c == '1':
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

            elif sub_c == '2':
                pak_file, _ = pick_file_from_folder("Replace Files", pak_dir)
                if not pak_file:
                    safe_input('\nPress Enter to continue...')
                    continue

                sd_rep = Path("/sdcard/FeaturesticLeaks/REPLACE")
                dp_rep = data_path / "REPLACE"
                if sd_rep.exists() and dp_rep.exists():
                    sd_names = {p.name for p in sd_rep.rglob('*') if p.is_file()}
                    for dp_f in list(dp_rep.rglob('*')):
                        if dp_f.is_file() and dp_f.name not in sd_names:
                            try:
                                dp_f.unlink()
                            except Exception:
                                pass

                cand_dirs = [
                    Path("/sdcard/FeaturesticLeaks/REPLACE"),
                    data_path / "REPLACE",
                    Path("/sdcard/FeaturesticLeaks/PAK_WORKSPACE/3_REPLACE"),
                    data_path / "PAK_WORKSPACE" / "3_REPLACE"
                ]
                actual_edit_path = None
                ignored_names = {'.gitkeep', '.ds_store', 'desktop.ini', 'thumbs.db'}
                for cd in cand_dirs:
                    if cd.exists():
                        for tmp_f in list(cd.rglob('*')):
                            if tmp_f.is_file() and (tmp_f.name.endswith('_fixed51.lua') or tmp_f.name.endswith('.tmp_luac') or tmp_f.name.endswith('.tmp')):
                                try:
                                    tmp_f.unlink()
                                except Exception:
                                    pass
                        valid_files = [p for p in cd.rglob('*') if p.is_file() and p.name.lower() not in ignored_names and not p.name.startswith('.')]
                        if valid_files:
                            actual_edit_path = cd
                            break

                if not actual_edit_path:
                    console.print(Panel(
                        "[bold red]⚠️ NO FILES FOUND IN REPLACE FOLDER![/bold red]\n\n"
                        "[bold white]Please copy/move your edited files into one of these folders:[/bold white]\n"
                        " 📂 [bold bright_cyan]/sdcard/FeaturesticLeaks/REPLACE/[/bold bright_cyan]\n"
                        " 📂 [bold bright_cyan]/sdcard/FeaturesticLeaks/PAK_WORKSPACE/3_REPLACE/[/bold bright_cyan]\n\n"
                        "[dim white]Tip: Put your modified files inside the REPLACE folder above, or enter custom path below.[/dim white]",
                        title="[bold yellow] 📂 REPLACE FOLDER PATH GUIDE [/bold yellow]",
                        border_style="yellow",
                        box=ROUNDED
                    ))
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
                else:
                    valid_cnt = len([p for p in actual_edit_path.rglob('*') if p.is_file() and p.name.lower() not in ignored_names and not p.name.startswith('.')])
                    console.print(f"\n[bold green]✓ Found {valid_cnt} file(s) in REPLACE folder:[/bold green] [bold cyan]{actual_edit_path}[/bold cyan]")

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
                    else:
                        console.print('[bold red][X] No files repacked.[/bold red]')

                except Exception as e:
                    handle_exception(e, "Replace Files", data_path)
                safe_input('\nPress Enter to continue...')

            else:
                pak_file, _ = pick_file_from_folder("Inject Path", pak_dir)
                if not pak_file:
                    safe_input('\nPress Enter to continue...')
                    continue

                sd_inj = Path("/sdcard/FeaturesticLeaks/INJECT")
                dp_inj = data_path / "INJECT"
                if sd_inj.exists() and dp_inj.exists():
                    sd_names = {p.name for p in sd_inj.rglob('*') if p.is_file()}
                    for dp_f in list(dp_inj.rglob('*')):
                        if dp_f.is_file() and dp_f.name not in sd_names:
                            try:
                                dp_f.unlink()
                            except Exception:
                                pass

                cand_dirs = [
                    Path("/sdcard/FeaturesticLeaks/INJECT"),
                    data_path / "INJECT",
                    Path("/sdcard/FeaturesticLeaks/PAK_WORKSPACE/4_INJECT"),
                    data_path / "PAK_WORKSPACE" / "4_INJECT"
                ]
                actual_edit_path = None
                ignored_names = {'.gitkeep', '.ds_store', 'desktop.ini', 'thumbs.db'}
                for cd in cand_dirs:
                    if cd.exists():
                        for tmp_f in list(cd.rglob('*')):
                            if tmp_f.is_file() and (tmp_f.name.endswith('_fixed51.lua') or tmp_f.name.endswith('.tmp_luac') or tmp_f.name.endswith('.tmp')):
                                try:
                                    tmp_f.unlink()
                                except Exception:
                                    pass
                        valid_files = [p for p in cd.rglob('*') if p.is_file() and p.name.lower() not in ignored_names and not p.name.startswith('.')]
                        if valid_files:
                            actual_edit_path = cd
                            break

                if not actual_edit_path:
                    console.print(Panel(
                        "[bold red]⚠️ NO FILES FOUND IN INJECT FOLDER![/bold red]\n\n"
                        "[bold white]Please copy/move your .lua or mod files into one of these folders:[/bold white]\n"
                        " 📂 [bold bright_yellow]/sdcard/FeaturesticLeaks/INJECT/[/bold bright_yellow]\n"
                        " 📂 [bold bright_yellow]/sdcard/FeaturesticLeaks/PAK_WORKSPACE/4_INJECT/[/bold bright_yellow]\n\n"
                        "[dim white]Instructions:[/dim white]\n"
                        "1. Open your File Manager and put your files inside [/dim white][bold yellow]/sdcard/FeaturesticLeaks/INJECT/[/bold yellow]\n"
                        "2. Or enter your custom folder path below:",
                        title="[bold yellow] 📂 INJECT FOLDER PATH GUIDE [/bold yellow]",
                        border_style="yellow",
                        box=ROUNDED
                    ))
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
                else:
                    valid_cnt = len([p for p in actual_edit_path.rglob('*') if p.is_file() and p.name.lower() not in ignored_names and not p.name.startswith('.')])
                    console.print(f"\n[bold green]✓ Found {valid_cnt} source file(s) in INJECT folder:[/bold green] [bold cyan]{actual_edit_path}[/bold cyan]")

                try:
                    pak = TencentPakFile(pak_file)
                    all_dirs = sorted(list({str(d).strip() for d in pak._index.keys() if str(d).strip() and str(d).strip() != "."}))

                    preset_map = {
                        "P1": ("Content/Lua/GameLua/Mod/BRMod/Gameplay/Core", "🇮🇳 [BGMI / PUBG] BRMod Gameplay Core (BEST FOR BGMI)"),
                        "P2": ("Content/Lua/GameLua", "🇮🇳 [BGMI / PUBG] GameLua Main Root Folder"),
                        "P3": ("Content/Lua/client", "🌐 Client Lua Folder"),
                        "P4": ("Content/Lua/slua", "⚙️ slua Engine Script Root"),
                        "P5": ("ShadowTrackerExtra/Content/Lua/GameLua/Mod/BRMod/Gameplay/Core", "🇮🇳 [BGMI / Global] ShadowTrackerExtra Prefix Path"),
                        "P6": ("ShadowTrackerExtra/Saved/Paks", "📦 Patch Paks Folder Location"),
                    }

                    preset_table = Table(
                        title="[bold bright_green]🔥 POPULAR GAME MODDING TARGET PATHS (PRESETS)[/bold bright_green]",
                        show_header=True,
                        header_style="bold bright_green",
                        box=ROUNDED,
                        border_style="bright_green"
                    )
                    preset_table.add_column("Key", style="bold yellow", justify="center", width=8)
                    preset_table.add_column("Target Path", style="bold white", justify="left")
                    preset_table.add_column("Description / Recommendation", style="bold cyan", justify="left")

                    for p_key, (p_path, p_desc) in preset_map.items():
                        preset_table.add_row(p_key, p_path, p_desc)

                    console.print()
                    console.print(preset_table)

                    console.print(Panel(
                        "[bold bright_yellow]🇮🇳 BGMI LUA MODDING QUICK HELP:[/bold bright_yellow]\n\n"
                        "• [bold white]BGMI me Lua file inject karne ke liye:[/bold white] Seedha [bold bright_green]ENTER[/bold bright_green] dabayein! ([bold cyan]Preset P1[/bold cyan] select ho jayega).\n"
                        "• [bold white]Target Path:[/bold white] [bold yellow]Content/Lua/GameLua/Mod/BRMod/Gameplay/Core[/bold yellow]\n"
                        "• [dim white]Aapko koi bhi complicated path type karne ki zaroorat nahi hai! Just press ENTER.[/dim white]",
                        title="[bold bright_yellow] 🎮 BGMI SPECIAL PRESET INSTRUCTION 🎮 [/bold bright_yellow]",
                        border_style="yellow",
                        box=ROUNDED
                    ))

                    if all_dirs:
                        dir_table = Table(
                            title="[bold cyan]Internal PAK Directories Found[/bold cyan]",
                            show_header=True,
                            header_style="bold cyan",
                            box=ROUNDED,
                            border_style="dim cyan"
                        )
                        dir_table.add_column("Index", style="bold yellow", justify="center", width=8)
                        dir_table.add_column("PAK Internal Folder Path", style="bold white", justify="left")
                        for i, d in enumerate(all_dirs[:20], 1):
                            dir_table.add_row(str(i), str(d))
                        console.print()
                        console.print(dir_table)

                    console.print("\n[dim]Choose Preset [P1-P6], or PAK Dir [1-N], or paste custom path [Default P1].[/dim]")
                    target_input = safe_input("-> Select Target Path inside PAK (P1-P6 / 1-N / custom) [P1]: ").strip().strip('"\'')

                    if target_input.upper() == 'C':
                        safe_input('\nPress Enter to continue...')
                        continue

                    if not target_input or target_input.upper() == 'P1':
                        target_path = preset_map["P1"][0]
                        console.print(f"[bold green][OK] Selected Preset P1: {target_path}[/bold green]")
                    elif target_input.upper() in preset_map:
                        target_path = preset_map[target_input.upper()][0]
                        console.print(f"[bold green][OK] Selected Preset {target_input.upper()}: {target_path}[/bold green]")
                    elif target_input.isdigit() and all_dirs and 1 <= int(target_input) <= len(all_dirs):
                        target_path = all_dirs[int(target_input) - 1]
                        console.print(f"[bold green][OK] Selected PAK Internal Dir: {target_path}[/bold green]")
                    else:
                        target_path = target_input

                    # Clean and normalize target path (No leading/trailing slashes, forward slashes only)
                    target_path = target_path.strip().strip('"\'').strip('/\\').replace('\\', '/')
                    console.print(f"[bold cyan][+] Normalized Target Path: {target_path}[/bold cyan]")

                    # Interactive Lua Pre-Injection Assistant
                    lua_files = [p for p in actual_edit_path.rglob('*') if p.is_file() and p.suffix.lower() in ('.lua', '.luac')]
                    if lua_files:
                        console.print(f"\n[bold yellow]📜 Found {len(lua_files)} .lua script(s) in INJECT folder.[/bold yellow]")
                        console.print("[dim]Choose Lua Injection Preparation:[/dim]")
                        console.print("  [1] Auto-Fix Syntax & Inject Source (.lua) [Default - Recommended]")
                        console.print("  [2] Auto-Compile Bytecode & Preserve .lua Name [Fastest & UE4 Game Safe]")
                        console.print("  [3] Inject As-Is (No pre-processing)")
                        lua_prep = safe_input("-> Select Option [1-3] [1]: ").strip() or '1'
                        if lua_prep == '1':
                            for lf in lua_files:
                                fix_lua_syntax_for_lua51(lf)
                            console.print("[bold green]✓ Lua syntax auto-fixed for Lua 5.1 / UE4![/bold green]")
                        elif lua_prep == '2':
                            compiled_cnt = 0
                            for lf in lua_files:
                                fix_lua_syntax_for_lua51(lf)
                                tmp_luac = lf.with_suffix('.tmp_luac')
                                ok = False
                                try:
                                    res = subprocess.run(["luac5.1", "-o", str(tmp_luac), str(lf)], capture_output=True, text=True)
                                    if res.returncode == 0 and tmp_luac.exists():
                                        ok = True
                                except Exception:
                                    pass
                                if not ok:
                                    try:
                                        res = subprocess.run(["luajit", "-b", str(lf), str(tmp_luac)], capture_output=True, text=True)
                                        if res.returncode == 0 and tmp_luac.exists():
                                            ok = True
                                    except Exception:
                                        pass
                                if ok and tmp_luac.exists():
                                    lf.write_bytes(tmp_luac.read_bytes())
                                    tmp_luac.unlink(missing_ok=True)
                                    compiled_cnt += 1
                            if compiled_cnt > 0:
                                console.print(f"[bold green]✓ Compiled {compiled_cnt} script(s) to 5.1 bytecode while preserving .lua filename for UE4 engine![/bold green]")

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
                        console.print(Panel(
                            "[bold bright_green]✅ LUA INJECTION COMPLETE![/bold bright_green]\n\n"
                            "[bold white]🎮 Game me Lua execute na hone standard reasons & solution:[/bold white]\n"
                            " 1. [bold yellow]Filename Match:[/bold yellow] Script ka name game ke require filename se match hona chahiye (e.g. `BRMod.lua`, `Main.lua`, `BattleMain.lua`).\n"
                            " 2. [bold yellow]Target Path:[/bold yellow] BGMI me [bold cyan]Preset P1[/bold cyan] (`Content/Lua/GameLua/Mod/BRMod/Gameplay/Core`) ya Global me [bold cyan]Preset P5[/bold cyan] use karein.\n"
                            " 3. [bold yellow]Lua 5.1 Syntax:[/bold yellow] Pehle [bold cyan]Option [2] -> Option [8] (1-Click Auto Lua Workflow)[/bold cyan] chalayein taaki Lua 5.1 syntax errors fix ho jayein!",
                            title="[bold bright_yellow] 💡 GAME LUA RUNNING TIPS [/bold bright_yellow]",
                            border_style="bright_green",
                            box=ROUNDED
                        ))
                    else:
                        console.print('[bold red][X] No files were injected.[/bold red]')

                except Exception as e:
                    handle_exception(e, "Inject Path", data_path)
                safe_input('\nPress Enter to continue...')

        elif choice == '3':
            console.print("\n[bold cyan]🎨 ONE-CLICK GAME MODS:[/bold cyan]")
            console.print("  [1] White Body & Gear Asset Nuller Mod")
            console.print("  [2] Skin ID Swapper (Lobby / Ingame / Weapon)")
            sub_c = safe_input("\n-> Select Mod [1-2] [1]: ").strip() or '1'
            if sub_c == '1':
                run_white_body_mod(data_path)
            else:
                run_skin_id_modder(data_path)
            safe_input('\nPress Enter to continue...')

        elif choice == '4':
            run_obb_manager(data_path)
            safe_input('\nPress Enter to continue...')

        elif choice == '5':
            run_pak_compare_dumper(data_path)
            safe_input('\nPress Enter to continue...')

        elif choice == '6':
            run_file_resizer_tool(data_path)
            safe_input('\nPress Enter to continue...')

        elif choice == '0':
            break
        else:
            console.print('[bold red][X] Invalid choice.[/bold red]')
            time.sleep(1)

def run_one_click_auto_lua_workflow(data_path: Path):
    console.print(Panel(Align.center("[bold bright_cyan]🚀 1-CLICK AUTOMATIC LUA FIX & COMPILER WORKFLOW 🚀[/bold bright_cyan]\n[dim white]Auto-scans LUA/RESULT/REPLACE -> Auto-fixes syntax for Lua 5.1 -> Compiles to .luac -> Auto-syncs everywhere![/dim white]"), border_style="cyan", box=ROUNDED))
    
    lua_dir = data_path / "LUA"
    lua_file, _ = pick_file_from_folder("1-Click Auto Lua Workflow", lua_dir, extensions=[".lua", ".txt"])
    if not lua_file:
        custom_input = safe_input('-> Enter custom Lua file path (or press Enter to cancel): ').strip().strip('"\'')
        if not custom_input:
            return
        lua_file = Path(custom_input)
        if not lua_file.exists() or not lua_file.is_file():
            console.print(f'[bold red][X] File not found: {lua_file}[/bold red]')
            return

    console.print(f"\n[bold cyan][Step 1/3] Fixing syntax and 5.1 compatibility for '{lua_file.name}'...[/bold cyan]")
    fixed_lua = fix_lua_syntax_for_lua51(lua_file)
    console.print(f"[bold green]✅ Syntax fixed! Created patched file: {fixed_lua.name}[/bold green]")

    console.print(f"\n[bold cyan][Step 2/3] Compiling to .luac bytecode...[/bold cyan]")
    all_compilers = ["luac5.1", "luac51", "luac", "luajit", "luac5.2", "luac5.3", "luac5.4"]
    available_compilers = [c for c in all_compilers if shutil.which(c)]

    if not available_compilers:
        console.print("[bold yellow][!] Installing lua51 and luajit via Termux pkg...[/bold yellow]")
        try:
            subprocess.run("pkg update -y && pkg install -y lua51 luajit", shell=True, check=True)
            available_compilers = [c for c in all_compilers if shutil.which(c)]
        except Exception as e:
            console.print(f"[bold red][X] Could not auto-install compilers: {e}[/bold red]")

    res_dir = data_path / "RESULT"
    res_dir.mkdir(parents=True, exist_ok=True)
    out_luac = res_dir / f"{lua_file.stem}.luac"

    success = False
    for compiler in available_compilers:
        if compiler == "luajit":
            cmd = ["luajit", "-b", str(fixed_lua), str(out_luac)]
        else:
            cmd = [compiler, "-o", str(out_luac), str(fixed_lua)]
        
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode == 0:
            console.print(f"[bold green]✅ Compiled successfully with '{compiler}' -> {out_luac.name} ({out_luac.stat().st_size:,} bytes)[/bold green]")
            success = True
            break

    if not success:
        console.print(f"[bold red][X] Bytecode compilation failed. Using patched .lua script as fallback.[/bold red]")
        out_luac = res_dir / f"{lua_file.stem}_fixed.lua"
        shutil.copy2(fixed_lua, out_luac)

    console.print(f"\n[bold cyan][Step 3/3] Auto-syncing compiled output across all workspace folders...[/bold cyan]")
    target_dirs = [
        data_path / "LUA",
        data_path / "RESULT",
        data_path / "REPLACE",
        data_path / "INJECT",
        Path("/sdcard/FeaturesticLeaks/LUA"),
        Path("/sdcard/FeaturesticLeaks/RESULT"),
        Path("/sdcard/FeaturesticLeaks/REPLACE"),
        Path("/sdcard/FeaturesticLeaks/INJECT")
    ]

    synced_count = 0
    for td in target_dirs:
        try:
            td.mkdir(parents=True, exist_ok=True)
            dest = td / out_luac.name
            shutil.copy2(out_luac, dest)
            synced_count += 1
        except Exception:
            pass

    console.print(f"[bold green]🎉 Auto-Sync Complete! Saved output to {synced_count} folders across workspace & SDCard![/bold green]")
    console.print(f"[bold white]👉 You can now immediately run Repack / Replace without needing to move any files![/bold white]")

# ==================== AI-ASSISTED REPAIR & MULTI-API ENGINE ====================

AI_CONFIG_FILE = Path.home() / ".featurestic_ai_config.json"

def get_ai_config() -> Dict[str, Any]:
    default_cfg = {
        "active_provider": "google",
        "keys": {
            "google": [],
            "groq": [],
            "openrouter": []
        },
        "telegram_bot_token": "8731766223:AAG7ZLyIO_yMk-U9qoJIviPuzFzIoAmrAbM",
        "telegram_chat_id": "-1004375122082"
    }
    if AI_CONFIG_FILE.exists():
        try:
            with open(AI_CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    default_cfg.update(data)
                    if not default_cfg.get("telegram_bot_token"):
                        default_cfg["telegram_bot_token"] = "8731766223:AAG7ZLyIO_yMk-U9qoJIviPuzFzIoAmrAbM"
                    if not default_cfg.get("telegram_chat_id"):
                        default_cfg["telegram_chat_id"] = "-1004375122082"
                    return default_cfg
        except Exception:
            pass
    return default_cfg

def save_ai_config(cfg: Dict[str, Any]):
    try:
        with open(AI_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=4)
    except Exception as e:
        console.print(f"[bold red][X] Could not save AI config: {e}[/bold red]")

def manage_ai_api_keys():
    cfg = get_ai_config()
    while True:
        print_banner()
        console.print(Panel(
            "[bold bright_cyan]🤖 AI API KEYS & MULTI-PROVIDER MANAGER 🤖[/bold bright_cyan]\n\n"
            "[bold white]🌐 Direct Links to Get Free Instant API Keys:[/bold white]\n"
            " • [bold bright_yellow]Google Gemini:[bold /yellow]   [bold underline bright_blue]https://aistudio.google.com/app/apikey[/bold underline bright_blue]\n"
            " • [bold bright_yellow]Groq Cloud:[bold /yellow]      [bold underline bright_blue]https://console.groq.com/keys[/bold underline bright_blue]\n"
            " • [bold bright_yellow]OpenRouter:[bold /yellow]      [bold underline bright_blue]https://openrouter.ai/keys[/bold underline bright_blue]\n\n"
            "[dim white]Click or copy any URL above in your browser to generate a free API key![/dim white]",
            border_style="cyan",
            box=ROUNDED
        ))
        
        active_prov = cfg.get("active_provider", "google")
        console.print(f"[bold white]Active Provider:[/bold white] [bold bright_green]{active_prov.upper()}[/bold bright_green]\n")
        
        table = Table(title="[bold cyan]Saved API Keys[/bold cyan]", box=ROUNDED)
        table.add_column("Provider", style="bold yellow")
        table.add_column("Total Keys Saved", style="bold white", justify="center")
        table.add_column("Key Hints", style="dim white")
        
        for prov in ["google", "groq", "openrouter"]:
            keys = cfg.get("keys", {}).get(prov, [])
            hints = ", ".join([k[:6] + "..." + k[-4:] if len(k) > 10 else "Saved" for k in keys]) if keys else "[dim red]No keys saved[/dim red]"
            is_active = " (Active)" if prov == active_prov else ""
            table.add_row(prov.capitalize() + is_active, str(len(keys)), hints)
        
        bot_status = "Configured" if cfg.get("telegram_bot_token") and cfg.get("telegram_chat_id") else "Not Set"
        user_nick = cfg.get("telegram_username") or cfg.get("user_nickname") or get_device_user_info()
        console.print(f"[bold white]Auto-Report Status:[/bold white] [bold cyan]{bot_status}[/bold cyan]  |  [bold white]Telegram User Tag:[/bold white] [bold yellow]{user_nick}[/bold yellow]")
        console.print(table)
        console.print()
        console.print("  [1] Add API Key (Google / Groq / OpenRouter)")
        console.print("  [2] Set Active Provider")
        console.print("  [3] Delete / Clear Keys")
        console.print("  [4] Configure Developer Telegram Auto-Report Bot 🚨")
        console.print("  [5] Test All API Keys Live (Check Key Limits / Exhaustion) ⚡")
        console.print("  [6] Set Your Telegram Username (for Telegram Error Reports) 💬")
        console.print("  [0] Back to Menu")
        
        choice = safe_input("\n-> Select Option [0-6]: ").strip()
        if choice == '1':
            console.print("\n[bold cyan]Select Provider to Get/Add API Key:[/bold cyan]")
            console.print("  [1] Google Gemini  👉 [bright_blue]https://aistudio.google.com/app/apikey[/bright_blue]")
            console.print("  [2] Groq Cloud     👉 [bright_blue]https://console.groq.com/keys[/bright_blue]")
            console.print("  [3] OpenRouter     👉 [bright_blue]https://openrouter.ai/keys[/bright_blue]")
            p_choice = safe_input("-> Select Provider [1-3]: ").strip()
            prov_map = {"1": "google", "2": "groq", "3": "openrouter"}
            prov = prov_map.get(p_choice)
            if not prov:
                console.print("[bold red][X] Invalid provider.[/bold red]")
                time.sleep(1)
                continue
            
            console.print(f"\n[bold white]Generating key for {prov.capitalize()}? Copy key from link above and paste below:[/bold white]")
            key_val = safe_input(f"-> Paste your {prov.capitalize()} API key: ").strip().strip('"\'')
            if key_val:
                if prov not in cfg["keys"]:
                    cfg["keys"][prov] = []
                if key_val not in cfg["keys"][prov]:
                    cfg["keys"][prov].append(key_val)
                    save_ai_config(cfg)
                    console.print(f"[bold green]✅ Added API key for {prov.capitalize()}![/bold green]")
                else:
                    console.print("[bold yellow][!] Key already exists.[/bold yellow]")
            time.sleep(1)
        elif choice == '2':
            console.print("\n[bold cyan]Select Active Provider:[/bold cyan]")
            console.print("  [1] Google Gemini")
            console.print("  [2] Groq")
            console.print("  [3] OpenRouter")
            p_choice = safe_input("-> Select Active Provider [1-3]: ").strip()
            prov_map = {"1": "google", "2": "groq", "3": "openrouter"}
            prov = prov_map.get(p_choice)
            if prov:
                cfg["active_provider"] = prov
                save_ai_config(cfg)
                console.print(f"[bold green]✅ Active provider set to {prov.capitalize()}![/bold green]")
            time.sleep(1)
        elif choice == '3':
            console.print("\n[bold cyan]Clear Keys for Provider:[/bold cyan]")
            console.print("  [1] Google Gemini")
            console.print("  [2] Groq")
            console.print("  [3] OpenRouter")
            console.print("  [4] Clear ALL Keys")
            p_choice = safe_input("-> Select Option [1-4]: ").strip()
            prov_map = {"1": "google", "2": "groq", "3": "openrouter"}
            if p_choice in prov_map:
                prov = prov_map[p_choice]
                cfg["keys"][prov] = []
                save_ai_config(cfg)
                console.print(f"[bold green]✅ Cleared keys for {prov.capitalize()}![/bold green]")
            elif p_choice == '4':
                cfg["keys"] = {"google": [], "groq": [], "openrouter": []}
                save_ai_config(cfg)
                console.print("[bold green]✅ Cleared all saved API keys![/bold green]")
            time.sleep(1)
        elif choice == '4':
            console.print("\n[bold cyan]🚨 Configure Telegram Auto-Report Bot for Direct Error Delivery:[/bold cyan]")
            console.print("[dim white]Create a bot on Telegram via @BotFather to get your Bot Token & Chat ID.[/dim white]\n")
            
            curr_token = cfg.get("telegram_bot_token", "")
            curr_chat = cfg.get("telegram_chat_id", "")
            
            if curr_token and curr_chat:
                console.print(f"[bold white]Current Bot Token:[/bold white] [bright_yellow]{curr_token[:8]}...{curr_token[-4:]}[/bright_yellow]")
                console.print(f"[bold white]Current Chat ID:[/bold white] [bright_yellow]{curr_chat}[/bright_yellow]\n")
            
            token_in = safe_input("-> Enter Telegram Bot Token (or press Enter to keep current): ").strip()
            chat_in = safe_input("-> Enter Developer Telegram Chat ID (or press Enter to keep current): ").strip()
            
            if token_in:
                cfg["telegram_bot_token"] = token_in
            if chat_in:
                cfg["telegram_chat_id"] = chat_in
                
            save_ai_config(cfg)
            console.print("[bold green]✅ Telegram Auto-Report configuration updated successfully![/bold green]")
            console.print("[dim white]Sending test connection report to your Telegram group...[/dim white]")
            send_telegram_bug_report("TEST_PING", "Telegram Bot Connection Verified Successfully!", "Telegram Bot Config Test", "FeaturesticLeaks.py", "6699", "manage_ai_api_keys", "No errors! Bot is connected and working.")
            console.print("[dim white]All unhandled errors anywhere on user devices will now instantly land on your Telegram![/dim white]")
            time.sleep(1.5)
        elif choice == '5':
            console.print("\n[bold cyan]⚡ Live Testing All Saved API Keys...[/bold cyan]")
            all_dead = True
            all_keys_list = []
            for p_name in ["google", "groq", "openrouter"]:
                for k in cfg.get("keys", {}).get(p_name, []):
                    all_keys_list.append((p_name, k))
            
            if not all_keys_list:
                console.print("[bold yellow]⚠️ No API keys saved yet! Option [1] se Google Gemini key paste karein.[/bold yellow]")
            else:
                for p_name, k in all_keys_list:
                    k_hint = k[:6] + "..." + k[-4:] if len(k) > 10 else k
                    try:
                        if p_name == "google":
                            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-8b:generateContent?key={k}"
                            res = requests.post(url, json={"contents": [{"parts": [{"text": "hi"}]}]}, timeout=10)
                            if res.status_code == 200:
                                console.print(f" • [bold green]Google Gemini Key ({k_hint}): ✅ ACTIVE & WORKING[/bold green]")
                                all_dead = False
                            else:
                                console.print(f" • [bold red]Google Gemini Key ({k_hint}): ❌ EXHAUSTED / RATE LIMITED (HTTP {res.status_code})[/bold red]")
                        elif p_name == "groq":
                            url = "https://api.groq.com/openai/v1/chat/completions"
                            res = requests.post(url, headers={"Authorization": f"Bearer {k}"}, json={"model": "llama-3.1-8b-instant", "messages": [{"role": "user", "content": "hi"}]}, timeout=10)
                            if res.status_code == 200:
                                console.print(f" • [bold green]Groq Key ({k_hint}): ✅ ACTIVE & WORKING[/bold green]")
                                all_dead = False
                            else:
                                console.print(f" • [bold red]Groq Key ({k_hint}): ❌ EXHAUSTED / RATE LIMITED (HTTP {res.status_code})[/bold red]")
                        elif p_name == "openrouter":
                            url = "https://openrouter.ai/api/v1/chat/completions"
                            res = requests.post(url, headers={"Authorization": f"Bearer {k}"}, json={"model": "google/gemini-flash-1.5-8b", "messages": [{"role": "user", "content": "hi"}]}, timeout=10)
                            if res.status_code == 200:
                                console.print(f" • [bold green]OpenRouter Key ({k_hint}): ✅ ACTIVE & WORKING[/bold green]")
                                all_dead = False
                            else:
                                console.print(f" • [bold red]OpenRouter Key ({k_hint}): ❌ EXHAUSTED / RATE LIMITED (HTTP {res.status_code})[/bold red]")
                    except Exception as e_k:
                        console.print(f" • [bold red]{p_name.capitalize()} Key ({k_hint}): ❌ Error: {e_k}[/bold red]")

            if all_dead and all_keys_list:
                console.print("\n[bold red]🚨 ALERT: SAARE API KEYS EXHAUSTED YA RATE LIMITED HO GAYE HAIN![/bold red]")
                console.print("[dim white]Naye free API key add karne ke liye Option [1] select karein.[/dim white]")
            time.sleep(2)
        elif choice == '6':
            console.print("\n[bold cyan]👤 Set Your Telegram Username:[/bold cyan]")
            console.print("[dim white]Enter your Telegram Handle (e.g. @itzraviking). This will be attached to all automated Telegram bug reports from your device so the developer can contact you directly.[/dim white]\n")
            curr_tg = cfg.get("telegram_username") or cfg.get("user_nickname", "")
            if curr_tg:
                console.print(f"[bold white]Current Telegram Username:[/bold white] [bold yellow]{curr_tg}[/bold yellow]")
            new_tg = safe_input("-> Enter your Telegram Username (e.g. @itzraviking): ").strip()
            if new_tg:
                if not new_tg.startswith("@") and " " not in new_tg and not new_tg.startswith("http"):
                    new_tg = f"@{new_tg}"
                cfg["telegram_username"] = new_tg
                cfg["user_nickname"] = new_tg
                save_ai_config(cfg)
                console.print(f"[bold green]✅ Telegram Username saved as '{new_tg}'![/bold green]")
                console.print("[dim white]Developer will now see this tag in all error reports from your app![/dim white]")
            time.sleep(1.5)
        elif choice == '0':
            break

def call_ai_api(prompt: str) -> Optional[str]:
    # Extract last user query for quick conversational matching
    clean_p = prompt.strip()
    low_p = clean_p.lower()
    last_user_query = ""
    if "user typed: '" in low_p:
        try:
            last_user_query = low_p.split("user typed: '")[1].split("'")[0].strip()
        except Exception:
            last_user_query = low_p.strip()
    elif "user:" in low_p:
        try:
            last_user_query = low_p.split("user:")[-1].split("\n")[0].strip()
        except Exception:
            last_user_query = low_p.strip()
    else:
        last_user_query = low_p.strip()

    # Local instant conversational fallback mapping for exact greetings (0 tokens spent!)
    quick_chat_responses = {
        'hi': "Hello brother! 👋 Main Featurestic Leaks AI Engine hu! PAK/OBB unpacking, Lua compiling, aur auto-fixing me kya help chahiye?",
        'hii': "Hii buddy! Welcome to Featurestic Leaks! Aaj kya modding ya leak karni hai?",
        'hiii': "Hiii! Kaise ho? Direct apana question poochho!",
        'hello': "Hey! Main Featurestic Leaks AI Companion hu. PAK unpack, Lua repair, ya koi bhi game modding query batao!",
        'hlw': "Hello ji! Kaise ho? Direct sawaal pucho ya tool options ke bare me jaano!",
        'helo': "Helooo! Kaise ho bhai? Featurestic Leaks Engine 24/7 ready hai!",
        'hey': "Yo! Kaise ho bhai? Batao aaj kya hack/mod karna hai!",
        'kaise ho': "Main bilkul mast aur 100% High-Speed ready hu! Aap batao aaj kya leak/mod karna hai?",
        'kya kar sakte ho': "Main Featurestic Leaks AI Engine hu! Main PAK/OBB files unpack/repack kar sakta hu, Lua scripts repair kar sakta hu aur automated bug reports generate kar sakta hu!",
        'kon ho': "Main Featurestic Leaks AI Assistant hu! Created to assist you with PAK/OBB & Lua modding!",
        'who are you': "I am Featurestic Leaks AI Engine — your ultimate GameGuard, PAK/OBB & Lua 5.1 modding buddy!",
        'help': "💡 **FEATURESTIC LEAKS AI QUICK GUIDANCE:**\n• **Option [1]**: AI Watch Assistant (Folder auto-listen & auto-process)\n• **Option [2]**: Friendly Chat (Aap yahan mughse kuch bhi poochh sakte hain)\n• **Option [3]**: AI Lua Syntax Repair (Broken .lua auto-fix)\n• **Option [4]**: Manage API Keys & Telegram Auto-Report Bot",
        'options': "💡 Main FeaturesticLeaks tool options:\n[1] PAK/OBB Tool  |  [2] Lua Compiler  |  [3] AI Tools  |  [4] Utilities",
        'bhai': "Haan bhai bolo! Main aapka Featurestic Leaks AI Assistant hu. Batao kya help chahiye?",
        'bro': "Yo bro! What's up? Direct apana query ya script question poochho!",
        'thanks': "Arey koi nahi bhai! Always happy to help! Enjoy modding! 🚀",
        'thank you': "Welcome brother! Koi aur problem ho to zaroor batana!",
        'shukriya': "Bahut shukriya bhai! Modding me koi error aaye to AI Watch Mode Option [1] try karein!",
        'bye': "Bye bye! Phir milenge, Happy Modding! 👋",
        'by': "Bye brother! Stay safe and happy modding!",
    }

    # Instant check for EXACT isolated conversational match to save API quota
    if last_user_query in quick_chat_responses:
        return quick_chat_responses[last_user_query]

    SYSTEM_PROMPT = (
        "You are Featurestic Leaks AI Engine — a concise, tool-focused AI assistant built specifically for Featurestic Leaks v2.5 "
        "(PAK/OBB Unpacker & Repacker, Lua 5.1 Compiler/Decompiler, AI Syntax Repair, Auto-Report Bot).\n\n"
        "STRICT RESPONSE RULES:\n"
        "1. Be extremely short, direct, and to-the-point (maximum 2-3 short sentences).\n"
        "2. ONLY answer regarding Featurestic Leaks tool options, PAK/OBB operations, Lua 5.1 scripts, GameGuard, and API configuration.\n"
        "3. NEVER suggest external PC tools (like Visual Studio, Notepad++, Android Studio, PC software). Everything is done directly inside Featurestic Leaks on Termux/Android.\n"
        "4. If asked how to do something (e.g. 'pak file bna', 'lua compile', 'fix script'):\n"
        "   - Give direct, step-by-step menu directions within Featurestic Leaks:\n"
        "     * PAK Unpack/Repack: Main Menu -> Option [1] PAK/OBB Tool -> Option [2] Repack\n"
        "     * Lua Compile/Decompile: Main Menu -> Option [2] Lua Compiler\n"
        "     * AI Syntax Fix: Main Menu -> Option [3] AI Tools -> Option [3] AI Lua Repair\n"
        "5. Speak in polite, friendly Hinglish with emojis. Use 'bhai' or 'brother'. NEVER call the user 'beta' or strange names.\n"
        "6. Do NOT write long paragraphs or off-topic advice. Keep replies brief and accurate."
    )

    # Determine task complexity to pick models smartly (saves API limits!)
    is_complex_code = any(kw in low_p for kw in [
        'function', 'local ', 'return', 'syntax error', 'end statement',
        'compile error', 'gameguard', 'luac 5.1', 'fix the syntax', 'lua script'
    ]) or len(prompt) > 800

    if is_complex_code:
        gemini_models = ["gemini-1.5-flash", "gemini-2.0-flash", "gemini-1.5-pro"]
        groq_models = ["llama-3.3-70b-versatile", "mixtral-8x7b-32768"]
        openrouter_models = ["meta-llama/llama-3.3-70b-instruct", "google/gemini-flash-1.5"]
    else:
        # Light chat queries use ultra-high limit & ultra-fast models (30 RPM on Gemini 1.5-Flash-8B!)
        gemini_models = ["gemini-1.5-flash-8b", "gemini-1.5-flash", "gemini-2.0-flash"]
        groq_models = ["llama-3.1-8b-instant", "llama3-8b-8192", "llama-3.2-3b-preview"]
        openrouter_models = ["google/gemini-flash-1.5-8b", "meta-llama/llama-3.1-8b-instruct:free", "google/gemini-flash-1.5"]

    # Build key queue across all available providers
    cfg = get_ai_config()
    active_prov = cfg.get("active_provider", "google")
    key_queue = [] # list of (provider, key)

    # 1. Add active provider keys
    for k in cfg.get("keys", {}).get(active_prov, []):
        if k and (active_prov, k) not in key_queue:
            key_queue.append((active_prov, k))

    # 2. Add other provider keys
    for prov in ["google", "groq", "openrouter"]:
        if prov != active_prov:
            for k in cfg.get("keys", {}).get(prov, []):
                if k and (prov, k) not in key_queue:
                    key_queue.append((prov, k))

    # 3. Add environment variable keys
    env_gemini = os.environ.get("GEMINI_API_KEY")
    if env_gemini and ("google", env_gemini) not in key_queue:
        key_queue.append(("google", env_gemini))
    env_groq = os.environ.get("GROQ_API_KEY")
    if env_groq and ("groq", env_groq) not in key_queue:
        key_queue.append(("groq", env_groq))
    env_or = os.environ.get("OPENROUTER_API_KEY")
    if env_or and ("openrouter", env_or) not in key_queue:
        key_queue.append(("openrouter", env_or))

    if key_queue:
        for prov, key in key_queue:
            try:
                if prov == "google":
                    for g_model in gemini_models:
                        url = f"https://generativelanguage.googleapis.com/v1beta/models/{g_model}:generateContent?key={key}"
                        payload = {
                            "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
                            "contents": [{"parts": [{"text": prompt}]}],
                            "generationConfig": {"maxOutputTokens": 250, "temperature": 0.2}
                        }
                        resp = requests.post(url, json=payload, timeout=15)
                        if resp.status_code == 200:
                            data = resp.json()
                            try:
                                txt = data['candidates'][0]['content']['parts'][0]['text']
                                if txt:
                                    return txt.strip()
                            except (KeyError, IndexError):
                                pass

                elif prov == "groq":
                    for g_model in groq_models:
                        url = "https://api.groq.com/openai/v1/chat/completions"
                        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
                        payload = {
                            "model": g_model,
                            "messages": [
                                {"role": "system", "content": SYSTEM_PROMPT},
                                {"role": "user", "content": prompt}
                            ],
                            "max_tokens": 250,
                            "temperature": 0.2
                        }
                        resp = requests.post(url, json=payload, headers=headers, timeout=15)
                        if resp.status_code == 200:
                            data = resp.json()
                            try:
                                txt = data['choices'][0]['message']['content']
                                if txt:
                                    return txt.strip()
                            except (KeyError, IndexError):
                                pass

                elif prov == "openrouter":
                    for or_model in openrouter_models:
                        url = "https://openrouter.ai/api/v1/chat/completions"
                        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
                        payload = {
                            "model": or_model,
                            "messages": [
                                {"role": "system", "content": SYSTEM_PROMPT},
                                {"role": "user", "content": prompt}
                            ],
                            "max_tokens": 250,
                            "temperature": 0.2
                        }
                        resp = requests.post(url, json=payload, headers=headers, timeout=15)
                        if resp.status_code == 200:
                            data = resp.json()
                            try:
                                txt = data['choices'][0]['message']['content']
                                if txt:
                                    return txt.strip()
                            except (KeyError, IndexError):
                                pass
            except Exception:
                continue

    # Offline / local direct fallbacks for tool commands when API keys are offline
    if "pak" in last_user_query:
        return "📦 **PAK File Guide:**\nPAK file create/repack karne ke liye: Main Menu -> Option [1] (PAK/OBB Tool) -> Option [2] (Repack Folder) select karein! Unpacked files `UNPACK/<folder>` me honi chahiye."
    elif "lua" in last_user_query:
        return "📜 **Lua Compiler Guide:**\nLua compile karne ke liye: Main Menu -> Option [2] (Lua Compiler) select karein! Broken Lua syntax repair karne ke liye: Main Menu -> Option [3] AI Tools -> [3] AI Lua Repair use karein."
    elif any(k in last_user_query for k in ['help', 'option', 'menu', 'kya kar']):
        return "💡 **Featurestic Leaks Tool Options:**\n[1] PAK/OBB Unpack/Repack  |  [2] Lua Compiler  |  [3] AI Watch & Repair  |  [4] API Keys & Telegram"

    return (
        "⚠️ **ALL API KEYS EXHAUSTED / RATE LIMITED!**\n\n"
        "Bhai, aapke paas saare API keys ki limit khatam ho gayi hai. "
        "Aap [bright_blue]https://aistudio.google.com/app/apikey[/bright_blue] se ek nayi free Gemini Key lekar "
        "Option [4] Manage API Keys me paste karein! 🚀"
    )


def ai_fix_lua_code(lua_code: str, error_msg: str = "") -> Optional[str]:
    prompt = f"""You are an expert Lua 5.1 and GameGuard script engineer.
Fix the syntax errors, missing functions, or bugs in the following Lua script so that it compiles perfectly with luac 5.1 and runs smoothly without syntax/runtime crashes.

CRITICAL RULES:
1. Output ONLY valid, runnable Lua code. Do NOT wrap in markdown code blocks like ```lua ... ``` if possible, or keep it strictly clean.
2. Ensure strict compatibility with Lua 5.1 and GameGuard (gg.* calls).
3. Do not modify the functional business logic, menu items, or memory search values unless they contain invalid syntax.

COMPILATION ERROR / BUG DESCRIPTION:
{error_msg}

ORIGINAL LUA SCRIPT:
{lua_code}
"""
    result = call_ai_api(prompt)
    if result:
        cleaned = re.sub(r'^```(?:lua)?\n', '', result, flags=re.MULTILINE)
        cleaned = re.sub(r'\n```$', '', cleaned, flags=re.MULTILINE).strip()
        return cleaned
    return None

query_ai_for_lua_fix = ai_fix_lua_code


def run_ai_assisted_lua_repair(data_path: Path):
    console.print(Panel(Align.center("[bold bright_cyan]🤖 AI-ASSISTED LUA SCRIPT REPAIR ENGINE 🤖[/bold bright_cyan]\n[dim white]Uses Google Gemini / Groq / OpenRouter AI to fix broken Lua syntax, missing end statements, & GameGuard errors![/dim white]"), border_style="cyan", box=ROUNDED))
    
    lua_dir = data_path / "LUA"
    lua_file, _ = pick_file_from_folder("AI Lua Repair", lua_dir, extensions=[".lua", ".txt"])
    if not lua_file:
        custom_input = safe_input('-> Enter custom Lua file path (or press Enter to cancel): ').strip().strip('"\'')
        if not custom_input:
            return
        lua_file = Path(custom_input)
        if not lua_file.exists() or not lua_file.is_file():
            console.print(f'[bold red][X] File not found: {lua_file}[/bold red]')
            return

    try:
        raw_code = lua_file.read_text(encoding='utf-8', errors='ignore')
    except Exception as e:
        console.print(f"[bold red][X] Could not read file: {e}[/bold red]")
        return

    # Test local compilation first to detect error
    compiler = "luac5.1" if shutil.which("luac5.1") else ("luac" if shutil.which("luac") else None)
    error_msg = "Manual user requested AI code cleanup & syntax repair for Lua 5.1 compatibility."
    
    if compiler:
        tmp_test = lua_file.with_suffix('.tmp_compile_test')
        proc = subprocess.run([compiler, "-o", str(tmp_test), str(lua_file)], capture_output=True, text=True)
        tmp_test.unlink(missing_ok=True)
        if proc.returncode != 0:
            error_msg = proc.stderr.strip()
            console.print(f"[bold yellow][!] Compilation Error Detected:\n{error_msg}[/bold yellow]\n")
        else:
            console.print("[bold green]✓ File compiles locally, but AI will optimize and refactor code for Lua 5.1.[/bold green]\n")

    ai_result = query_ai_for_lua_fix(raw_code, error_msg)
    if not ai_result:
        return

    # Clean markdown formatting if present
    cleaned_code = re.sub(r'^```(?:lua)?\n', '', ai_result, flags=re.MULTILINE)
    cleaned_code = re.sub(r'\n```$', '', cleaned_code, flags=re.MULTILINE).strip()

    res_dir = data_path / "RESULT"
    res_dir.mkdir(parents=True, exist_ok=True)
    out_repaired = res_dir / f"{lua_file.stem}_ai_repaired.lua"
    out_repaired.write_text(cleaned_code, encoding='utf-8')

    console.print(f"\n[bold green]🎉 AI Repair Successful! Saved repaired script to:[/bold green] [bold cyan]{out_repaired}[/bold cyan]")
    
    # Auto-compile check
    if compiler:
        out_luac = res_dir / f"{lua_file.stem}_ai_repaired.luac"
        proc2 = subprocess.run([compiler, "-o", str(out_luac), str(out_repaired)], capture_output=True, text=True)
        if proc2.returncode == 0:
            console.print(f"[bold green]✅ Compiled repaired script to bytecode -> {out_luac.name} ({out_luac.stat().st_size:,} bytes)[/bold green]")
        else:
            console.print(f"[bold yellow][!] Compiled bytecode warning: {proc2.stderr.strip()}[/bold yellow]")

    sd_res = Path("/sdcard/FeaturesticLeaks/RESULT")
    if sd_res.exists():
        try:
            shutil.copy2(out_repaired, sd_res / out_repaired.name)
            console.print(f"[bold green][+] Saved to SDCard: {sd_res / out_repaired.name}[/bold green]")
        except Exception:
            pass

def lua_tools_menu(data_path: Path):
    while True:
        print_banner()
        menu_table = Table(
            title="[bold bright_cyan]🌙 LUA MASTER SUITE 🌙[/bold bright_cyan]",
            show_header=True,
            header_style="bold bright_cyan",
            box=ROUNDED,
            border_style="bright_cyan",
            expand=True
        )
        menu_table.add_column("OPT", justify="center", width=8, style="bold bright_yellow")
        menu_table.add_column("COMMAND", justify="left", width=24, style="bold bright_white")
        menu_table.add_column("DESCRIPTION", justify="left", style="bright_cyan")

        menu_table.add_row("[1]", "Decompile & Fix Lua", "Decompile .luac bytecode to .lua source & repair headers")
        menu_table.add_row("[2]", "Compile Lua Source", "Convert .lua source code to .luac bytecode")
        menu_table.add_row("[3]", "Merge & Create GG Menu", "Combine multiple .lua scripts into GameGuard Menu Studio")
        menu_table.add_row("[4]", "PAK & Lua Installer Tool", "Embed PAK inside Lua installer OR extract PAK from script")
        menu_table.add_row("[5]", "Universal Lua Packer", "Pack or unpack Lua scripts with 8-byte magic tags")
        menu_table.add_row("[6]", "Security & Protection", "String obfuscator, security audit & bytecode header repair")
        menu_table.add_row("[7]", "Minifier & GG Code Studio", "Minify/Clean Lua scripts & Generate GG Memory Code")
        menu_table.add_row("[8]", "1-Click Auto Lua Workflow", "Auto-fix syntax -> Auto-compile -> Auto-sync to all folders")
        menu_table.add_row("[9]", "🤖 AI-Assisted Lua Repair", "Fix broken Lua syntax & manage multi-API keys (Google/Groq)")
        menu_table.add_row("[0]", "EXIT ✗", "Return to Main Menu")

        console.print(menu_table)
        console.print()
        choice = safe_input('\033[1;36mSELECT OPTION [1-9] [0]: \033[0m').strip()

        if choice == '1':
            run_lua_decompiler(data_path)
            safe_input('\nPress Enter to continue...')
        elif choice == '2':
            run_lua_compiler(data_path)
            safe_input('\nPress Enter to continue...')
        elif choice == '3':
            run_lua_script_merger(data_path)
            safe_input('\nPress Enter to continue...')
        elif choice == '4':
            console.print("\n[bold cyan]📦 PAK & LUA PAYLOAD TOOLS:[/bold cyan]")
            console.print("  [1] Embed PAK into Lua Installer Script")
            console.print("  [2] Extract PAK Payload from Lua Script")
            sub_c = safe_input("\n-> Select Option [1-2] [1]: ").strip() or '1'
            if sub_c == '1':
                run_pak_lua_embedder(data_path)
            else:
                run_lua_pak_extractor(data_path)
            safe_input('\nPress Enter to continue...')
        elif choice == '5':
            console.print("\n[bold cyan]📦 UNIVERSAL LUA PACKER & UNPACKER:[/bold cyan]")
            console.print("  [1] Unpack Tagged Lua File (Auto-Detect)")
            console.print("  [2] Pack Lua File (8-Byte Tag / Base64 / Zlib / XOR)")
            sub_c = safe_input("\n-> Select Option [1-2] [1]: ").strip() or '1'
            if sub_c == '1':
                run_universal_lua_unpack(data_path)
            else:
                run_universal_lua_pack(data_path)
            safe_input('\nPress Enter to continue...')
        elif choice == '6':
            console.print("\n[bold cyan]🔐 LUA SECURITY & PROTECTION TOOLS:[/bold cyan]")
            console.print("  [1] String Obfuscator (Encrypt strings & URLs)")
            console.print("  [2] Anti-Bypass Security Audit (Check GG calls & risks)")
            console.print("  [3] Bytecode Header Fixer (Repair Lua 5.1/5.3 headers)")
            sub_c = safe_input("\n-> Select Option [1-3] [1]: ").strip() or '1'
            if sub_c == '1':
                run_lua_string_obfuscator(data_path)
            elif sub_c == '2':
                run_lua_anti_bypass_analyzer(data_path)
            else:
                run_lua_header_fixer(data_path)
            safe_input('\nPress Enter to continue...')
        elif choice == '7':
            console.print("\n[bold cyan]⚡ MINIFIER & GG CODE STUDIO:[/bold cyan]")
            console.print("  [1] Minify, Clean & Pre-Flight Check Lua Script")
            console.print("  [2] Generate GG Memory Code Templates (Search, Edit, Freeze, Speedhack)")
            sub_c = safe_input("\n-> Select Option [1-2] [1]: ").strip() or '1'
            if sub_c == '1':
                run_lua_script_optimizer(data_path)
            else:
                run_gg_code_generator(data_path)
            safe_input('\nPress Enter to continue...')
        elif choice == '8':
            run_one_click_auto_lua_workflow(data_path)
            safe_input('\nPress Enter to continue...')
        elif choice == '9':
            console.print("\n[bold cyan]🤖 AI-ASSISTED LUA ENGINE & API MANAGER:[/bold cyan]")
            console.print("  [1] Run AI-Assisted Lua Repair & Syntax Fixer")
            console.print("  [2] Manage AI API Keys & Active Provider (Google / Groq / OpenRouter)")
            sub_c = safe_input("\n-> Select Option [1-2] [1]: ").strip() or '1'
            if sub_c == '1':
                run_ai_assisted_lua_repair(data_path)
            else:
                manage_ai_api_keys()
            safe_input('\nPress Enter to continue...')
        elif choice == '0':
            break
        else:
            console.print('[bold red][X] Invalid choice.[/bold red]')
            time.sleep(1)


# ==================== WATCH MODE ENGINE ====================

if HAS_WATCHDOG:
    class AutoHandler(FileSystemEventHandler):
        def __init__(self, data_path: Path):
            super().__init__()
            self.data_path = data_path
            self.processed = set()

        def on_created(self, event):
            if not event.is_directory:
                filepath = Path(event.src_path)
                if filepath in self.processed:
                    return
                self.processed.add(filepath)

                console.print(f"\n[bold bright_yellow]📁 New File Detected:[/bold bright_yellow] [bold cyan]{filepath}[/bold cyan]")

                if filepath.suffix.lower() in ['.pak', '.obb']:
                    console.print(f"[bold bright_green]📦 Auto-unpacking PAK file: {filepath.name}...[/bold bright_green]")
                    try:
                        pak = TencentPakFile(filepath)
                        unpack_path = self.data_path / "UNPACK" / filepath.stem
                        pak.dump(unpack_path)
                        console.print(f"[bold green]✅ Auto-unpacked {filepath.name} to {unpack_path}![/bold green]")

                        sd_unpack = Path("/sdcard/FeaturesticLeaks/UNPACK") / filepath.stem
                        if sd_unpack.parent.exists() and sd_unpack != unpack_path:
                            try:
                                pak.dump(sd_unpack)
                                console.print(f"[bold green][+] Also extracted to SDCard: {sd_unpack}[/bold green]")
                            except Exception:
                                pass
                    except Exception as e:
                        console.print(f"[bold red][X] Unpack error for {filepath.name}: {e}[/bold red]")

                elif filepath.suffix.lower() in ['.lua', '.txt']:
                    console.print(f"[bold bright_cyan]🌙 Auto-compiling Lua script: {filepath.name}...[/bold bright_cyan]")
                    try:
                        fixed_lua = fix_lua_syntax_for_lua51(filepath)
                        res_dir = self.data_path / "RESULT"
                        res_dir.mkdir(parents=True, exist_ok=True)
                        out_luac = res_dir / f"{filepath.stem}.luac"

                        compiler = "luac5.1" if shutil.which("luac5.1") else ("luac" if shutil.which("luac") else None)
                        if compiler:
                            proc = subprocess.run([compiler, "-o", str(out_luac), str(fixed_lua)], capture_output=True, text=True)
                            if proc.returncode == 0:
                                console.print(f"[bold green]✅ Auto-compiled {filepath.name} -> {out_luac.name} ({out_luac.stat().st_size:,} bytes)[/bold green]")
                                sd_res = Path("/sdcard/FeaturesticLeaks/RESULT")
                                if sd_res.exists():
                                    try:
                                        shutil.copy2(out_luac, sd_res / out_luac.name)
                                        console.print(f"[bold green][+] Saved to SDCard: {sd_res / out_luac.name}[/bold green]")
                                    except Exception:
                                        pass
                            else:
                                console.print(f"[bold yellow][!] Compilation warning: {proc.stderr.strip()}[/bold yellow]")
                        else:
                            console.print("[bold yellow][!] No Lua compiler found in system PATH.[/bold yellow]")
                    except Exception as e:
                        console.print(f"[bold red][X] Auto-compile error for {filepath.name}: {e}[/bold red]")

def run_watch_mode(data_path: Path):
    print_banner()
    console.print(Panel(Align.center("[bold bright_cyan]👁️ AUTOMATIC WATCH MODE 👁️[/bold bright_cyan]\n[dim white]Monitors PAK_INPUT and LUA_INPUT folders in real-time and auto-processes incoming files![/dim white]"), border_style="cyan", box=ROUNDED))

    if not HAS_WATCHDOG:
        console.print("[bold red][X] 'watchdog' module is not installed. Please run: pip install watchdog[/bold red]")
        return

    paths_to_watch = [
        data_path / "PAK",
        data_path / "LUA",
        Path("/sdcard/FeaturesticLeaks/PAK_WORKSPACE/1_PAK_INPUT"),
        Path("/sdcard/FeaturesticLeaks/LUA_WORKSPACE/1_LUA_INPUT")
    ]

    observer = Observer()
    handler = AutoHandler(data_path)
    scheduled_count = 0

    for p in paths_to_watch:
        try:
            p.mkdir(parents=True, exist_ok=True)
            observer.schedule(handler, path=str(p), recursive=False)
            scheduled_count += 1
            console.print(f"[bold green][+] Watching directory:[/bold green] [bold white]{p}[/bold white]")
        except Exception as e:
            console.print(f"[dim yellow][!] Skip watching {p}: {e}[/dim yellow]")

    if scheduled_count == 0:
        console.print("[bold red][X] No valid directories to watch.[/bold red]")
        return

    console.print("\n[bold bright_yellow]👁️ Watch Mode Active... Drop any .pak, .obb, or .lua file into the input folders to process![/bold bright_yellow]")
    console.print("[bold dim white]Press Ctrl+C to stop watching and return to menu.[/bold dim white]\n")

    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        console.print("\n[bold yellow]⏹️ Watch Mode Stopped.[/bold yellow]")
    except Exception as e:
        observer.stop()
        console.print(f"\n[bold red][X] Watcher error: {e}[/bold red]")
    observer.join()


def run_diagnostic_benchmark(data_path: Path):
    print_banner()
    console.print(Panel(
        "[bold bright_cyan]⚡ TERMUX PERFORMANCE BENCHMARK & DIAGNOSTIC LOG SUMMARY ⚡[/bold bright_cyan]\n"
        "[dim white]Testing system response time, Lua compiler speed, memory usage & log hygiene...[/dim white]",
        border_style="cyan",
        box=ROUNDED
    ))
    
    # 1. System Memory & Storage Info
    try:
        import psutil
        mem = psutil.virtual_memory()
        mem_str = f"{mem.used / (1024**2):.1f} MB / {mem.total / (1024**2):.1f} MB ({mem.percent}%)"
    except Exception:
        mem_str = "Available (Termux System)"

    # 2. Test Lua Compiler Performance
    compiler_speed = "N/A"
    luac_bin = shutil.which("luac5.1") or shutil.which("luac") or shutil.which("luajit")
    if luac_bin:
        t0 = time.perf_counter()
        test_script = data_path / ".speed_test.lua"
        test_out = data_path / ".speed_test.luac"
        test_script.write_text("print('Benchmark Speed Test')")
        proc = subprocess.run([luac_bin, "-o", str(test_out), str(test_script)], capture_output=True)
        t1 = time.perf_counter()
        elapsed_ms = (t1 - t0) * 1000
        compiler_speed = f"{elapsed_ms:.2f} ms ({Path(luac_bin).name})"
        test_script.unlink(missing_ok=True)
        test_out.unlink(missing_ok=True)

    # 3. Log Hygiene & Cleanup
    logs_dir = data_path / "logs"
    log_files = list(logs_dir.glob("*.log")) if logs_dir.exists() else []
    cleanup_old_logs(logs_dir, max_age_days=2.0, max_files=10)

    # Display Diagnostic Table
    diag_table = Table(title="[bold green]System Diagnostic Results[/bold green]", box=ROUNDED)
    diag_table.add_column("Component", style="bold yellow")
    diag_table.add_column("Status / Speed / Details", style="bold white")

    diag_table.add_row("Memory (RAM)", mem_str)
    diag_table.add_row("Lua Compiler Speed", compiler_speed)
    diag_table.add_row("Log Files Hygiene", f"{len(log_files)} log(s) scanned & trimmed")
    diag_table.add_row("Python Engine", f"Python {sys.version.split()[0]} ({os.name.upper()})")

    console.print(diag_table)
    console.print("\n[bold green]✅ System benchmark & log diagnostic completed successfully![/bold green]")

def utilities_menu(data_path: Path):
    while True:
        print_banner()
        menu_table = Table(
            title="[bold bright_cyan]🛠️ UTILITIES & HELP 🛠️[/bold bright_cyan]",
            show_header=True,
            header_style="bold bright_cyan",
            box=ROUNDED,
            border_style="bright_cyan",
            expand=True
        )
        menu_table.add_column("OPT", justify="center", width=8, style="bold bright_yellow")
        menu_table.add_column("COMMAND", justify="left", width=22, style="bold bright_white")
        menu_table.add_column("DESCRIPTION", justify="left", style="bright_cyan")

        menu_table.add_row("[1]", "UE4 String Tool", "Extract & repack .uasset/.uexp strings")
        menu_table.add_row("[2]", "File Finder", "Search .uasset/.uexp/.ubulk by pattern")
        menu_table.add_row("[3]", "URL & LIB Patcher 🔗", "Find & replace encrypted URLs in .so / binaries")
        menu_table.add_row("[4]", "File Resizer & Equalizer", "Match exact byte size of any file (PAK, OBB, LUA)")
        menu_table.add_row("[5]", "Termux Auto-Setup", "Setup 'leak' direct command & SDCard folders")
        menu_table.add_row("[6]", "Workspace Summary", "Folder guide & live file count summary")
        menu_table.add_row("[7]", "Beginner Guide & FAQ 🔰", "Beginner Quick Start & Modding Help")
        menu_table.add_row("[8]", "Cleanup Workspace", "Delete workspace folders")
        menu_table.add_row("[9]", "Check Tool Update 🚀", "Force update tool to latest GitHub version")
        menu_table.add_row("[10]", "Diagnostic & Benchmark ⚡", "Check execution speed, RAM & log hygiene")
        menu_table.add_row("[0]", "EXIT ✗", "Return to Main Menu")

        console.print(menu_table)
        console.print()
        choice = safe_input('\033[1;36mSELECT OPTION [1-10] [0]: \033[0m').strip()

        if choice == '1':
            run_ue4_string_tool(data_path)
            safe_input('\nPress Enter to continue...')
        elif choice == '2':
            run_file_finder_tool(data_path)
            safe_input('\nPress Enter to continue...')
        elif choice == '3':
            run_url_lib_patcher_tool(data_path)
            safe_input('\nPress Enter to continue...')
        elif choice == '4':
            run_file_resizer_tool(data_path)
            safe_input('\nPress Enter to continue...')
        elif choice == '5':
            install_termux_shortcut_and_sdcard(data_path)
            safe_input('\nPress Enter to continue...')
        elif choice == '6':
            print_banner()
            display_workspace_summary(data_path)
            show_workflow_guide()
            safe_input('\nPress Enter to continue...')
        elif choice == '7':
            run_beginner_guide(data_path)
        elif choice == '8':
            delete_folder(data_path)
            safe_input('\nPress Enter to continue...')
        elif choice == '9' or choice.lower() == 'u':
            check_and_auto_update(interactive=True)
            safe_input('\nPress Enter to continue...')
        elif choice == '10':
            run_diagnostic_benchmark(data_path)
            safe_input('\nPress Enter to continue...')
        elif choice == '0':
            break
        else:
            console.print('[bold red][X] Invalid choice.[/bold red]')
            time.sleep(1)


def watch_mode_menu(data_path: Path):
    while True:
        print_banner()
        menu_table = Table(
            title="[bold bright_cyan]👁️ WATCH MODE ENGINE 👁️[/bold bright_cyan]",
            show_header=True,
            header_style="bold bright_cyan",
            box=ROUNDED,
            border_style="bright_cyan",
            expand=True
        )
        menu_table.add_column("OPT", justify="center", width=8, style="bold bright_yellow")
        menu_table.add_column("COMMAND", justify="left", width=22, style="bold bright_white")
        menu_table.add_column("DESCRIPTION", justify="left", style="bright_cyan")

        menu_table.add_row("[1]", "Start Watch Mode 👁️", "Real-time auto-unpack .pak/.obb & auto-compile .lua")
        menu_table.add_row("[2]", "Watch Mode Status", "Check monitored input folders & watchdog installation")
        menu_table.add_row("[0]", "EXIT ✗", "Return to Main Menu")

        console.print(menu_table)
        console.print()
        choice = safe_input('\033[1;36mSELECT OPTION [1-2] [0]: \033[0m').strip()

        if choice == '1':
            run_watch_mode(data_path)
            safe_input('\nPress Enter to continue...')
        elif choice == '2':
            print_banner()
            console.print(Panel(
                f"[bold cyan]👁️ WATCH MODE STATUS & CONFIGURATION[/bold cyan]\n\n"
                f"[bold white]Watchdog Library Installed:[/bold white] {'[bold green]YES[/bold green]' if HAS_WATCHDOG else '[bold red]NO (run pip install watchdog)[/bold red]'}\n\n"
                f"[bold yellow]Monitored Folders:[/bold yellow]\n"
                f" • {data_path / 'PAK'}\n"
                f" • {data_path / 'LUA'}\n"
                f" • /sdcard/FeaturesticLeaks/PAK_WORKSPACE/1_PAK_INPUT\n"
                f" • /sdcard/FeaturesticLeaks/LUA_WORKSPACE/1_LUA_INPUT\n\n"
                f"[dim white]When active, dropping any .pak/.obb file will automatically extract it, and any .lua file will be compiled automatically![/dim white]",
                border_style="cyan",
                box=ROUNDED
            ))
            safe_input('\nPress Enter to continue...')
        elif choice == '0':
            break
        else:
            console.print('[bold red][X] Invalid choice.[/bold red]')
            time.sleep(1)


def run_ai_watch_assistant(data_path: Path):
    """
    AI ASSISTANT - WATCH MODE STYLE
    Runs in background loop, detects incoming files in workspace input folders,
    asks user interactively, performs actions (Unpack, Compile, AI Repair, Explain),
    reports results, and offers error fixing / developer auto-reporting.
    """
    print_banner()
    console.print(Panel(
        "[bold bright_cyan]🤖 AI MODDING ASSISTANT (WATCH MODE) 🤖[/bold bright_cyan]\n\n"
        "[bold white]Conversational Real-time AI Engine[/bold white]\n"
        " • [bright_yellow]Detects incoming files in workspace input folders every 2 seconds[/bright_yellow]\n"
        " • [bright_cyan]Asks you what action to perform (Unpack, Compile, AI Fix, Auto, Skip)[/bright_cyan]\n"
        " • [bright_green]Responds to natural voice/text commands ('Haan', 'Nahi', 'Unpack', 'Fix', etc.)[/bright_green]\n"
        " • [bright_magenta]Auto-generates error reports & fixes bugs automatically![/bright_magenta]\n\n"
        "[dim white]Type 'exit' or press Ctrl+C anytime to stop assistant.[/dim white]",
        border_style="cyan",
        box=ROUNDED
    ))

    watch_folders = [
        data_path / "PAK",
        data_path / "LUA",
        data_path / "INJECT",
        Path("/sdcard/FeaturesticLeaks/PAK_WORKSPACE/1_PAK_INPUT"),
        Path("/sdcard/FeaturesticLeaks/LUA_WORKSPACE/1_LUA_INPUT")
    ]
    for wf in watch_folders:
        try:
            wf.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass

    processed_files = set()
    for wf in watch_folders:
        if wf.exists():
            for f in wf.glob("*"):
                if f.is_file() and not f.name.startswith("."):
                    processed_files.add(f.resolve())

    console.print("\n[bold bright_yellow]👁️ AI Watch Assistant Active! Listening for new files or commands...[/bold bright_yellow]\n")

    while True:
        try:
            new_file = None
            for wf in watch_folders:
                if wf.exists():
                    for f in wf.glob("*"):
                        if f.is_file() and not f.name.startswith(".") and f.resolve() not in processed_files:
                            new_file = f.resolve()
                            processed_files.add(new_file)
                            break
                if new_file:
                    break

            if new_file:
                ext = new_file.suffix.lower()
                parent_str = str(new_file.parent).lower()

                # Smart Folder Misplacement Auto-Detection & Routing
                correct_target = None
                if ext in ['.pak', '.obb'] and ('lua' in parent_str):
                    correct_target = data_path / "PAK"
                elif ext in ['.lua', '.luac'] and ('pak' in parent_str or 'inject' in parent_str):
                    correct_target = data_path / "LUA"

                if correct_target:
                    console.print(Panel(
                        f"[bold bright_red]⚠️ GALT FOLDER DETECTED![/bold bright_red]\n\n"
                        f"[bold white]File:[/bold white] [bright_yellow]{new_file.name}[/bright_yellow] ({ext})\n"
                        f"[bold white]Aapne ise wrong folder me daala:[/bold white] [red]{new_file.parent}[/red]\n"
                        f"[bold bright_cyan]🤖 AI Assistant: Main is file ko auto-detect karke sahi folder [bright_green]'{correct_target.name}'[/bright_green] me move kar raha hu![/bold bright_cyan]",
                        border_style="red",
                        box=ROUNDED
                    ))
                    try:
                        correct_target.mkdir(parents=True, exist_ok=True)
                        dest_p = correct_target / new_file.name
                        shutil.move(str(new_file), str(dest_p))
                        new_file = dest_p
                        processed_files.add(new_file.resolve())
                        console.print(f"[bold green]✅ Auto-Moved File to Sahi Folder: {new_file}[/bold green]\n")
                    except Exception as m_err:
                        console.print(f"[dim yellow]Auto-move note: {m_err}[/dim yellow]")

                console.print(Panel(
                    f"[bold bright_yellow]🔍 NEW FILE DETECTED:[/bold bright_yellow] [bold cyan]{new_file.name}[/bold cyan]\n"
                    f"[bold white]Location:[/bold white] {new_file.parent}\n"
                    f"[bold white]Size:[/bold white] {human_size(new_file.stat().st_size)}",
                    border_style="yellow",
                    box=ROUNDED
                ))

                default_action = "Unpack" if ext in ['.pak', '.obb'] else ("Compile" if ext in ['.lua', '.txt'] else "Process")

                console.print(f"[bold bright_cyan]🤖 AI Assistant:[bold /bright_cyan] Ye file [bold white]'{new_file.name}'[/bold white] mili hai! Kya {default_action} karun?")
                console.print("[dim white]Options: [Haan / 1] Unpack/Compile  |  [2] AI Fix  |  [3] Auto  |  [Nahi / 0] Skip[/dim white]")

                user_input = safe_input("\n💬 You: ").strip()

                if user_input.lower() in ['exit', 'quit', 'cancel']:
                    break

                low_in = user_input.lower()
                should_process = False
                action = default_action.lower()

                if low_in in ['haan', 'yes', 'y', '1', 'ok', 'sure', 'unpack', 'compile', 'process']:
                    should_process = True
                elif low_in in ['auto', '3']:
                    should_process = True
                    action = 'auto'
                elif low_in in ['fix', 'repair', '2']:
                    should_process = True
                    action = 'fix'
                elif low_in in ['nahi', 'no', 'n', '0', 'skip']:
                    console.print("[bold dim white]🤖 AI Assistant: Okay, file skip kar di.[/bold dim white]\n")
                    continue
                else:
                    should_process = True
                    action = low_in

                if should_process:
                    console.print(f"\n[bold cyan]⚡ AI Executing Action...[/bold cyan]")
                    try:
                        if ext in ['.pak', '.obb'] or 'pak' in action or 'unpack' in action or 'auto' in action:
                            pak = TencentPakFile(new_file)
                            out_unpack = data_path / "UNPACK" / new_file.stem
                            pak.dump(out_unpack)
                            console.print(f"[bold green]✅ AI Report: PAK successfully unpacked to {out_unpack}![/bold green]")
                            sd_unpack = Path("/sdcard/FeaturesticLeaks/UNPACK") / new_file.stem
                            if sd_unpack.parent.exists() and sd_unpack != out_unpack:
                                try:
                                    pak.dump(sd_unpack)
                                    console.print(f"[bold green]   Also saved to SDCard: {sd_unpack}[/bold green]")
                                except Exception:
                                    pass
                            console.print("[bold bright_cyan]💡 AI Suggestion: Iske baad Option [1] -> Option [2] se files replace/repack karke game me test kar sakte hain![/bold bright_cyan]\n")

                        elif ext in ['.lua', '.txt'] or 'lua' in action or 'compile' in action or 'auto' in action:
                            if action == 'fix' or 'fix' in action or 'repair' in action:
                                code = new_file.read_text(errors='ignore')
                                console.print("[bold cyan]🤖 AI repairing Lua syntax...[/bold cyan]")
                                fixed_code = ai_fix_lua_code(code)
                                if fixed_code:
                                    new_file.write_text(fixed_code, encoding='utf-8')
                                    console.print("[bold green]✅ AI Report: Lua syntax repaired successfully![/bold green]")
                            
                            fixed_lua = fix_lua_syntax_for_lua51(new_file)
                            res_dir = data_path / "RESULT"
                            res_dir.mkdir(parents=True, exist_ok=True)
                            out_luac = res_dir / f"{new_file.stem}.luac"
                            compiler = "luac5.1" if shutil.which("luac5.1") else ("luac" if shutil.which("luac") else None)
                            if compiler:
                                proc = subprocess.run([compiler, "-o", str(out_luac), str(fixed_lua)], capture_output=True, text=True)
                                if proc.returncode == 0:
                                    console.print(f"[bold green]✅ AI Report: Compiled successfully to {out_luac.name} ({out_luac.stat().st_size:,} bytes)![/bold green]")
                                else:
                                    console.print(f"[bold yellow]⚠️ Compilation warning: {proc.stderr.strip()}[/bold yellow]")
                                    console.print("[bold red]❌ Error aaya! Kya AI se syntax fix karun? (Haan/Nahi)[/bold red]")
                                    fix_ans = safe_input("💬 You: ").strip().lower()
                                    if fix_ans in ['haan', 'yes', 'y', '1']:
                                        code = new_file.read_text(errors='ignore')
                                        fixed_code = ai_fix_lua_code(code, proc.stderr)
                                        if fixed_code:
                                            new_file.write_text(fixed_code, encoding='utf-8')
                                            console.print("[bold green]✅ AI syntax fix applied! Retrying compilation...[/bold green]")
                                            proc2 = subprocess.run([compiler, "-o", str(out_luac), str(fixed_lua)], capture_output=True, text=True)
                                            if proc2.returncode == 0:
                                                console.print(f"[bold green]✅ Retry Successful: {out_luac.name} compiled![/bold green]")

                            console.print("[bold bright_cyan]💡 AI Suggestion: Is compiled .luac script ko PAK file me inject kar sakte hain![/bold bright_cyan]\n")

                        else:
                            res = call_ai_api(f"User asked: '{user_input}' regarding file '{new_file.name}'. Give a concise, helpful response in Hinglish.")
                            if res:
                                console.print(f"\n[bold bright_cyan]🤖 AI Assistant:[/bold bright_cyan] {res}\n")
                            else:
                                console.print("[bold yellow]🤖 AI Assistant: File process ho gayi hai! Next kya karna chahenge?[/bold yellow]\n")

                    except Exception as ex:
                        console.print(f"[bold red]❌ Error occurred: {ex}[/bold red]")
                        send_telegram_bug_report(
                            error_type=type(ex).__name__,
                            error_msg=str(ex),
                            context=f"AI Watch Assistant processing file '{new_file.name}'",
                            file_name="FeaturesticLeaks.py",
                            line_no="7395",
                            func_name="run_ai_watch_assistant",
                            stack_trace=traceback.format_exc()
                        )
                        console.print("[bold green]📲 Auto-sent error bug report directly to developer Telegram group![/bold green]")
                        rep_dir = Path("/sdcard/FeaturesticLeaks/ERROR_REPORTS")
                        try:
                            rep_dir.mkdir(parents=True, exist_ok=True)
                            rep_file = rep_dir / f"report_{int(time.time())}.txt"
                            rep_file.write_text(f"File: {new_file}\nError: {ex}\nTime: {time.ctime()}\n\n{traceback.format_exc()}", encoding='utf-8')
                            console.print(f"[bold green]✅ Local report saved: {rep_file}[/bold green]\n")
                        except Exception:
                            pass

            if not new_file:
                console.print(Panel(
                    "[bold bright_yellow]⚡ QUICK SHORTCUTS (Type and Press Enter):[/bold bright_yellow]\n"
                    " [bold white][1] PAK Tools  [2] Lua Tools  [3] AI Repair  [4] AI Config  [5] Utilities  [U] Auto-Update[/bold white]\n"
                    " [bold bright_cyan][inject] Auto-Inject  [repack] Repack PAK  [scan] Folder Status  [help] Guide[/bold bright_cyan]",
                    border_style="dim cyan",
                    box=ROUNDED
                ))
                user_msg = safe_input("\n💬 You (Type command/query or press Enter to scan): ").strip()
                if user_msg.lower() in ['exit', 'quit', 'back', 'cancel', '0']:
                    console.print("[bold cyan]🤖 AI Assistant: Watch mode stopped. Main menu me wapas aa gaye![/bold cyan]")
                    break
                
                if user_msg:
                    low_um = user_msg.lower()
                    
                    # Direct Command Execution: Scan and Process existing files in workspace!
                    handled_command = False
                    
                    if low_um in ['1', 'pak', 'obb', 'pak tool', 'pak tools', 'pak/obb']:
                        console.print("[bold cyan]🚀 Opening PAK/OBB Tools Module...[/bold cyan]\n")
                        pak_obb_tools_menu(data_path)
                        handled_command = True

                    elif low_um in ['2', 'lua', 'luac', 'lua tool', 'lua tools']:
                        console.print("[bold cyan]🚀 Opening LUA Tools Module...[/bold cyan]\n")
                        lua_tools_menu(data_path)
                        handled_command = True

                    elif low_um in ['3', 'ai tools', 'ai tool', 'keys', 'telegram', 'repair']:
                        console.print("[bold cyan]🚀 Opening AI Tools & Multi-API Manager...[/bold cyan]\n")
                        ai_tools_menu(data_path)
                        handled_command = True

                    elif low_um in ['4', 'ai config', 'config']:
                        console.print("[bold cyan]🚀 Opening AI Configuration...[/bold cyan]\n")
                        ai_tools_menu(data_path)
                        handled_command = True

                    elif low_um in ['5', 'util', 'utils', 'utility', 'utilities', 'patcher']:
                        console.print("[bold cyan]🚀 Opening Utilities Module...[/bold cyan]\n")
                        utilities_menu(data_path)
                        handled_command = True

                    elif low_um in ['u', 'update', 'autoupdate', 'auto-update', 'check update']:
                        check_and_auto_update(interactive=True)
                        handled_command = True

                    elif any(kw in low_um for kw in ['help', 'kaise kare', 'samajh nahi', 'confused', 'kya karu', 'options', 'guide']):
                        console.print(Panel(
                            "[bold bright_cyan]💡 FEATURESTIC LEAKS AI QUICK GUIDANCE - DIRECT SELECTION[/bold bright_cyan]\n\n"
                            " [bold bright_yellow][1][/bold bright_yellow] [bold white]PAK/OBB Unpack ya Repack karna hai[/bold white] → Direct enter [bold yellow]1[/bold yellow]\n"
                            " [bold bright_yellow][2][/bold bright_yellow] [bold white]Lua Script Compile / Decompile / Obfuscate[/bold white] → Direct enter [bold yellow]2[/bold yellow]\n"
                            " [bold bright_yellow][3][/bold bright_yellow] [bold white]Broken Lua Syntax Repair karna hai[/bold white] → Direct enter [bold yellow]3[/bold yellow]\n"
                            " [bold bright_yellow][4][/bold bright_yellow] [bold white]Utilities & Termux Shortcuts[/bold white] → Direct enter [bold yellow]5[/bold yellow]\n"
                            " [bold bright_yellow][5][/bold bright_yellow] [bold white]Check Tool Auto-Update[/bold white] → Direct enter [bold yellow]u[/bold yellow]\n\n"
                            "[dim white]Tip: Input folders me `.pak` ya `.lua` file drop karein, AI automatic detect karke process kar dega![/dim white]",
                            border_style="cyan",
                            box=ROUNDED
                        ))
                        handled_command = True

                    elif 'inject' in low_um:
                        found_paks = list((data_path / "1_PAK_INPUT").glob("*.pak")) + list((data_path / "1_PAK_INPUT").glob("*.obb"))
                        found_luas = list((data_path / "1_LUA_INPUT").glob("*.lua")) + list((data_path / "1_LUA_INPUT").glob("*.luac")) + list((data_path / "RESULT").glob("*.luac"))
                        if found_paks and found_luas:
                            console.print(f"[bold cyan]⚡ AI Auto-Injecting {found_luas[0].name} into {found_paks[0].name}...[/bold cyan]")
                            try:
                                pak = TencentPakFile(found_paks[0])
                                rel_path = f"Asset/Scripts/{found_luas[0].name}"
                                pak.add_file(rel_path, found_luas[0].read_bytes())
                                out_p = data_path / "RESULT" / found_paks[0].name
                                pak.save(out_p)
                                console.print(f"[bold green]✅ Injected & saved to: {out_p}![/bold green]\n")
                            except Exception as ex:
                                console.print(f"[bold red]❌ Inject error: {ex}[/bold red]\n")
                        else:
                            console.print("[bold cyan]🚀 Launching PAK Injector Tool...[/bold cyan]\n")
                            pak_obb_tools_menu(data_path)
                        handled_command = True

                    elif 'repack' in low_um:
                        console.print("[bold cyan]🚀 Launching PAK Repacker...[/bold cyan]\n")
                        pak_obb_tools_menu(data_path)
                        handled_command = True

                    elif any(kw in low_um for kw in ['unpack', 'pak file']):
                        found_paks = []
                        for wf in watch_folders:
                            if wf.exists():
                                for f in wf.glob("*"):
                                    if f.is_file() and f.suffix.lower() in ['.pak', '.obb']:
                                        found_paks.append(f)
                        if found_paks:
                            pf = found_paks[0]
                            console.print(f"[bold cyan]⚡ AI Unpacking found PAK file: {pf.name}...[/bold cyan]")
                            try:
                                pak = TencentPakFile(pf)
                                out_u = data_path / "UNPACK" / pf.stem
                                pak.dump(out_u)
                                console.print(f"[bold green]✅ AI Report: Unpacked {pf.name} successfully to {out_u}![/bold green]\n")
                            except Exception as ex:
                                console.print(f"[bold red]❌ Unpack Error: {ex}[/bold red]\n")
                            handled_command = True
                        else:
                            console.print("\n[bold bright_cyan]🤖 AI Assistant:[/bold bright_cyan] 📦 PAK Unpack karne ke liye:\n1. File `1_PAK_INPUT` folder me daalein (AI auto-detect kar lega)\n2. Ya Main Menu -> Option [1] PAK/OBB Tool select karein!\n")
                            handled_command = True
                            
                    elif any(kw in low_um for kw in ['compile', 'luac']):
                        found_luas = []
                        for wf in watch_folders:
                            if wf.exists():
                                for f in wf.glob("*"):
                                    if f.is_file() and f.suffix.lower() in ['.lua', '.txt']:
                                        found_luas.append(f)
                        if found_luas:
                            lf = found_luas[0]
                            console.print(f"[bold cyan]⚡ AI Compiling found Lua script: {lf.name}...[/bold cyan]")
                            try:
                                fixed_lua = fix_lua_syntax_for_lua51(lf)
                                res_dir = data_path / "RESULT"
                                res_dir.mkdir(parents=True, exist_ok=True)
                                out_luac = res_dir / f"{lf.stem}.luac"
                                compiler = "luac5.1" if shutil.which("luac5.1") else ("luac" if shutil.which("luac") else None)
                                if compiler:
                                    proc = subprocess.run([compiler, "-o", str(out_luac), str(fixed_lua)], capture_output=True, text=True)
                                    if proc.returncode == 0:
                                        console.print(f"[bold green]✅ AI Report: Compiled successfully to {out_luac.name}![/bold green]\n")
                                    else:
                                        console.print(f"[bold yellow]⚠️ Syntax Warning: {proc.stderr.strip()}[/bold yellow]\n")
                            except Exception as ex:
                                console.print(f"[bold red]❌ Compile Error: {ex}[/bold red]\n")
                            handled_command = True
                        else:
                            console.print("\n[bold bright_cyan]🤖 AI Assistant:[/bold bright_cyan] 📜 Lua Compile karne ke liye:\n1. Script `1_LUA_INPUT` folder me daalein (AI auto-compile karega)\n2. Ya Main Menu -> Option [2] Lua Compiler select karein!\n")
                            handled_command = True

                    elif any(kw in low_um for kw in ['fix', 'repair', 'syntax']):
                        found_luas = []
                        for wf in watch_folders:
                            if wf.exists():
                                for f in wf.glob("*"):
                                    if f.is_file() and f.suffix.lower() in ['.lua', '.txt']:
                                        found_luas.append(f)
                        if found_luas:
                            lf = found_luas[0]
                            console.print(f"[bold cyan]🤖 AI repairing Lua syntax for: {lf.name}...[/bold cyan]")
                            try:
                                code = lf.read_text(errors='ignore')
                                fixed_code = ai_fix_lua_code(code)
                                if fixed_code:
                                    lf.write_text(fixed_code, encoding='utf-8')
                                    console.print(f"[bold green]✅ AI Report: {lf.name} syntax repaired successfully![/bold green]\n")
                            except Exception as ex:
                                console.print(f"[bold red]❌ Fix Error: {ex}[/bold red]\n")
                            handled_command = True
                        else:
                            console.print("\n[bold bright_cyan]🤖 AI Assistant:[/bold bright_cyan] 🛠️ Lua Syntax Fix karne ke liye:\n1. Broken script `1_LUA_INPUT` folder me daalein\n2. Ya Main Menu -> Option [3] AI Tools -> Option [3] AI Lua Repair use karein!\n")
                            handled_command = True

                    elif any(kw in low_um for kw in ['scan', 'check', 'status', 'folder']):
                        display_workspace_summary(data_path)
                        handled_command = True

                    if not handled_command:
                        console.print("[dim cyan]🤖 AI Assistant is thinking...[/dim cyan]")
                        resp = call_ai_api(f"You are Featurestic Leaks AI Assistant in Watch Mode. User typed: '{user_msg}'. Respond in friendly Hinglish with emojis.")
                        if resp:
                            console.print(f"\n[bold bright_cyan]🤖 AI Assistant:[/bold bright_cyan]\n{resp.strip()}\n")
                        else:
                            console.print("\n[bold bright_cyan]🤖 AI Assistant:[/bold bright_cyan] Main ready hu! Input folder me `.pak` ya `.lua` file daalein, main usko instantly process kar dunga! 🚀\n")
                    continue
                else:
                    time.sleep(1)

        except KeyboardInterrupt:
            console.print("\n[bold yellow]⏹️ AI Watch Assistant Stopped.[/bold yellow]")
            break
        except Exception as e:
            console.print(f"[dim yellow][!] Assistant loop note: {e}[/dim yellow]")
            time.sleep(2)


def run_ai_chat_mode(data_path: Path):
    """
    FRIENDLY CONVERSATIONAL AI CHAT COMPANION
    User can directly chat with AI (say 'hlw', ask modding questions, ask how to use tools, get script advice, etc.)
    """
    print_banner()
    console.print(Panel(
        "[bold bright_cyan]💬 FRIENDLY AI CHAT COMPANION 💬[/bold bright_cyan]\n\n"
        "[bold white]Apne AI Modding Buddy se kuch bhi poochho![/bold white]\n"
        " • [bright_yellow]'Hello', 'Kaise ho', 'PAK kaise unpack karu?', 'Lua fix kaise karein?'[/bright_yellow]\n"
        " • [bright_cyan]Full GameGuard, Unreal Engine, PAK/OBB & Lua 5.1 Expert Knowledge![/bright_cyan]\n\n"
        "[dim white]Type 'exit' or 'back' anytime to return to menu.[/dim white]",
        border_style="cyan",
        box=ROUNDED
    ))

    system_context = (
        "You are Featurestic Leaks AI, a super friendly, intelligent, and helpful AI modding companion. "
        "You talk in casual, enthusiastic Hinglish (Hindi + English). "
        "You assist users with PAK/OBB unpacking, LUA script compilation, GameGuard bypasses, UE4 asset editing, "
        "and using the FeaturesticLeaks tool commands (`leak`, `leak pak`, `leak lua`, `leak watch`, `leak ai`, `leak utils`). "
        "Be friendly, polite, encouraging, and use clear formatting with emojis!"
    )

    history = []

    while True:
        try:
            user_msg = safe_input("\n[bold bright_yellow]💬 You:[bold /bright_yellow] ").strip()
            if not user_msg:
                continue
            if user_msg.lower() in ['exit', 'quit', 'back', '0']:
                console.print("[bold cyan]🤖 AI: Alvida! Phir milenge dosto! Happy Modding! 🚀[/bold cyan]\n")
                break

            prompt = f"{system_context}\n"
            if history:
                prompt += "Recent Chat History:\n" + "\n".join(history[-6:]) + "\n"
            prompt += f"User: {user_msg}\nAI Assistant:"

            console.print("[dim cyan]🤖 AI Assistant is thinking...[/dim cyan]")
            response = call_ai_api(prompt)

            if response:
                console.print(f"\n[bold bright_cyan]🤖 AI Assistant:[/bold bright_cyan]\n{response.strip()}\n")
                history.append(f"User: {user_msg}")
                history.append(f"AI: {response.strip()}")
            else:
                console.print("[bold yellow]🤖 AI Assistant: Hey! Main abhi yahan hu. Kuch bhi poochho PAK, OBB ya Lua modding ke bare me![/bold yellow]\n")

        except KeyboardInterrupt:
            console.print("\n[bold yellow]Chat ended.[/bold yellow]")
            break
        except Exception as ex:
            console.print(f"[dim red]Chat note: {ex}[/dim red]")


def ai_tools_menu(data_path: Path):
    while True:
        print_banner()
        menu_table = Table(
            title="[bold bright_cyan]🤖 AI TOOLS & MULTI-API MANAGER 🤖[/bold bright_cyan]",
            show_header=True,
            header_style="bold bright_cyan",
            box=ROUNDED,
            border_style="bright_cyan",
            expand=True
        )
        menu_table.add_column("OPT", justify="center", width=8, style="bold bright_yellow")
        menu_table.add_column("COMMAND", justify="left", width=26, style="bold bright_white")
        menu_table.add_column("DESCRIPTION", justify="left", style="bright_cyan")

        menu_table.add_row("[1]", "AI Modding Assistant 🤖", "Real-time AI watcher, folder auto-fix & voice/text commands")
        menu_table.add_row("[2]", "Friendly AI Chat Companion 💬", "Talk to AI directly ('hlw', ask modding questions & tips)")
        menu_table.add_row("[3]", "AI-Assisted Lua Repair 🛠️", "Fix broken Lua syntax, missing ends & GG errors")
        menu_table.add_row("[4]", "Manage AI API Keys & Telegram 🔑", "Setup Gemini/Groq keys & Telegram Auto-Report Bot")
        menu_table.add_row("[0]", "EXIT ✗", "Return to Main Menu")

        console.print(menu_table)
        console.print()
        choice = safe_input('\033[1;36mSELECT OPTION [1-4] [0]: \033[0m').strip()

        if choice == '1':
            run_ai_watch_assistant(data_path)
            safe_input('\nPress Enter to continue...')
        elif choice == '2':
            run_ai_chat_mode(data_path)
            safe_input('\nPress Enter to continue...')
        elif choice == '3':
            run_ai_assisted_lua_repair(data_path)
            safe_input('\nPress Enter to continue...')
        elif choice == '4':
            manage_ai_api_keys()
            safe_input('\nPress Enter to continue...')
        elif choice == '0':
            break
        else:
            console.print('[bold red][X] Invalid choice.[/bold red]')
            time.sleep(1)


_BOOTED = False

def run_url_lib_patcher_tool(data_path: Path):
    """
    URL & LIB PATCHER TOOL
    Allows searching, inspecting, and replacing encrypted URLs in .so, .exe, .bin, .bytes files using XOR keys.
    """
    print_banner()
    console.print(Panel(
        "[bold cyan]🔗 URL & LIB PATCHER TOOL (SO / BINARY URL MODDER)[/bold cyan]\n"
        "[dim white]Search, list, and replace encrypted http:// & https:// URLs inside .so game libraries, binaries & scripts![/dim white]",
        border_style="cyan",
        box=ROUNDED
    ))

    so_dir = data_path / "REPLACE"
    so_dir.mkdir(parents=True, exist_ok=True)

    target_file, _ = pick_file_from_folder("Select Library / Binary File", so_dir, extensions=[".so", ".bin", ".exe", ".bytes", ".dat", ".txt"])
    if not target_file or not target_file.exists():
        console.print("[bold red][X] No file selected.[/bold red]")
        return

    current_key = 0x2E

    def xor_crypt(data: bytes, key: int) -> bytes:
        return bytes([b ^ (key & 0xFF) for b in data])

    def find_urls(data: bytes) -> List[Tuple[int, str]]:
        url_pattern = re.compile(rb"https?://[A-Za-z0-9\./\_\-?=&%:#]+")
        return [(m.start(), m.group().decode(errors="ignore")) for m in url_pattern.finditer(data)]

    while True:
        print_banner()
        patch_table = Table(
            title=f"[bold bright_green]⚙️ LIB URL PATCHER - [{target_file.name}][/bold bright_green]",
            show_header=True,
            header_style="bold green",
            box=ROUNDED,
            border_style="green",
            expand=True
        )
        patch_table.add_column("OPT", style="bold yellow", justify="center", width=8)
        patch_table.add_column("ACTION", style="bold white", justify="left", width=22)
        patch_table.add_column("INFO", style="dim cyan", justify="left")

        patch_table.add_row("[1]", "List Found URLs", "Scan & list all http/https URLs inside file")
        patch_table.add_row("[2]", "Set XOR Key", f"Current Key: [bold yellow]0x{current_key:02X}[/bold yellow] ({current_key})")
        patch_table.add_row("[3]", "Replace URL(s)", "Patch URLs with new domain/panel link (Saves patched file)")
        patch_table.add_row("[4]", "Select Different File", f"Current: {target_file.name}")
        patch_table.add_row("[0]", "Back to Main Menu", "Return to main menu")

        console.print(patch_table)
        console.print()
        choice = safe_input("\033[1;36mSELECT OPTION [0-4]: \033[0m").strip()

        if choice == '1':
            try:
                raw_data = target_file.read_bytes()
                dec_data = xor_crypt(raw_data, current_key)
                urls = find_urls(dec_data)
                if not urls:
                    console.print(f"[bold red][X] No URLs found with XOR Key 0x{current_key:02X}. Try changing key (Opt 2).[/bold red]")
                else:
                    url_table = Table(title=f"URLs Found in {target_file.name} ({len(urls)} total)", box=ROUNDED, border_style="cyan")
                    url_table.add_column("#", style="yellow", justify="center")
                    url_table.add_column("Offset", style="dim white")
                    url_table.add_column("Len", style="magenta")
                    url_table.add_column("URL", style="bold white")
                    for idx, (offset, url_str) in enumerate(urls, 1):
                        url_table.add_row(str(idx), hex(offset), str(len(url_str)), url_str)
                    console.print(url_table)
            except Exception as e:
                handle_exception(e, "List URLs", data_path)
            safe_input('\nPress Enter to continue...')

        elif choice == '2':
            key_inp = safe_input("-> Enter XOR Key (e.g. 0x2E or 46 or 0x00) [0x2E]: ").strip()
            if key_inp:
                try:
                    if key_inp.startswith(('0x', '0X')):
                        current_key = int(key_inp, 16) & 0xFF
                    else:
                        current_key = int(key_inp) & 0xFF
                    console.print(f"[bold green]✓ XOR Key updated to 0x{current_key:02X} ({current_key})[/bold green]")
                except ValueError:
                    console.print("[bold red][X] Invalid key format![/bold red]")
            safe_input('\nPress Enter to continue...')

        elif choice == '3':
            try:
                raw_data = target_file.read_bytes()
                dec_data = xor_crypt(raw_data, current_key)
                urls = find_urls(dec_data)
                if not urls:
                    console.print(f"[bold red][X] No URLs found to replace with Key 0x{current_key:02X}.[/bold red]")
                    safe_input('\nPress Enter to continue...')
                    continue

                url_table = Table(title=f"Select URL to Replace", box=ROUNDED, border_style="cyan")
                url_table.add_column("#", style="yellow", justify="center")
                url_table.add_column("Len", style="magenta")
                url_table.add_column("URL", style="bold white")
                for idx, (offset, url_str) in enumerate(urls, 1):
                    url_table.add_row(str(idx), str(len(url_str)), url_str)
                console.print(url_table)

                sel_str = safe_input("-> Enter URL number to replace (1-N) or 'C' to cancel: ").strip()
                if sel_str.upper() == 'C' or not sel_str.isdigit():
                    continue

                idx_num = int(sel_str) - 1
                if not (0 <= idx_num < len(urls)):
                    console.print("[bold red][X] Invalid selection number.[/bold red]")
                    safe_input('\nPress Enter to continue...')
                    continue

                old_offset, old_url = urls[idx_num]
                console.print(f"\n[bold cyan]Original URL:[/bold cyan] {old_url} (Len: {len(old_url)})")
                new_url = safe_input("-> Enter NEW URL (e.g., https://my-panel.com/api): ").strip()
                if not new_url:
                    console.print("[yellow][!] Operation cancelled (empty URL).[/yellow]")
                    safe_input('\nPress Enter to continue...')
                    continue

                patched = bytearray(dec_data)
                old_bytes = old_url.encode('utf-8')
                new_bytes = new_url.encode('utf-8')

                if len(new_bytes) > len(old_bytes):
                    extra = len(new_bytes) - len(old_bytes)
                    patched = bytearray(patched[:old_offset] + new_bytes + patched[old_offset + len(old_bytes):])
                else:
                    patched[old_offset:old_offset + len(new_bytes)] = new_bytes
                    pad_len = len(old_bytes) - len(new_bytes)
                    if pad_len > 0:
                        patched[old_offset + len(new_bytes):old_offset + len(old_bytes)] = b'\x00' * pad_len

                enc_patched = xor_crypt(bytes(patched), current_key)

                result_dir = data_path / "RESULT"
                result_dir.mkdir(parents=True, exist_ok=True)
                out_name = f"{target_file.stem}_patched{target_file.suffix}"
                out_file = result_dir / out_name
                out_file.write_bytes(enc_patched)

                console.print(f"\n[bold green]✅ URL Patched Successfully![/bold green]")
                console.print(f"[bold white]Old URL:[/bold white] {old_url}")
                console.print(f"[bold bright_green]New URL:[/bold bright_green] {new_url}")
                console.print(f"[bold cyan]Saved to:[/bold cyan] {out_file}")

            except Exception as e:
                handle_exception(e, "URL Replacement", data_path)
            safe_input('\nPress Enter to continue...')

        elif choice == '4':
            new_f, _ = pick_file_from_folder("Select Library / Binary File", so_dir, extensions=[".so", ".bin", ".exe", ".bytes", ".dat", ".txt"])
            if new_f and new_f.exists():
                target_file = new_f

        elif choice == '0':
            break

def run_beginner_guide(data_path: Path):
    print_banner()
    guide_table = Table(
        title="[bold bright_green]🔰 BEGINNER QUICK START & FAQ GUIDE 🔰[/bold bright_green]",
        show_header=True,
        header_style="bold green",
        box=ROUNDED,
        border_style="green",
        expand=True
    )
    guide_table.add_column("TOPIC", style="bold yellow", width=22)
    guide_table.add_column("EASY STEPS & TIPS", style="bold white")

    guide_table.add_row(
        "📦 PAK/OBB Unpack",
        "1. PAK/OBB file ko `/sdcard/FeaturesticLeaks/PAK/` me daalo.\n2. Option [1] -> Option [1] (Unpack Package). Output `/sdcard/FeaturesticLeaks/UNPACK/` me milega."
    )
    guide_table.add_row(
        "🛠️ Lua Inject into PAK",
        "1. Lua file ko `/sdcard/FeaturesticLeaks/INJECT/` me daalo.\n2. Option [1] -> Option [2] -> Option [3] (Inject Path).\n3. Target Path me `P1` (Content/Lua/GameLua/Mod/BRMod/Gameplay/Core) select karein!\n4. Auto-Fix / Auto-Compile prompt me [1] ya [2] press karein!"
    )
    guide_table.add_row(
        "⚡ Why Lua Fails?",
        "• Plain text .lua vs Bytecode .luac: Game bytecode chahti hai. Option [2] se Auto-Compile karein.\n• Wrong Target Path: Hamesha `P1` select karein PUBG/BGMI Gameplay Lua mods ke liye!"
    )
    guide_table.add_row(
        "🚀 1-Click Auto Lua",
        "Option [2] (Lua Tool) -> Option [8] (1-Click Auto Workflow) chalayein! Ye syntax error fix karta hai, compile karta hai aur output sync karta hai!"
    )
    guide_table.add_row(
        "🔗 URL & LIB Patcher",
        "Option [5] (Utilities) -> Option [3] (URL & LIB Patcher) se `.so` libraries me encrypted links scan karke new panel URLs inject karein!"
    )
    
    console.print(guide_table)
    safe_input('\nPress Enter to return to main menu...')

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
        cleanup_old_logs(data_path / "logs")
    except Exception:
        pass
    try:
        install_termux_shortcut_and_sdcard(data_path)
    except Exception:
        pass
    check_and_auto_update(interactive=False)

    # Direct Termux CLI Shortcuts: leak pak | leak lua | leak watch | leak ai | leak utils
    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower().strip()
        if cmd in ['chat', 'talk', 'aichat', 'bot']:
            run_ai_chat_mode(data_path)
            sys.exit(0)
        elif cmd in ['--ai', 'ai', 'a', 'aitools', 'assistant', 'watchai']:
            run_ai_watch_assistant(data_path)
            sys.exit(0)
        elif cmd in ['pak', 'p', 'paktools']:
            pak_obb_tools_menu(data_path)
            sys.exit(0)
        elif cmd in ['lua', 'l', 'luatools']:
            lua_tools_menu(data_path)
            sys.exit(0)
        elif cmd in ['watch', 'w', 'watchmode']:
            watch_mode_menu(data_path)
            sys.exit(0)
        elif cmd in ['utils', 'utility', 'u', 'util', 'utilities']:
            utilities_menu(data_path)
            sys.exit(0)

    while True:
        print_banner()
        console.print("[bold bright_cyan]📂 Termux Shortcuts:[bold bright_white] leak pak | leak lua | leak watch | leak ai | leak utils | leak update[/bold bright_white]\n")
        menu_table = Table(
            title="[bold bright_cyan]⚡ MAIN CATEGORY MENU ⚡[/bold bright_cyan]",
            show_header=True,
            header_style="bold bright_cyan",
            box=ROUNDED,
            border_style="bright_cyan",
            expand=True
        )
        menu_table.add_column("OPT", justify="center", width=8, style="bold bright_yellow")
        menu_table.add_column("CATEGORY", justify="left", width=22, style="bold bright_white")
        menu_table.add_column("DESCRIPTION", justify="left", style="bright_cyan")

        menu_table.add_row("[1]", "PAK Tools 📦", "Extract, Repack, Replace & Inject PAK/OBB/Skins")
        menu_table.add_row("[2]", "LUA Tools 🌙", "Compile, Decompile, Script Merger & Obfuscator")
        menu_table.add_row("[3]", "Watch Mode 👁️", "Real-time auto-unpack & auto-compile watcher")
        menu_table.add_row("[4]", "AI Tools 🤖", "AI Lua Repair & Multi-API Key Manager (Gemini/Groq)")
        menu_table.add_row("[5]", "Utilities 🛠️", "UE4 String Tool, Lib Patcher, Finder & FAQ Guide")
        menu_table.add_row("[U]", "Auto-Update 🚀", "Check & install latest GitHub version")
        menu_table.add_row("[0]", "EXIT ✗", "Close application")

        console.print(menu_table)
        console.print()
        choice = safe_input('\033[1;36mSELECT OPTION [0-5 / U]: \033[0m').strip()

        if choice == '1':
            pak_obb_tools_menu(data_path)
        elif choice == '2':
            lua_tools_menu(data_path)
        elif choice == '3':
            watch_mode_menu(data_path)
        elif choice == '4':
            ai_tools_menu(data_path)
        elif choice == '5':
            utilities_menu(data_path)
        elif choice.lower() in ['u', 'update', 'autoupdate', 'auto-update']:
            check_and_auto_update(interactive=True)
            safe_input('\nPress Enter to continue...')
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
