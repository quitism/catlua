import re

class Token:
    def __init__(self, type, value, line, column):
        self.type = type
        self.value = value
        self.line = line
        self.column = column

    def __repr__(self):
        return f"Token({self.type}, {repr(self.value)}, line={self.line})"

KEYWORDS = {
    "local", "global", "object", "if", "then", "elseif", "else", "end",
    "repeat", "forever", "break", "for", "in", "ipairs", "pairs", "do", "function",
    "return", "delete", "and", "or", "nor", "xor", "not", "protected", "bg", "nil", "contains"
}

TOKEN_SPEC = [
    ("ANNOTATION", r"--[@#]\s*[^\n]*"),
    ("COMMENT", r"--.*"),
    ("NUMBER", r"\d+(\.\d+)?"),
    ("INTERP_STR", r"`[^`]*`"),
    ("STRING", r'"[^"]*"|\'[^\']*\''),
    ("IDENT", r"(?:[glo]!)?[a-zA-Z_]\w*"),
    ("OP", r"==|~=|>=|<=|\+=|-=|\*=|/=|\^=|%=|[\+\-\*/\^%=<>#]|(\.\.)"), 
    ("PUNC", r"[\(\)\[\]\{\}\.,:]"),
    ("WS", r"[ \t]+"),
    ("NEWLINE", r"\n"),
    ("MISMATCH", r"."),
]

class LexerError(Exception):
    pass

class Lexer:
    def __init__(self, code):
        self.code = code
        self.tokens = []
        self.regex = "|".join(f"(?P<{pair[0]}>{pair[1]})" for pair in TOKEN_SPEC)
        self.line = 1
        self.line_start = 0

    def tokenize(self):
        for mo in re.finditer(self.regex, self.code):
            kind = mo.lastgroup
            value = mo.group(kind) if kind else mo.group(0)
            column = mo.start() - self.line_start

            if kind == "NEWLINE":
                self.line += 1
                self.line_start = mo.end()
                continue
            elif kind == "WS":
                continue
            elif kind == "COMMENT":
                value = value[2:].strip()
                self.tokens.append(Token(kind, value, self.line, column))
                continue
            elif kind == "MISMATCH":
                raise LexerError(f"unexpected char {value!r} at line {self.line}, col {column}")
            elif kind == "IDENT" and value in KEYWORDS:
                kind = "KEYWORD"
            elif kind == "STRING":
                value = value[1:-1]
            elif kind == "INTERP_STR":
                value = value[1:-1]

            self.tokens.append(Token(kind, value, self.line, column))
            
        self.tokens.append(Token("EOF", "", self.line, len(self.code) - self.line_start))
        return self.tokens