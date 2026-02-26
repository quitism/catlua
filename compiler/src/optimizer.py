from ast_nodes import *

class Optimizer:
    def __init__(self, ast):
        self.ast = ast
        self.read_counts = {}

    def count_reads(self, node):
        if node is None: return

        if type(node).__name__ == "VarRef":
            name = node.name
            self.read_counts[name] = self.read_counts.get(name, 0) + 1

        if type(node).__name__ in ("StringLit", "InterpStringLit"):
            import re

            matches = re.findall(r"\{(?:[lgo]!)?([a-zA-Z_]\w*)", str(node.value))
            for var_name in matches:
                self.read_counts[var_name] = self.read_counts.get(var_name, 0) + 1

        for key, value in vars(node).items():

            if key == "targets" and type(node).__name__ == "AssignStmt": continue

            if isinstance(value, list):
                for item in value:
                    if hasattr(item, '__dict__'): self.count_reads(item)
            elif hasattr(value, '__dict__'):
                self.count_reads(value)

    def has_function_call(self, node):
        # recursively check if an expression has a function call inside it
        if isinstance(node, CallStmt): return True
        if hasattr(node, '__dict__'):
            for key, value in vars(node).items():
                if isinstance(value, list):
                    if any(self.has_function_call(item) for item in value): return True
                else:
                    if self.has_function_call(value): return True
        return False

    def eliminate_dead_code(self, node):
        if node is None: return
        
        # if this node has a block of statements (like a function body or if-statement)
        for attr in ['body', 'true_body', 'false_body']:
            block = getattr(node, attr, None)
            if isinstance(block, list):
                new_block = []
                for i, stmt in enumerate(block):
                    # DCE
                    if isinstance(stmt, AssignStmt) and stmt.scope == "local":
                        target = stmt.targets[0]
                        if isinstance(target, VarRef):
                            reads = self.read_counts.get(target.name, 0)
                            # if it's never read, and the right side has no side-effects (like a function call)
                            if reads == 0 and not self.has_function_call(stmt.value):
                                print(f"[optimizer (-O2)] eliminated dead variable '{target.name}' at line {stmt.line}")
                                continue # it gets deleted
                    
                    self.eliminate_dead_code(stmt)
                    new_block.append(stmt)

                    if isinstance(stmt, ReturnStmt) or isinstance(stmt, BreakStmt):
                        # if we return, anything after is dead code
                        if i + 1 < len(block):
                            dropped = len(block) - (i + 1)
                            print(f"[optimizer (-O2)] eliminated {dropped} unreachable statement(s) after return statement at line {stmt.line}")
                        break
                    
                setattr(node, attr, new_block)

        # recursively check else-ifs and other shards
        if hasattr(node, 'else_ifs'):
            for cond, body in node.else_ifs:
                self.eliminate_dead_code(body) # we pass body as a dummy object if needed, or just iterate its stmts
                # (simplified)
                
        if hasattr(node, '__dict__'):
            for key, value in vars(node).items():
                if isinstance(value, list) and key not in ['body', 'true_body', 'false_body']:
                    for item in value:
                        if hasattr(item, '__dict__'): self.eliminate_dead_code(item)
                elif hasattr(value, '__dict__') and key not in ['body', 'true_body', 'false_body']:
                    self.eliminate_dead_code(value)

    def optimize(self, colors_class=None):
        self.Colors = colors_class
        self.count_reads(self.ast)
        self.eliminate_dead_code(self.ast)