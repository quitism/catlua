# from ast import stmt
# from platform import node

from ast_nodes import *

class IREmitter:
    def __init__(self, ast, semantic_analyzer):
        self.ast = ast
        self.semantic = semantic_analyzer
        self.lines = []
        self.lines = []
        # not the full list but you get the idea
        self.AUDIO_PROPS = {"Volume", "PlaybackSpeed", "TimePosition", "IsLoaded", "IsPlaying", "IsPaused"}
        self.INPUT_PROPS = {"Text", "PlaceholderText", "CursorPosition", "SelectionStart"}
        # builtins map
        # format: "func_name": ("OPCODE", max_args, has_output_var)
        self.SIMPLE_CALLS = {
            "print": ("LOG", 1, False),
            "warn": ("WARN", 1, False),
            "error": ("ERROR", 1, False),
            "wait": ("WAIT", 1, False),
            "task.wait": ("WAIT", 1, False),
            "string.len": ("STR_LEN", 1, True),
            "string.lower": ("STR_LOWER", 1, True),
            "string.upper": ("STR_UPPER", 1, True),
            "string.split": ("STR_SPLIT", 2, True),
            "table.concat": ("TABLE_JOIN", 2, True),
            "makeVisible": ("LOOK_SHOW", 1, False),
            "makeInvisible": ("LOOK_HIDE", 1, False),
            "os.time": ("TIME_GET_UNIX", 0, True),
            "tick": ("TIME_GET_TICK", 0, True),
            "formatLocalTime": ("TIME_FORMAT_NOW", 1, True),
            "getUrl": ("NAV_GET_URL", 0, True),
            "getQuery": ("NAV_GET_QUERY", 1, True),
            "hexToRGB": ("COLOR_HEX_TO_RGB", 1, True),
            "RGBToHex": ("COLOR_RGB_TO_HEX", 1, True),
            "lerpColor": ("COLOR_LERP", 3, True),
            "clone": ("LOOK_DUPLICATE", 1, True),
            "destroy": ("LOOK_DELETE", 1, False),
            "redirect": ("NAV_REDIRECT", 1, False),
            "playAudio": ("AUDIO_PLAY", 1, True),
            "playLoopedAudio": ("AUDIO_PLAY_LOOP", 1, True),
            "stopAllAudio": ("AUDIO_STOP_ALL", 0, False),
            "getTimezone": ("TIME_GET_TIMEZONE", 0, True),
            "server.os.time": ("TIME_GET_SERVER_UNIX", 0, True),
            "setImage": ("LOOK_SET_IMG", 2, False),
            "setHeadshot": ("LOOK_SET_AVATAR", 3, False),
            "getAssetInfo": ("LOOK_GET_ASSET_INFO", 2, True),
            "getObjectsAtPosition": ("LOOK_GET_AT_POS", 2, True),
            "findFirstAncestor": ("HIER_FIND_ANCESTOR", 2, True),
            "findFirstDescendant": ("HIER_FIND_DESCENDANT", 2, True),
            "getDescendants": ("HIER_GET_DESCENDANTS", 1, True),
            "formatUniversalTime": ("TIME_FORMAT_UNIX", 2, True),
            "Stop": ("AUDIO_STOP", 1, False),
            "Pause": ("AUDIO_PAUSE", 1, False),
            "Resume": ("AUDIO_RESUME", 1, False),
            "hexToHSV": ("COLOR_HEX_TO_HSV", 1, True),
            "HSVToHex": ("COLOR_COLOR_HSV_TO_HEX", 1, True),
            "cookie.set": ("COOKIE_SET", 2, False),
            "cookie.get": ("COOKIE_GET", 1, True),
            "cookie.inc": ("COOKIE_INC", 2, False),
            "cookie.del": ("COOKIE_DEL", 1, False),
        }

    def emit(self):
        self.lines.append("CWIR_VERSION 1.0\n")
        
        for shard in self.ast.shards:
            self.lines.append("SCRIPT")
            if shard.alias:
                self.lines.append(f'SCRIPT_ALIAS "{shard.alias}"\n')
                
            for func in shard.func_defs:
                self.emit_function(func)
            for event in shard.events:
                self.emit_event(event)
                
            self.lines.append("END_SCRIPT\n")
            
        return "\n".join(self.lines)

    def add(self, line):
        self.lines.append(line)

    def new_tmp_var(self):
        if not hasattr(self, 'tmp_counter'):
            self.tmp_counter = 0
        self.tmp_counter += 1
        tmp_ref = VarRef(0, f"__tmp{self.tmp_counter}")
        tmp_ref.prefix = "l!"
        return tmp_ref

    def format_interp(self, raw):
        import re
        result = re.sub(r'\{g!(\w+)\}', r'{\1}', raw)
        return f'"{result}"'

    def scaffold(self, node, ind):
        if isinstance(node, (NumberLit, StringLit)):
            tmp = self.new_tmp_var()
            self.add(f'{ind}VAR_SET {self.format_var_name(tmp)} {self.format_val(node)}')
            return tmp
        if isinstance(node, BinaryExpr):
            left_node = self.scaffold(node.left, ind)
            right_node = self.scaffold(node.right, ind)
            
            left_str = self.format_val(left_node)
            right_str = self.format_val(right_node)

            if node.op == "..":
                tmp_ref = self.new_tmp_var()
                tmp_str = self.format_var_name(tmp_ref)
                self.add(f'{ind}STR_CONCAT {left_str} {right_str} {tmp_str}')
                return tmp_ref

            if isinstance(left_node, VarRef) and left_node.name.startswith("__tmp"):
                tmp_ref = left_node
                tmp_str = self.format_var_name(tmp_ref)
            else:
                # create a new one if the left side is just a normal variable or number
                tmp_ref = self.new_tmp_var()
                tmp_str = self.format_var_name(tmp_ref)
                self.add(f'{ind}VAR_SET {tmp_str} {left_str}')
            
            op_map = {"+": "VAR_INC", "-": "VAR_DEC", "*": "VAR_MUL", "/": "VAR_DIV", "^": "VAR_POW", "%": "VAR_MOD"}
            if node.op in op_map:
                self.add(f'{ind}{op_map[node.op]} {tmp_str} {right_str}')
            
            return tmp_ref

        elif isinstance(node, CallStmt):
            tmp_ref = self.new_tmp_var()
            tmp_str = self.format_var_name(tmp_ref)
            result = self.emit_call(node, ind, target_override=tmp_str)
            return result if isinstance(result, VarRef) else tmp_ref

        elif isinstance(node, UnaryExpr) and node.op == "-":
            # native format_val already handles raw negative numbers (-5), 
            # this catches complex negations like -(5 + x)
            if type(node.right).__name__ == "NumberLit": return node 
            val = self.format_val(self.scaffold(node.right, ind))
            tmp_ref = self.new_tmp_var()
            tmp_str = self.format_var_name(tmp_ref)
            self.add(f'{ind}VAR_SET {tmp_str} "0"')
            self.add(f'{ind}VAR_DEC {tmp_str} {val}')
            return tmp_ref
        
        return node
    
    def format_var_name(self, node):
        if isinstance(node, VarRef):
            prefix = node.prefix if node.prefix in ('l!', 'o!') else ""
            return f'"{prefix}{node.name}"'
        return '"temp"'

    def format_val(self, node):
        if node is None: return "EMPTY"
        if isinstance(node, NumberLit):
            return f'"{node.value}"'
        if isinstance(node, StringLit):
            return f'"{node.value}"'
        if isinstance(node, InterpStringLit):
            return self.format_interp(node.value)
        if isinstance(node, UnaryExpr) and node.op == "-" and isinstance(node.right, NumberLit):
            return f'"-{node.right.value}"'
        if isinstance(node, VarRef):
            if node.name == "nil": return "EMPTY"
            prefix = node.prefix if node.prefix in ('l!', 'o!') else ""
            return f'"{{{prefix}{node.name}}}"'
        if isinstance(node, PropRef):
            obj_name = node.obj.name if isinstance(node.obj, VarRef) else "obj"
            return f'"{{{obj_name}.{node.prop}}}"'
        return "EMPTY"

    def format_obj(self, node):
        if isinstance(node, VarRef):
            # uppercase = static UI element, lowercase = runtime object variable (cheap trick)
            if node.name[0].isupper():
                return f'({node.name})'
            prefix = node.prefix if node.prefix in ('l!', 'o!') else ""
            return f'"{{{prefix}{node.name}}}"'
        return self.format_val(node)

    def emit_function(self, func):
        args_str = " ".join([f'"{arg}"' for arg in func.params])
        args_arr = f"[{args_str}]" if args_str else "[]"
        self.add(f'EVENT FUNC_DEF "{func.name}" {args_arr}')
        self.emit_block(func.body)
        self.add("END_EVENT\n")

    def emit_event(self, event):
        ev_map = {
            "OnWebsiteLoaded": "LOADED",
            "OnMessageReceived": "MSG_RECEIVED",
            "OnCrossSiteMessageReceived": "CROSSSITE_MSG",
        }
        name = event.event_type
        args_out = ""
        
        if name in ev_map: ev_type = ev_map[name]
        elif name.endswith(".MouseButton1Click"):
            ev_type, args_out = "PRESSED", f"({name.split('.')[0]})"
        elif name.endswith(".MouseEnter"):
            ev_type, args_out = "MOUSE_ENTER", f"({name.split('.')[0]})"
        elif name.endswith(".MouseLeave"):
            ev_type, args_out = "MOUSE_LEAVE", f"({name.split('.')[0]})"
        elif name.endswith(".FocusLost"):
            ev_type, args_out = "INPUT_SUBMIT", f"({name.split('.')[0]})"
        elif name.endswith(".InputBegan"):
            ev_type, args_out = "KEY_PRESSED", f'"{event.args[0]}"' if event.args else '"Unknown"'
        elif name.endswith(".OnDonationPurchase"):
            ev_type, args_out = "DONATION", f"({name.split('.')[0]})"
        elif name.endswith(".MouseButton2Click"):
            ev_type, args_out = "RIGHT_CLICKED", f"({name.split('.')[0]})"
        elif name.endswith(".MouseButton1Down"):
            ev_type, args_out = "MOUSE_DOWN", f"({name.split('.')[0]})"
        elif name.endswith(".MouseButton1Up"):
            ev_type, args_out = "MOUSE_UP", f"({name.split('.')[0]})"
        else:
            ev_type, args_out = "CHANGED", f"({name.split('.')[0] if '.' in name else name})"
            
        self.add(f'EVENT {ev_type} {args_out}'.strip())
        self.emit_block(event.body)
        self.add("END_EVENT\n")

    def emit_block(self, stmts, indent="    "):
        for stmt in stmts:
            self.emit_stmt(stmt, indent)

    def emit_stmt(self, stmt, ind):
        if isinstance(stmt, AssignStmt): self.emit_assign(stmt, ind)
        elif isinstance(stmt, CommentStmt): self.add(f'{ind}COMMENT "{stmt.value}"')
        elif isinstance(stmt, CallStmt): self.emit_call(stmt, ind)
        elif isinstance(stmt, IfStmt): self.emit_if(stmt, ind)
        elif isinstance(stmt, RepeatStmt): self.emit_repeat(stmt, ind)
        elif isinstance(stmt, ForStmt): self.emit_for(stmt, ind)
        elif isinstance(stmt, BreakStmt): self.add(f"{ind}BREAK")
        elif isinstance(stmt, ReturnStmt):
            val = stmt.value
            if isinstance(val, (BinaryExpr, CallStmt, UnaryExpr)):
                val = self.scaffold(val, ind)
            self.add(f"{ind}RETURN {self.format_val(val)}")
        elif isinstance(stmt, DeleteStmt):
            if isinstance(stmt.target, VarRef):
                if stmt.target.name[0].isupper():
                    self.add(f"{ind}LOOK_DELETE {self.format_obj(stmt.target)}")
                else:
                    self.add(f'{ind}VAR_DEL {self.format_var_name(stmt.target)}')
            elif isinstance(stmt.target, PropRef):
                tbl = self.format_var_name(stmt.target.obj)
                self.add(f'{ind}TABLE_DEL "{stmt.target.prop}" {tbl}')
            elif isinstance(stmt.target, IndexRef):
                tbl = self.format_var_name(stmt.target.table)
                entry = self.format_val(stmt.target.index)
                self.add(f'{ind}TABLE_DEL {entry} {tbl}')

    def emit_assign(self, stmt, ind):
        target = stmt.targets[0]
        if isinstance(target, VarRef) and isinstance(stmt.value, VarRef):
            if stmt.value.name in self.semantic.SERVICES:
                return

        if isinstance(stmt.value, CallStmt):
            if isinstance(stmt.value.func_expr, PropRef):
                if stmt.value.func_expr.prop == "GetMouseLocation":
                    x_var = self.format_var_name(stmt.targets[0])
                    y_var = self.format_var_name(stmt.targets[1]) if len(stmt.targets) > 1 else "EMPTY"
                    self.add(f'{ind}INPUT_GET_CURSOR {x_var} {y_var}')
                    return

        if isinstance(stmt.value, PropRef):
            if isinstance(stmt.value.obj, VarRef) and stmt.value.obj.name == "UserInputService":
                if stmt.value.prop == "GetMousePosition()":
                    if len(stmt.targets) >= 2:
                        x_var = self.format_var_name(stmt.targets[0])
                        y_var = self.format_var_name(stmt.targets[1])
                    else:
                        x_var = self.format_var_name(stmt.targets[0])
                        y_var = "EMPTY"
                    self.add(f'{ind}INPUT_GET_VIEWPORT {x_var} {y_var}')
                    return
            elif isinstance(stmt.value.obj, VarRef) and stmt.value.obj.name == "Camera":
                if stmt.value.prop == "ViewportSize":
                    if len(stmt.targets) >= 2:
                        x_var = self.format_var_name(stmt.targets[0])
                        y_var = self.format_var_name(stmt.targets[1])
                    else:
                        x_var = self.format_var_name(stmt.targets[0])
                        y_var = "EMPTY"
                    self.add(f'{ind}INPUT_GET_VIEWPORT {x_var} {y_var}')
                    return

        if isinstance(stmt.value, CallStmt):
            func_expr = stmt.value.func_expr
            if isinstance(func_expr, PropRef) and isinstance(func_expr.obj, VarRef):
                if func_expr.obj.name == "math" and func_expr.prop in ("round", "floor", "ceil"):
                    op = {"round": "VAR_ROUND", "floor": "VAR_FLOOR", "ceil": "VAR_CEIL"}[func_expr.prop]
                    out_var = self.format_var_name(target)
                    print(out_var)
                    arg = stmt.value.args[0] if stmt.value.args else None
                    if arg is not None:
                        self.add(f'{ind}VAR_SET {out_var} {self.format_val(arg)}')
                    self.add(f'{ind}{op} {out_var}')
                    return
                 
        if isinstance(stmt.value, UnaryExpr) and stmt.value.op == "#":
            var_name = self.format_var_name(target)
            arr_node = stmt.value.right
            if isinstance(arr_node, VarRef):
                prefix = arr_node.prefix if arr_node.prefix in ('l!', 'o!') else ""
                array_name = f"{prefix}{arr_node.name}"
            else:
                array_name = "temp"
            self.add(f'{ind}TABLE_LEN "{array_name}" {var_name}')
            return
            
        if isinstance(stmt.value, BinaryExpr) and stmt.value.op == "..":
            out_var = self.format_var_name(target)
            left = self.format_val(stmt.value.left)
            right = self.format_val(stmt.value.right)
            self.add(f'{ind}STR_CONCAT {left} {right} {out_var}')
            return

        if isinstance(stmt.value, (BinaryExpr, CallStmt, UnaryExpr)):
            stmt.value = self.scaffold(stmt.value, ind)

        if isinstance(stmt.value, TableLit):
            self.add(f'{ind}TABLE_CREATE {self.format_var_name(target)}')
            return
        
        is_object_assign = getattr(stmt, 'annotations', {}).get('type') == 'object'
        if is_object_assign or (isinstance(stmt.value, VarRef) and getattr(stmt.value, 'name', '')[0].isupper()):
            val_str = self.format_obj(stmt.value)
        else:
            val_str = self.format_val(stmt.value)

        # handle reading properties & tables
        if isinstance(stmt.value, (PropRef, IndexRef)):
            node = stmt.value
            is_prop, prop = False, ""
            
            if isinstance(node, PropRef):
                prop = node.prop
                is_prop = prop[0].isupper() or prop in ("Text", "Parent")
            elif isinstance(node.index, StringLit):
                prop = node.index.value
                is_prop = prop[0].isupper() or prop in ("Text", "Parent")

            obj_node = node.obj if isinstance(node, PropRef) else node.table
            obj_name = obj_node.name if isinstance(obj_node, VarRef) else ""
            out_var = self.format_var_name(target)

            # audio and input getters
            is_audio = getattr(stmt, 'annotations', {}).get('type') == 'audio' or prop in getattr(self, 'AUDIO_PROPS', set())
            is_input = getattr(stmt, 'annotations', {}).get('type') == 'input' or prop in getattr(self, 'INPUT_PROPS', set())

            if is_audio:
                obj_ref = self.format_var_name(obj_node)
                self.add(f'{ind}AVAR_GET "{prop}" {obj_ref} {out_var}')
                return
                
            if is_input and prop == "Text":
                obj_ref = self.format_obj(obj_node)
                self.add(f'{ind}INPUT_GET_TEXT {obj_ref} {out_var}')
                return

            if obj_name == "LocalPlayer":
                if prop == "Name": self.add(f'{ind}USER_GET_NAME {out_var}')
                elif prop == "UserId": self.add(f'{ind}USER_GET_ID {out_var}')
                elif prop == "DisplayName": self.add(f'{ind}USER_GET_DISPLAY {out_var}')
                return

            if is_prop:
                obj_ref = self.format_obj(obj_node)
                if prop == "Parent": self.add(f'{ind}HIER_GET_PARENT {obj_ref} {out_var}')
                else: self.add(f'{ind}LOOK_GET_PROP "{prop}" {obj_ref} {out_var}')
            else:
                tbl_ref = self.format_var_name(obj_node)
                idx_node = getattr(target, 'index', None)
                entry = f'"{prop}"' if prop else self.format_val(idx_node)
                self.add(f'{ind}TABLE_GET {entry} {tbl_ref} {out_var}')
            return

        # handle writing properties & tables
        if isinstance(target, (PropRef, IndexRef)):
            is_prop, prop = False, ""
            
            if isinstance(target, PropRef):
                prop = target.prop
                is_prop = prop[0].isupper() or prop in ("Text", "Parent")
            elif isinstance(target.index, StringLit):
                prop = target.index.value
                is_prop = prop[0].isupper() or prop in ("Text", "Parent")

            obj_node = target.obj if isinstance(target, PropRef) else target.table

            # audio & table setters
            is_audio = getattr(stmt, 'annotations', {}).get('type') == 'audio' or prop in getattr(self, 'AUDIO_PROPS', set())
            is_object_table = getattr(stmt, 'annotations', {}).get('type') == 'object' or val_str.startswith('(') or val_str.startswith('"{o!')

            if is_audio:
                obj_ref = self.format_var_name(obj_node)
                self.add(f'{ind}AVAR_SET "{prop}" {obj_ref} {val_str}')
                return

            if is_prop:
                obj_ref = self.format_obj(obj_node)
                if prop == "Parent":
                    self.add(f'{ind}HIER_PARENT {obj_ref} {val_str}')
                elif prop == "Text":
                    self.add(f'{ind}LOOK_SET_TEXT {obj_ref} {val_str}')
                else:
                    self.add(f'{ind}LOOK_SET_PROP "{prop}" {obj_ref} {val_str}')
            else:
                tbl_ref = self.format_var_name(obj_node)
                idx_node = getattr(target, 'index', None)
                entry = f'"{prop}"' if prop else self.format_val(idx_node)
                
                if is_object_table:
                    self.add(f'{ind}TABLE_SET_OBJ {entry} {tbl_ref} {val_str}')
                else:
                    self.add(f'{ind}TABLE_SET {entry} {tbl_ref} {val_str}')
            return

        out_var = self.format_var_name(target)
        
        if stmt.op == "=": self.add(f'{ind}VAR_SET {out_var} {val_str}')
        elif stmt.op == "+=": self.add(f'{ind}VAR_INC {out_var} {val_str}')
        elif stmt.op == "-=": self.add(f'{ind}VAR_DEC {out_var} {val_str}')
        elif stmt.op == "*=": self.add(f'{ind}VAR_MUL {out_var} {val_str}')
        elif stmt.op == "/=": self.add(f'{ind}VAR_DIV {out_var} {val_str}')
        elif stmt.op == "^=": self.add(f'{ind}VAR_POW {out_var} {val_str}')
        elif stmt.op == "%=": self.add(f'{ind}VAR_MOD {out_var} {val_str}')

    def emit_call(self, stmt, ind, target_override=None):
        func_name = ""
        if type(stmt.func_expr).__name__ == "VarRef":
            func_name = stmt.func_expr.name
        elif type(stmt.func_expr).__name__ == "PropRef":
            prop = stmt.func_expr.prop
            obj = stmt.func_expr.obj
            audio_methods = {"Stop": "AUDIO_STOP", "Pause": "AUDIO_PAUSE", "Resume": "AUDIO_RESUME"}
            if prop in audio_methods:
                obj_ref = self.format_var_name(obj) if isinstance(obj, VarRef) else "EMPTY"
                self.add(f"{ind}{audio_methods[prop]} {obj_ref}")
                return
            obj_name = getattr(obj, 'name', 'obj')
            func_name = f"{obj_name}.{prop}"
        
        for i in range(len(stmt.args)):
            if isinstance(stmt.args[i], (BinaryExpr, UnaryExpr)):
                stmt.args[i] = self.scaffold(stmt.args[i], ind)

        out_var = target_override if target_override else "EMPTY"
        if not target_override and getattr(stmt, 'targets', None):
            out_var = self.format_var_name(stmt.targets[0])

        # annotation override
        is_builtin = getattr(stmt, 'force_builtin', False)
        is_custom = getattr(stmt, 'force_custom', False)

        if (is_custom or func_name in self.semantic.funcs) and not is_builtin:
            args_fmt = " ".join([self.format_val(a) for a in stmt.args])
            args_arr = f"[{args_fmt}]" if args_fmt else "[]"
            
            if getattr(stmt, 'is_protected', False):
                success_var = self.format_var_name(stmt.targets[0]) if len(stmt.targets) > 0 else "EMPTY"
                out_var_prot = self.format_var_name(stmt.targets[1]) if len(stmt.targets) > 1 else "EMPTY"
                self.add(f'{ind}FUNC_RUN_PROTECTED "{func_name}" {args_arr} {success_var} {out_var_prot}')
            elif getattr(stmt, 'is_bg', False):
                self.add(f'{ind}FUNC_RUN_BG "{func_name}" {args_arr}')
            else:
                self.add(f'{ind}FUNC_RUN "{func_name}" {args_arr} {out_var}')
            return

        if func_name in self.SIMPLE_CALLS:
            opcode, expected_args, yields_output = self.SIMPLE_CALLS[func_name]
            
            args_fmt = []
            for i in range(expected_args):
                if i < len(stmt.args):
                    if opcode == "TABLE_JOIN" and i == 0:
                        val = self.format_var_name(stmt.args[i])
                    else:
                        val = self.format_obj(stmt.args[i]) if "LOOK_" in opcode else self.format_val(stmt.args[i])
                    args_fmt.append(val)
                else:
                    args_fmt.append('"0"' if opcode == "WAIT" else '""' if opcode == "TABLE_JOIN" else "EMPTY")
            
            if yields_output:
                args_fmt.append(out_var)
                
            self.add(f"{ind}{opcode} " + " ".join(args_fmt))
            return

        if func_name.startswith("math."):
            math_func = func_name.split(".")[1]
            if math_func == "random":
                min_val = self.format_val(stmt.args[0]) if len(stmt.args) > 0 else '"0"'
                max_val = self.format_val(stmt.args[1]) if len(stmt.args) > 1 else '"1"'
                self.add(f"{ind}VAR_RANDOM {out_var} {min_val} {max_val}")
            elif math_func in ("round", "floor", "ceil"):
                op = {"round": "VAR_ROUND", "floor": "VAR_FLOOR", "ceil": "VAR_CEIL"}[math_func]
                if stmt.args:
                    arg = stmt.args[0]
                    if out_var and out_var != "EMPTY":
                        self.add(f"{ind}VAR_SET {out_var} {self.format_val(arg)}")
                        self.add(f"{ind}{op} {out_var}")
                        return out_var
                    else:
                        if not isinstance(arg, VarRef):
                            arg = self.scaffold(arg, ind)
                        arg_var = self.format_var_name(arg)
                        self.add(f"{ind}{op} {arg_var}")
                        return arg
                return None
            else:
                args_fmt = " ".join([self.format_val(a) for a in stmt.args])
                args_arr = f"[{args_fmt}]" if args_fmt else "[]"
                self.add(f'{ind}MATH_RUN "{math_func}" {args_arr} {out_var}')

        elif func_name == "string.sub":
            val = self.format_var_name(stmt.args[0]) if len(stmt.args) > 0 else "EMPTY"
            start = self.format_val(stmt.args[1]) if len(stmt.args) > 1 else "EMPTY"
            end = self.format_val(stmt.args[2]) if len(stmt.args) > 2 else "EMPTY"
            self.add(f"{ind}STR_SUB {val} {start} {end}")
            
        elif func_name == "string.gsub":
            val = self.format_var_name(stmt.args[0]) if len(stmt.args) > 0 else "EMPTY"
            find = self.format_val(stmt.args[1]) if len(stmt.args) > 1 else "EMPTY"
            repl = self.format_val(stmt.args[2]) if len(stmt.args) > 2 else "EMPTY"
            self.add(f"{ind}STR_REPLACE {find} {val} {repl}")

        elif func_name in ("page.broadcast", "site.broadcast", "crossSite.broadcast"):
            op = {"page.broadcast": "NET_BROADCAST_PAGE", "site.broadcast": "NET_BROADCAST_SITE", "crossSite.broadcast": "NET_BROADCAST_CROSSSITE"}[func_name]
            msg = self.format_val(stmt.args[0]) if stmt.args else "EMPTY"
            target = self.format_val(stmt.args[1]) if len(stmt.args) > 1 else "EMPTY"
            self.add(f"{ind}{op} {msg} {target}" if func_name == "crossSite.broadcast" else f"{ind}{op} {msg}")

        elif type(stmt.func_expr).__name__ == "PropRef" and stmt.func_expr.prop == "insert":
            obj = stmt.func_expr.obj
            if isinstance(obj, VarRef):
                prefix = obj.prefix if obj.prefix in ('l!', 'o!') else ""
                arr = f'"{prefix}{obj.name}"'
            else:
                arr = self.format_var_name(obj)
            val = self.format_val(stmt.args[0]) if len(stmt.args) > 0 else "EMPTY"
            pos = self.format_val(stmt.args[1]) if len(stmt.args) > 1 else "EMPTY"
            self.add(f"{ind}TABLE_INSERT {val} {pos} {arr}")
            
        elif type(stmt.func_expr).__name__ == "PropRef" and stmt.func_expr.prop == "remove":
            arr = self.format_var_name(stmt.func_expr.obj)
            pos = self.format_val(stmt.args[0]) if len(stmt.args) > 0 else "EMPTY"
            obj = stmt.func_expr.obj
            if isinstance(obj, VarRef):
                prefix = obj.prefix if obj.prefix in ('l!', 'o!') else ""
                arr = f'"{prefix}{obj.name}"'
            else:
                arr = self.format_var_name(obj)
            self.add(f"{ind}TABLE_REMOVE {pos} {arr}")

        elif func_name == "getChildren":
            obj = self.format_obj(stmt.args[0]) if len(stmt.args) > 0 else "EMPTY"
            self.add(f"{ind}HIER_GET_CHILDREN {obj} {out_var}")
            
        elif func_name == "findFirstChild":
            obj = self.format_obj(stmt.args[0]) if len(stmt.args) > 0 else "EMPTY"
            child_name = self.format_val(stmt.args[1]) if len(stmt.args) > 1 else "EMPTY"
            self.add(f"{ind}HIER_FIND_CHILD {child_name} {obj} {out_var}")

        elif func_name == "tween":
            obj = self.format_obj(stmt.args[0]) if len(stmt.args) > 0 else "EMPTY"
            prop = self.format_val(stmt.args[1]) if len(stmt.args) > 1 else "EMPTY"
            val = self.format_val(stmt.args[2]) if len(stmt.args) > 2 else "EMPTY"
            time = self.format_val(stmt.args[3]) if len(stmt.args) > 3 else "EMPTY"
            style = self.format_val(stmt.args[4]) if len(stmt.args) > 4 else "EMPTY"
            dir_ = self.format_val(stmt.args[5]) if len(stmt.args) > 5 else "EMPTY"
            self.add(f"{ind}LOOK_TWEEN {prop} {obj} {val} {time} {style} {dir_}")

    def emit_if(self, stmt, ind):
        self._emit_condition(stmt.condition, ind)
        self.emit_block(stmt.true_body, ind + "    ")
        closing_ends, curr_ind = 1, ind
        
        for elif_cond, elif_body in stmt.else_ifs:
            self.add(f"{curr_ind}ELSE")
            curr_ind += "    "
            self._emit_condition(elif_cond, curr_ind)
            self.emit_block(elif_body, curr_ind + "    ")
            closing_ends += 1
            
        if stmt.false_body:
            self.add(f"{curr_ind}ELSE")
            self.emit_block(stmt.false_body, curr_ind + "    ")
            
        for _ in range(closing_ends):
            self.add(f"{curr_ind}END_IF")
            if len(curr_ind) >= 4: curr_ind = curr_ind[:-4]

    def _emit_condition(self, cond, ind):
        if isinstance(cond, CallStmt):
            func_name = cond.func_expr.name if isinstance(cond.func_expr, VarRef) else ""
            
            if isinstance(cond.func_expr, PropRef):
                if getattr(cond.func_expr.obj, 'name', '') == "string" and cond.func_expr.prop == "find":
                    str_a = self.format_val(cond.args[0]) if len(cond.args) > 0 else "EMPTY"
                    str_b = self.format_val(cond.args[1]) if len(cond.args) > 1 else "EMPTY"
                    self.add(f"{ind}IF_CONTAINS {str_a} {str_b}")
                    return

            if func_name == "IsAncestorOf":
                obj = self.format_obj(cond.args[0]) if len(cond.args) > 0 else "EMPTY"
                child = self.format_obj(cond.args[1]) if len(cond.args) > 1 else "EMPTY"
                self.add(f"{ind}IF_IS_ANCESTOR {obj} {child}")
                return
                
            if func_name == "IsDescendantOf":
                child = self.format_obj(cond.args[0]) if len(cond.args) > 0 else "EMPTY"
                ancestor = self.format_obj(cond.args[1]) if len(cond.args) > 1 else "EMPTY"
                self.add(f"{ind}IF_IS_DESCENDANT {child} {ancestor}")
                return

            if func_name == "keyDown":
                key = self.format_val(cond.args[0]) if cond.args else '""'
                self.add(f"{ind}IF_KEY_DOWN {key}")
                return
            if func_name == "leftMouseDown":
                self.add(f"{ind}IF_MOUSE_LEFT")
                return
            if func_name == "rightMouseDown":
                self.add(f"{ind}IF_MOUSE_RIGHT")
                return
            if func_name == "middleMouseDown":
                self.add(f"{ind}IF_MOUSE_MIDDLE")
                return
        if isinstance(cond, BinaryExpr):
            if cond.op in ("==", "~=") and getattr(cond.right, "name", None) == "nil":
                op = "IF_NOT_EXISTS" if cond.op == "==" else "IF_EXISTS"
                var_name = self.format_var_name(cond.left)
                self.add(f"{ind}{op} {var_name}")
                return
                
            op_map = {
                "==": "IF_EQ", "~=": "IF_NEQ", ">": "IF_GT", ">=": "IF_GTE",
                "<": "IF_LT", "<=": "IF_LTE", "contains": "IF_CONTAINS", "not contains": "IF_NOT_CONTAINS"
            }
            if cond.op in op_map:
                left, right = self.format_val(cond.left), self.format_val(cond.right)
                self.add(f"{ind}{op_map[cond.op]} {left} {right}")
            elif cond.op in ("and", "or", "nor", "xor"):
                op_name = f"IF_{cond.op.upper()}"
                left = cond.left.name if isinstance(cond.left, VarRef) else "temp"
                right = cond.right.name if isinstance(cond.right, VarRef) else "temp"
                self.add(f'{ind}{op_name} "{left}" "{right}"')
        else:
            self.add(f"{ind}IF_NEQ {self.format_val(cond)} EMPTY")

    def emit_repeat(self, stmt, ind):
        if stmt.count: self.add(f"{ind}REPEAT {self.format_val(stmt.count)}")
        else: self.add(f"{ind}REPEAT_FOREVER")
        self.emit_block(stmt.body, ind + "    ")
        self.add(f"{ind}END_REPEAT")

    def emit_for(self, stmt, ind):
        key_var = stmt.vars[0] if len(stmt.vars) > 1 else None
        val_var = stmt.vars[-1]
        
        if isinstance(stmt.iterator, VarRef):
            tbl_var = self.format_var_name(stmt.iterator)
            self.add(f'{ind}TABLE_ITER {tbl_var}')
        else:
            self.add(f'{ind}TABLE_ITER "temp"')
        
        start = len(self.lines)
        self.emit_block(stmt.body, ind + "    ")
        
        for i in range(start, len(self.lines)):
            if key_var:
                self.lines[i] = self.lines[i].replace(f'{{{key_var}}}', '{l!index}')
                self.lines[i] = self.lines[i].replace(f'{{l!{key_var}}}', '{l!index}')
            self.lines[i] = self.lines[i].replace(f'{{{val_var}}}', '{l!value}')
            self.lines[i] = self.lines[i].replace(f'{{l!{val_var}}}', '{l!value}')
        
        self.add(f"{ind}END_ITER")