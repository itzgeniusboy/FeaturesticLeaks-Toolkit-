import re
from pathlib import Path
from lua.reader import (
    _LUA_CUSTOM_TO_STD, _LUA53_OPCODES
)

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
            old_fixed = lua_file.parent / f"{lua_file.stem}_fixed51.lua"
            if old_fixed.exists() and old_fixed != lua_file:
                try: old_fixed.unlink()
                except Exception: pass
            return lua_file
        else:
            out_file = lua_file.parent / f"{lua_file.stem}_fixed51.lua"
            out_file.write_text(masked_text, encoding="utf-8")
            return out_file
    except Exception:
        return lua_file
