class Node:
    def __init__(self, line):
        self.line = line
        self.force_builtin = False
        self.force_custom = False
        self.annotations = {}

class ScriptShardNode:
    def __init__(self, alias=""):
        self.alias = alias
        self.events = []
        self.func_defs = []
        self.requires = []

class ScriptNode(Node):
    def __init__(self, line, shards):
        super().__init__(line)
        self.shards = shards

class EventNode(Node):
    def __init__(self, line, event_type, args, body):
        super().__init__(line)
        self.event_type = event_type
        self.args = args
        self.body = body

class FuncDefNode(Node):
    def __init__(self, line, name, params, body):
        super().__init__(line)
        self.name = name
        self.params = params
        self.body = body

class AssignStmt(Node):
    def __init__(self, line, scope, targets, value, op="="):
        super().__init__(line)
        self.scope = scope
        self.targets = targets
        self.value = value
        self.op = op

class IfStmt(Node):
    def __init__(self, line, condition, true_body, else_ifs, false_body):
        super().__init__(line)
        self.condition = condition
        self.true_body = true_body
        self.else_ifs = else_ifs
        self.false_body = false_body

class RepeatStmt(Node):
    def __init__(self, line, count, body):
        super().__init__(line)
        self.count = count
        self.body = body

class ForStmt(Node):
    def __init__(self, line, vars, iterator, body):
        super().__init__(line)
        self.vars = vars
        self.iterator = iterator
        self.body = body

class CallStmt(Node):
    def __init__(self, line, is_bg, func_expr, args, targets, is_protected, scope=None):
        super().__init__(line)
        self.is_bg = is_bg
        self.func_expr = func_expr
        self.args = args
        self.targets = targets
        self.is_protected = is_protected
        self.scope = scope

class ReturnStmt(Node):
    def __init__(self, line, value):
        super().__init__(line)
        self.value = value

class BreakStmt(Node):
    pass

class DeleteStmt(Node):
    def __init__(self, line, target):
        super().__init__(line)
        self.target = target

class PropertySet(Node):
    def __init__(self, line, obj, prop, value):
        super().__init__(line)
        self.obj = obj
        self.prop = prop
        self.value = value

class IndexSet(Node):
    def __init__(self, line, table, index, value, is_object_ref=False):
        super().__init__(line)
        self.table = table
        self.index = index
        self.value = value
        self.is_object_ref = is_object_ref

class BinaryExpr(Node):
    def __init__(self, line, left, op, right):
        super().__init__(line)
        self.left = left
        self.op = op
        self.right = right

class UnaryExpr(Node):
    def __init__(self, line, op, right):
        super().__init__(line)
        self.op = op
        self.right = right

class VarRef(Node):
    def __init__(self, line, name, prefix=None):
        super().__init__(line)
        self.name = name
        self.prefix = prefix

class PropRef(Node):
    def __init__(self, line, obj, prop):
        super().__init__(line)
        self.obj = obj
        self.prop = prop

class IndexRef(Node):
    def __init__(self, line, table, index):
        super().__init__(line)
        self.table = table
        self.index = index

class NumberLit(Node):
    def __init__(self, line, value):
        super().__init__(line)
        self.value = value

class StringLit(Node):
    def __init__(self, line, value):
        super().__init__(line)
        self.value = value

class InterpStringLit(Node):
    def __init__(self, line, value):
        super().__init__(line)
        self.value = value

class TableLit(Node):
    def __init__(self, line):
        super().__init__(line)

class CommentStmt(Node):
    def __init__(self, line, value):
        super().__init__(line)
        self.value = value