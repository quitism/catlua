import sys
import os
import json
import re
from lexer import Lexer, LexerError
from parser import Parser, ParseError
from semantic import SemanticAnalyzer
from ir_emitter import IREmitter
from optimizer import Optimizer
from ast_nodes import ScriptNode

# try to grab the JSON emitter
try:
    from emitter import emit
except (ImportError, ModuleNotFoundError):
    emit = None
    class EmitError(Exception):
        pass

class Colors:
    RED = '\033[91m'
    YELLOW = '\033[93m'
    GREEN = '\033[92m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    RESET = '\033[0m'

def main():
    if len(sys.argv) < 2:
        print(f"{Colors.BOLD}usage:{Colors.RESET} python main.py <file.catlua> [-o output.json] [--ir] [-O0|-O1|-O2]")
        sys.exit(1)

    filename = sys.argv[1]
    
    with open(filename, 'r', encoding='utf-8') as f:
        code = f.read()

    # linter setup
    is_linting = "--lint" in sys.argv
    lint_diagnostics = []

    def add_diagnostic(msg, fallback_line=1, severity="error"):
        msg_str = str(msg)
        extracted_line = fallback_line
        
        match = re.search(r"line\s*(\d+)", msg_str, re.IGNORECASE)
        if match:
            extracted_line = int(match.group(1))
            
        clean_msg = re.sub(r"^(Error|Warning|Parse Error|Lexer Error).*?line\s*\d+\)?:\s*", "", msg_str, flags=re.IGNORECASE).strip()
        
        lint_diagnostics.append({
            "line": extracted_line,
            "msg": clean_msg,
            "severity": severity
        })

    # recursive multi-file linker
    def compile_file(filepath, parsed_files=None):
        if parsed_files is None:
            parsed_files = set()
            
        abs_path = os.path.abspath(filepath)
        if abs_path in parsed_files:
            return []
        parsed_files.add(abs_path)
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                file_code = f.read()
                
            lexer = Lexer(file_code)
            tokens = lexer.tokenize()
            
            parser = Parser(tokens)
            ast = parser.parse()
            
            if parser.errors:
                for err in parser.errors:
                    if is_linting:
                        add_diagnostic(err, 1)
                    else:
                        print(f"{Colors.RED}[ERROR] Syntax in {os.path.basename(filepath)}: {err}{Colors.RESET}")
                
                if not is_linting:
                    sys.exit(1)
                
        except (LexerError, ParseError) as e:
            if is_linting:
                add_diagnostic(str(e), 1)
                print(json.dumps(lint_diagnostics))
                sys.exit(0)
            else:
                print(f"{Colors.RED}[ERROR] Syntax in {os.path.basename(filepath)}: {e}{Colors.RESET}")
                sys.exit(1)
                
        final_shards = []
        base_dir = os.path.dirname(abs_path)
        
        for shard in ast.shards:
            final_shards.append(shard)
            for req in shard.requires:
                req_path = os.path.join(base_dir, req)
                if not os.path.exists(req_path) and os.path.exists(req_path + ".catlua"):
                    req_path += ".catlua"
                    
                if not os.path.exists(req_path):
                    if is_linting: continue
                    print(f"{Colors.RED}[ERROR] Linker: Could not find required file '{req}'{Colors.RESET}")
                    sys.exit(1)
                    
                final_shards.extend(compile_file(req_path, parsed_files))
                
        return final_shards

    # lex, parse and link
    all_shards = compile_file(filename)
    ast = ScriptNode(1, all_shards)

    # desugaring pass
    from desugar import Desugarer
    ast = Desugarer(ast).process()

    # optimization pass
    opt_level = 1 # default: constant folding
    if "-O0" in sys.argv: opt_level = 0
    if "-O2" in sys.argv: opt_level = 2

    # analysis
    analyzer = SemanticAnalyzer(ast, opt_level=opt_level)
    errors, warnings = analyzer.analyze()

    # DCE
    if opt_level >= 2:
        opt = Optimizer(ast)
        # Only pass Colors if we aren't linting (keeps stdout clean for VS Code)
        opt.optimize(Colors if not is_linting else None)
    
    # linter json output
    if is_linting:
        for w in warnings: add_diagnostic(w, 1, "warning")
        for e in errors: add_diagnostic(e, 1, "error")
        print(json.dumps(lint_diagnostics))
        sys.exit(0)
    
    # pretty printing
    if warnings:
        print(f"\n{Colors.BOLD}{Colors.YELLOW}=== WARNINGS ==={Colors.RESET}")
        for w in warnings: print(f"{Colors.YELLOW}⚠ {w}{Colors.RESET}")
        
    if errors:
        print(f"\n{Colors.BOLD}{Colors.RED}=== COMPILATION FAILED ==={Colors.RESET}")
        for e in errors: print(f"{Colors.RED}✖ {e}{Colors.RESET}")
        sys.exit(1)
        
    print(f"{Colors.BOLD}{Colors.GREEN}analysis passed{Colors.RESET}")

    # ir emitter
    ir_gen = IREmitter(ast, analyzer)
    cwir_output = ir_gen.emit()
    
    if "--ir" in sys.argv:
        print(f"\n{Colors.BOLD}{Colors.BLUE}=== CWIR ==={Colors.RESET}")
        print(cwir_output)

    # json export
    out_file = None
    if "-o" in sys.argv:
        idx = sys.argv.index("-o")
        if idx + 1 < len(sys.argv):
            out_file = sys.argv[idx + 1]
            
    if not out_file:
        base = os.path.splitext(filename)[0]
        out_file = f"{base}.json"

    if emit:
        try:
            final_json = emit(cwir_output)
            with open(out_file, 'w', encoding='utf-8') as f:
                f.write(final_json)
            print(f"\n{Colors.BOLD}{Colors.GREEN}compiled {filename} -> {out_file} successfully{Colors.RESET}")
        except EmitError as e:
            print(f"\n{Colors.RED}JSON Emitter Error: {e}{Colors.RESET}")
            sys.exit(1)
    else:
        cwobj_file = out_file.replace(".json", ".cwobj")
        with open(cwobj_file, 'w', encoding='utf-8') as f:
            f.write(cwir_output)
        print(f"\n{Colors.YELLOW}[WARN] emitter.py not found. saved raw IR to {cwobj_file} instead.{Colors.RESET}")

if __name__ == "__main__":
    main()