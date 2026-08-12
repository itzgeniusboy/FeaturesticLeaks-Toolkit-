import zlib
from functools import lru_cache
from typing import Optional

from zstandard import ZstdCompressionDict, ZstdDecompressor, DICT_TYPE_AUTO
from pak.crypto import CM_NONE, CM_ZLIB, CM_ZSTD, CM_ZSTD_DICT

class PakCompression:
    @staticmethod
    @lru_cache(maxsize=33)
    def _zstd_decompressor(dict: Optional[ZstdCompressionDict]) -> ZstdDecompressor:
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
                other_dict = None if active_dict else dict
                if other_dict:
                    try:
                        return PakCompression._zstd_decompressor(other_dict).decompress(block)
                    except Exception:
                        pass
                if active_dict or other_dict:
                    try:
                        return PakCompression._zstd_decompressor(None).decompress(block)
                    except Exception:
                        pass
                try:
                    return zlib.decompress(block)
                except Exception:
                    pass
                return bytes(block)
        else:
            return bytes(block)
