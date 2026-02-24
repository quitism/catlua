from ast_nodes import *

class ParseError(Exception):
    pass

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.block_annotations = {}
        self.errors = []

    def peek(self, offset=0):
        if self.pos + offset < len(self.tokens):
            return self.tokens[self.pos + offset]
        return self.tokens[-1] # EOF

    def consume(self):
        tok = self.peek()
        self.pos += 1
        return tok

    def match(self, type_, value=None):
        tok = self.peek()
        if tok.type == type_ and (value is None or tok.value == value):
            return self.consume()
        return None

    def expect(self, type_, value=None):
        tok = self.match(type_, value)
        if not tok:
            expected = value if value else type_
            raise ParseError(f"expected {expected}, got {self.peek().value!r} at line {self.peek().line}")
        return tok
    
    def synchronize(self):
        # advance past the bad token
        self.consume()
        
        while self.peek().type != "EOF":
            safe_keywords = {"function", "local", "global", "object", "if", "for", "repeat", "end", "return", "break", "delete"}
            if self.peek().type == "KEYWORD" and self.peek().value in safe_keywords:
                return
            self.consume()

    def parse(self):
        shards = []
        current_shard = ScriptShardNode()
        
        while self.peek().type != "EOF":
            line = self.peek().line
            
            # --- REQUIRE PARSING ---
            if self.peek().type == "IDENT" and self.peek().value == "require":
                self.consume()
                has_parens = self.match("PUNC", "(")
                req_file = self.expect("STRING").value
                if has_parens:
                    self.expect("PUNC", ")")
                current_shard.requires.append(req_file)
                continue

            # --- ANNOTATION PARSING ---
            if self.peek().type == "ANNOTATION":
                anno_text = self.consume().value[3:].strip()
                
                if anno_text == "script":
                    if current_shard.events or current_shard.func_defs:
                        shards.append(current_shard)
                    current_shard = ScriptShardNode()
                    
                elif anno_text.startswith("script_alias"):
                    parts = anno_text.split("=")
                    if len(parts) > 1:
                        alias = parts[1].strip().strip('"').strip("'")
                        current_shard.alias = alias
                continue
                
            # --- NORMAL PARSING ---
            if self.match("KEYWORD", "function"):
                name = self.expect("IDENT").value
                
                while self.match("PUNC", "."):
                    name += "." + self.expect("IDENT").value
                    
                self.expect("PUNC", "(")
                params = []
                if not self.match("PUNC", ")"):
                    params.append(self.expect("IDENT").value)
                    while self.match("PUNC", ","):
                        params.append(self.expect("IDENT").value)
                    self.expect("PUNC", ")")
                body = self.parse_block()
                self.expect("KEYWORD", "end")
                current_shard.func_defs.append(FuncDefNode(line, name, params, body))
            else:
                obj_or_event = self.expect("IDENT").value
                event_name = obj_or_event
                obj_name = None
                
                if self.match("PUNC", "."):
                    obj_name = obj_or_event
                    event_name = self.expect("IDENT").value
                
                args = []
                if self.match("PUNC", "("):
                    if not self.match("PUNC", ")"):
                        arg_tok = self.consume()
                        if arg_tok.type not in ("IDENT", "STRING"):
                            raise ParseError(f"expected IDENT or STRING, got {arg_tok.value!r} at line {line}")
                        args.append(arg_tok.value)
                        
                        while self.match("PUNC", ","):
                            arg_tok = self.consume()
                            if arg_tok.type not in ("IDENT", "STRING"):
                                raise ParseError(f"expected IDENT or STRING, got {arg_tok.value!r} at line {line}")
                            args.append(arg_tok.value)
                        self.expect("PUNC", ")")
                
                full_event = f"{obj_name}.{event_name}" if obj_name else event_name
                body = self.parse_block(is_event=True)
                self.expect("KEYWORD", "end")
                
                current_shard.events.append(EventNode(line, full_event, args, body))
                
        if current_shard.events or current_shard.func_defs:
            shards.append(current_shard)
                
        return ScriptNode(1, shards)

    def parse_block(self, is_event=False):
        stmts = []
        line_annotations = {}

        while self.peek().type != "EOF":
            if self.peek().type == "ANNOTATION":
                anno_str = self.consume().value
                is_block = anno_str.startswith("--#")
                # strip the '--@' or '--#' and leading whitespace
                anno_text = anno_str[3:].strip()
                
                if is_block:
                    if anno_text == "end":
                        self.block_annotations.clear()
                    else:
                        parts = anno_text.split(maxsplit=1)
                        if not parts:
                            continue
                        
                        anno_key = parts[0]
                        if len(parts) > 1:
                            self.block_annotations[anno_key] = parts[1]
                        else:
                            self.block_annotations.pop(anno_key, None)
                else:
                    for tag in anno_text.split():
                        kv = tag.split("=", 1)
                        if len(kv) == 2:
                            line_annotations[kv[0]] = kv[1]
                        else:
                            line_annotations[kv[0]] = True
                continue

            val = self.peek().value
            if val in ("end", "else", "elseif"):
                break
            
            if is_event and self.peek().type == "IDENT" and self.peek(1).value in (".", "(") and val not in ("bg", "protected", "delete"):
                pass
            
            try:
                stmt = self.parse_statement()
                if stmt:
                    stmt.annotations = self.block_annotations.copy()
                    stmt.annotations.update(line_annotations)
                    
                    stmt.force_builtin = stmt.annotations.get("builtin", False)
                    stmt.force_custom = stmt.annotations.get("custom", False)
                    
                    stmts.append(stmt)
            except ParseError as e:
                self.errors.append(str(e))
                self.synchronize()
                
            line_annotations.clear()
                
        return stmts

    def parse_statement(self):
        line = self.peek().line
        
        if self.peek().type == "COMMENT":
            return CommentStmt(line, self.consume().value)
        
        if self.match("KEYWORD", "if"):
            cond = self.parse_expr()
            self.expect("KEYWORD", "then")
            true_body = self.parse_block()
            
            else_ifs = []
            while self.match("KEYWORD", "elseif"):
                elif_cond = self.parse_expr()
                self.expect("KEYWORD", "then")
                elif_body = self.parse_block()
                else_ifs.append((elif_cond, elif_body))
                
            false_body = None
            if self.match("KEYWORD", "else"):
                false_body = self.parse_block()
                
            self.expect("KEYWORD", "end")
            return IfStmt(line, cond, true_body, else_ifs, false_body)
            
        if self.match("KEYWORD", "repeat"):
            if self.match("KEYWORD", "forever"):
                count = None
            elif self.peek().value == "end":
                count = None
            else:
                count = self.parse_expr()
            body = self.parse_block()
            self.expect("KEYWORD", "end")
            return RepeatStmt(line, count, body)
            
        if self.match("KEYWORD", "for"):
            var1 = self.expect("IDENT").value
            self.expect("PUNC", ",")
            var2 = self.expect("IDENT").value
            self.expect("KEYWORD", "in")
            
            iter_tok = self.match("KEYWORD", "pairs") or self.match("KEYWORD", "ipairs")
            if not iter_tok:
                raise ParseError(f"expected 'pairs' or 'ipairs', got {self.peek().value!r} at line {line}")
            
            self.expect("PUNC", "(")
            table_expr = self.parse_expr()
            self.expect("PUNC", ")")
            self.expect("KEYWORD", "do")
            
            body = self.parse_block()
            self.expect("KEYWORD", "end")
            return ForStmt(line, [var1, var2], table_expr, body)
            
        if self.match("KEYWORD", "break"):
            return BreakStmt(line)
            
        if self.match("KEYWORD", "return"):
            val = None
            if self.peek().line == line and self.peek().value not in ("end", "else", "elseif"):
                val = self.parse_expr()
            return ReturnStmt(line, val)
            
        if self.match("KEYWORD", "delete"):
            target = self.parse_postfix()
            return DeleteStmt(line, target)

        scope = None
        if self.peek().value in ("local", "global", "object"):
            scope = self.consume().value
            
        is_bg = bool(self.match("KEYWORD", "bg") or self.match("IDENT", "background"))
        
        targets = [self.parse_postfix()]
        while self.match("PUNC", ","):
            targets.append(self.parse_postfix())
            
        is_protected = False
        if self.match("OP", "="):
            if self.match("KEYWORD", "protected"):
                is_protected = True
            
            val = self.parse_expr()
            if isinstance(val, CallStmt):
                val.targets = targets
                val.is_protected = is_protected
                val.scope = scope
                return val
            else:
                return AssignStmt(line, scope, targets, val, "=")
                
        elif self.peek().type == "OP" and self.peek().value in ("+=", "-=", "*=", "/=", "^=", "%="):
            op = self.consume().value
            val = self.parse_expr()
            return AssignStmt(line, scope, targets, val, op)
            
        if len(targets) == 1 and isinstance(targets[0], CallStmt):
            targets[0].is_bg = is_bg
            return targets[0]
            
        raise ParseError(f"unexpected statement at line {line}: {self.peek().value}")

    def parse_expr(self, precedence=0):
        line = self.peek().line
        
        if self.peek().type == "OP" and self.peek().value in ("-", "#"):
            op = self.consume().value
            left = UnaryExpr(line, op, self.parse_expr(7))
        elif self.match("KEYWORD", "not"):
            left = UnaryExpr(line, "not", self.parse_expr(7))
        else:
            left = self.parse_primary()
            
        left = self.parse_postfix(left)
            
        op_prec = {
            "or": 1, "nor": 1, "xor": 1,
            "and": 2,
            "==": 3, "~=": 3, ">": 3, ">=": 3, "<": 3, "<=": 3, "contains": 3, "not contains": 3,
            "..": 4,
            "+": 5, "-": 5,
            "*": 6, "/": 6, "%": 6,
            "^": 7
        }
        
        while True:
            op_tok = self.peek()
            op = op_tok.value
            
            if op == "not" and self.peek(1).value == "contains":
                op = "not contains"
            
            if op_tok.type in ("KEYWORD", "OP") and op in op_prec:
                prec = op_prec[op]
            else:
                break
                
            if prec < precedence:
                break
                
            if op == "not contains":
                self.consume()
                self.consume()
            else:
                self.consume()
                
            next_prec = prec if op == "^" else prec + 1
            right = self.parse_expr(next_prec)
            left = BinaryExpr(line, left, op, right)
            
        return left

    def parse_primary(self):
        line = self.peek().line
        tok = self.consume()
        
        if tok.type == "NUMBER":
            return NumberLit(line, float(tok.value) if '.' in tok.value else int(tok.value))
        elif tok.type == "STRING":
            return StringLit(line, tok.value)
        elif tok.type == "INTERP_STR":
            return InterpStringLit(line, tok.value)
        elif tok.type == "IDENT":
            prefix = None
            name = tok.value
            if name.startswith("l!") or name.startswith("g!") or name.startswith("o!"):
                prefix = name[:2]
                name = name[2:]
            return VarRef(line, name, prefix)
        elif tok.type == "KEYWORD" and tok.value == "nil":
            return VarRef(line, "nil")
        elif tok.type == "PUNC" and tok.value == "{":
            self.expect("PUNC", "}")
            return TableLit(line)
        elif tok.type == "PUNC" and tok.value == "(":
            expr = self.parse_expr()
            self.expect("PUNC", ")")
            return expr
            
        raise ParseError(f"unexpected primary token {tok.value!r} at line {line}")

    def parse_postfix(self, left=None):
        if left is None:
            left = self.parse_primary()
            
        while True:
            line = self.peek().line
            if self.match("PUNC", "."):
                prop = self.expect("IDENT").value
                left = PropRef(line, left, prop)
            elif self.match("PUNC", "["):
                index = self.parse_expr()
                self.expect("PUNC", "]")
                left = IndexRef(line, left, index)
            elif self.match("PUNC", "("):
                args = []
                if not self.match("PUNC", ")"):
                    args.append(self.parse_expr())
                    while self.match("PUNC", ","):
                        args.append(self.parse_expr())
                    self.expect("PUNC", ")")
                left = CallStmt(line, is_bg=False, func_expr=left, args=args, targets=[], is_protected=False)

            elif self.match("PUNC", ":"):
                method_name = self.expect("IDENT").value
                self.expect("PUNC", "(")
                
                # inject 'left' as the first argument
                args = [left]
                if not self.match("PUNC", ")"):
                    args.append(self.parse_expr())
                    while self.match("PUNC", ","):
                        args.append(self.parse_expr())
                    self.expect("PUNC", ")")
                
                # route string methods back to string library, leave others as global calls
                string_methods = {"lower", "upper", "sub", "gsub", "len", "split"}
                if method_name in string_methods:
                    func_expr = PropRef(line, VarRef(line, "string"), method_name)
                else:
                    func_expr = VarRef(line, method_name)
                    
                left = CallStmt(line, is_bg=False, func_expr=func_expr, args=args, targets=[], is_protected=False)
            else:
                break
                
        return left