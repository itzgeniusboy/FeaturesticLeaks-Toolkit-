import struct
from typing import Optional

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
