from ast_nodes import *

class SemanticAnalyzer:
    SERVICES = {"UserInputService", "LocalPlayer", "Camera"}

    BUILTINS = {
    "print", "warn", "error", "wait", "task",
    "string", "math", "table", "os", "server",
    "makeVisible", "makeInvisible", "redirect",
    "playAudio", "playLoopedAudio", "stopAllAudio",
    "getUrl", "getQuery", "getTimezone", "tick",
    "formatLocalTime", "formatUniversalTime",
    "hexToRGB", "hexToHSV", "RGBToHex", "HSVToHex", "lerpColor",
    "findFirstChild", "findFirstAncestor", "findFirstDescendant",
    "getChildren", "getDescendants", "getObjectsAtPosition",
    "setImage", "setHeadshot", "getAssetInfo", "tween",
    "clone", "destroy", "darkTheme", "keyDown",
    "leftMouseDown", "middleMouseDown", "rightMouseDown",
    "Camera", "LocalPlayer", "UserInputService", "page", "site", "crossSite",
    "protected", "bg", "background"
    }

    LIBRARIES = {
        "string.", "math.", "table.", "os.", "cookie", "server."
    }
    def __init__(self, ast, opt_level=1):
        self.ast = ast
        self.opt_level = opt_level
        self.globals = set()
        self.objects = set()
        self.funcs = {}
        
        self.locals = set()
        self.in_loop = 0
        self.action_count = 0
        self.errors = []
        self.warnings = []

    def collect_aliases(self):
        self.aliases = {}
        self.alias_lines = {}
        for shard in self.ast.shards:
            for event in shard.events:
                for stmt in event.body:
                    if isinstance(stmt, AssignStmt) and len(stmt.targets) == 1:
                        target = stmt.targets[0]
                        value = stmt.value
                        if isinstance(target, VarRef) and isinstance(value, VarRef):
                            if value.name in self.SERVICES:
                                if value.name in self.aliases:
                                    self.warn(stmt.line, f"'{value.name}' remapped more than once")
                                self.aliases[value.name] = target.name
                                self.alias_lines[value.name] = stmt.line

    def _resolve_target(self, target, scope, line):
        if not isinstance(target, VarRef):
            self.visit(target)
            return
            
        name = target.name
        
        if scope and target.prefix:
            expected = {'local': 'l!', 'global': 'g!', 'object': 'o!'}[scope]
            if target.prefix != expected:
                self.warn(line, f"prefix '{target.prefix}' conflicts with scope keyword '{scope}', stripping prefix")
            target.prefix = None

        active_scope = scope
        if not active_scope and target.prefix:
            active_scope = {'l!': 'local', 'g!': 'global', 'o!': 'object'}.get(target.prefix)

        if active_scope == "local":
            if name in self.locals and scope == "local":
                self.error(line, f"'{name}' already declared as local, use l!{name} = ... to reassign")
            self.locals.add(name)
            target.prefix = 'l!'
        elif active_scope == "object":
            if name in self.objects and scope == "object":
                self.error(line, f"'{name}' already declared as object, use o!{name} = ... to reassign")
            self.objects.add(name)
            target.prefix = 'o!'
        elif active_scope == "global":
            self.globals.add(name)
            target.prefix = 'g!'
        else:
            if name in self.globals:
                pass
            elif name in self.locals or name in self.objects:
                self.warn(line, f"bare assignment to '{name}', did you mean l!{name} or o!{name}?")
            else:
                self.globals.add(name)
            target.prefix = 'g!'

    def fold_constants(self, expr):
        if type(expr).__name__ != "BinaryExpr":
            return expr
            
        expr.left = self.fold_constants(expr.left)
        expr.right = self.fold_constants(expr.right)
        
        if type(expr.left).__name__ == "NumberLit" and type(expr.right).__name__ == "NumberLit":
            try:
                left_val = float(expr.left.value)
                right_val = float(expr.right.value)
                result = None
                
                if expr.op == "+": result = left_val + right_val
                elif expr.op == "-": result = left_val - right_val
                elif expr.op == "*": result = left_val * right_val
                elif expr.op == "/": result = left_val / right_val if right_val != 0 else None
                elif expr.op == "^": result = left_val ** right_val
                elif expr.op == "%": result = left_val % right_val if right_val != 0 else None
                
                if result is not None:
                    res_str = str(int(result)) if result.is_integer() else str(result)
                    
                    return NumberLit(expr.line, res_str)
            except Exception:
                pass # if math fails for some weird reason, just abort folding
                
        return expr

    def error(self, line, msg):
        self.errors.append(f"Error (line {line}): {msg}")

    def warn(self, line, msg):
        self.warnings.append(f"Warning (line {line}): {msg}")

    def analyze(self):
        self.collect_aliases()
        for shard in self.ast.shards:
            for func in shard.func_defs:
                
                if func.name in self.funcs:
                    self.warn(func.line, f"duplicate function '{func.name}' declared")
                if len(func.params) > 6:
                    self.error(func.line, f"function '{func.name}' exceeds max 6 arguments")
                self.funcs[func.name] = func.params

        for shard in self.ast.shards:
            for event in shard.events:
                self.analyze_event(event)
                
            for func in shard.func_defs:
                self.locals = set(func.params)
                self.action_count = 0
                self.in_loop = 0
                self.visit_block(func.body)

        return self.errors, self.warnings

    def analyze_event(self, event):
        self.locals = set()
        self.action_count = 0
        self.in_loop = 0
        
        # hidden locals based on event type
        if event.event_type == "OnMessageReceived":
            self.locals.update(["messageContent", "messageSenderId", "messageSenderName"])
        elif event.event_type == "OnCrossSiteMessageReceived":
            self.locals.update(["sourceDomain", "messageContent", "messageSenderId", "messageSenderName"])
        elif "GetPropertyChangedSignal" in event.event_type:
            self.locals.add("propertyChanged")
            
        self.visit_block(event.body)

    def visit_block(self, stmts):
        for stmt in stmts:
            self.action_count += 1
            if self.action_count == 121:
                self.warn(stmt.line, "action limit exceeded (120 per event). further actions may not compile or run correctly.")
            self.visit(stmt)

    def visit(self, node):
        if node is None:
            return
        method_name = 'visit_' + type(node).__name__
        visitor = getattr(self, method_name, self.generic_visit)
        visitor(node)

    def generic_visit(self, node):
        for key, value in vars(node).items():
            if isinstance(value, list):
                for item in value:
                    if hasattr(item, '__dict__'):
                        self.visit(item)
            elif hasattr(value, '__dict__'):
                self.visit(value)

    def visit_IfStmt(self, node):
        self.visit(node.condition)
        self.visit_block(node.true_body)
        
        for elif_cond, elif_body in node.else_ifs:
            self.visit(elif_cond)
            self.visit_block(elif_body)
            
        if node.false_body:
            self.visit_block(node.false_body)

    def visit_AssignStmt(self, node):
        if getattr(node, 'value', None):
            if self.opt_level >= 1:
                node.value = self.fold_constants(node.value)
            self.visit(node.value)
        for target in node.targets:
            self._resolve_target(target, node.scope, node.line)

    def visit_VarRef(self, node):
        if node.name == "nil":
            return
        if node.name in self.aliases:
            if node.line != self.alias_lines.get(node.name):
                self.error(node.line, f"'{node.name}' has been remapped to '{self.aliases[node.name]}', use '{self.aliases[node.name]}' instead")
            return
            
        active_prefix = node.prefix
        if not active_prefix:
            if node.name not in self.globals and node.name not in self.locals and node.name not in self.objects:
                self.warn(node.line, f"'{node.name}' not declared, assuming global")
                node.prefix = 'g!'
            elif node.name in self.globals:
                node.prefix = 'g!'
            elif node.name in self.locals and node.name not in self.globals:
                node.prefix = 'l!'
            elif node.name in self.objects and node.name not in self.globals:
                node.prefix = 'o!'
            else:
                node.prefix = 'g!'
        else:
            # explicit prefix used, verify it exists
            if active_prefix == 'l!' and node.name not in self.locals:
                self.warn(node.line, f"l!{node.name} not declared in local scope")
            elif active_prefix == 'o!' and node.name not in self.objects:
                self.warn(node.line, f"o!{node.name} not declared in object scope")

    def visit_ForStmt(self, node):
        self.visit(node.iterator)
        for var in node.vars:
            self.locals.add(var)
            
        self.in_loop += 1
        self.visit_block(node.body)
        self.in_loop -= 1

    def visit_RepeatStmt(self, node):
        if node.count:
            self.visit(node.count)
        self.in_loop += 1
        self.visit_block(node.body)
        self.in_loop -= 1

    def visit_BreakStmt(self, node):
        if self.in_loop <= 0:
            self.warn(node.line, "break statement used outside of a loop")

    def visit_CallStmt(self, node):
            for target in getattr(node, 'targets', []):
                self._resolve_target(target, getattr(node, 'scope', None), node.line)

            func_name = None
            if isinstance(node.func_expr, VarRef):
                func_name = node.func_expr.name
            elif isinstance(node.func_expr, PropRef) and isinstance(node.func_expr.obj, VarRef):
                func_name = node.func_expr.obj.name # this gets "string" from "string.lower"

            is_known = (
                func_name in self.funcs or 
                func_name in self.BUILTINS or 
                func_name in self.SERVICES
            )

            if func_name and not is_known:
                self.visit(node.func_expr)
            elif isinstance(node.func_expr, PropRef) and not func_name:
                # handle cases like (get_stuff()).method()
                self.visit(node.func_expr.obj)

            if func_name in self.funcs:
                if len(node.args) > len(self.funcs[func_name]):
                    self.warn(node.line, f"too many arguments passed to '{func_name}'")

            for arg in node.args:
                arg = self.fold_constants(arg)
                self.visit(arg)

    def visit_PropRef(self, node):
        if isinstance(node.obj, VarRef):
            name = node.obj.name
            
            is_known = (
                name in self.BUILTINS or 
                name in self.SERVICES or 
                name.startswith(tuple(self.LIBRARIES))
            )
            
            if is_known:
                return

        self.visit(node.obj)