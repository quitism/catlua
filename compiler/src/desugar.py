from ast_nodes import *

class Desugarer:
    def __init__(self, ast):
        self.ast = ast

    def desugar_block(self, block):
        if not isinstance(block, list): return block
        
        new_block = []
        for stmt in block:
            for attr in ['body', 'true_body', 'false_body']:
                inner = getattr(stmt, attr, None)
                if isinstance(inner, list):
                    setattr(stmt, attr, self.desugar_block(inner))
                    
            if hasattr(stmt, 'else_ifs'):
                new_else_ifs = []
                for cond, e_body in stmt.else_ifs:
                    new_else_ifs.append((cond, self.desugar_block(e_body)))
                stmt.else_ifs = new_else_ifs

            if type(stmt).__name__ == "AssignStmt" and type(stmt.value).__name__ == "BinaryExpr" and stmt.value.op == "or":
                target_var = stmt.targets[0]
                
                base_assign = AssignStmt(stmt.line, stmt.targets, stmt.value.left, getattr(stmt, 'scope', ''))
                
                fallback_assign = AssignStmt(stmt.line, stmt.targets, stmt.value.right, "")
                
                cond = UnaryExpr(stmt.line, "not", target_var)
                
                if_stmt = IfStmt(stmt.line, cond, [fallback_assign], [], None)
                
                new_block.append(base_assign)
                new_block.append(if_stmt)
                
            else:
                new_block.append(stmt)
                
        return new_block

    def process(self):
        for shard in self.ast.shards:
            for func in shard.func_defs:
                func.body = self.desugar_block(func.body)
            for event in shard.events:
                event.body = self.desugar_block(event.body)
        
        return self.ast