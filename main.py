"""
VibeLang - A statically-typed language compiler
Command-line interface
"""

import sys
import argparse
from src.compiler import Compiler
from src.vm import VibeLangVM
from src.errors import VibeLangError


def run_file(filename: str, debug: bool = False):
    """Compile and run a VibeLang source file."""
    try:
        compiler = Compiler()
        bytecode = compiler.compile_file(filename)
        
        if debug:
            print(bytecode.disassemble())
            print("\n=== Execution ===")
        
        vm = VibeLangVM(bytecode, debug=debug)
        result = vm.run()
        
        if result is not None and debug:
            print(f"\n=== Result: {result} ===")
    
    except VibeLangError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print(f"Error: File not found: {filename}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Internal error: {e}", file=sys.stderr)
        if debug:
            raise
        sys.exit(1)


def run_repl():
    """Run interactive REPL."""
    print("VibeLang REPL v1.0")
    print("Type 'exit' to quit\n")
    
    compiler = Compiler()
    
    while True:
        try:
            line = input(">>> ")
            if line.strip() in ['exit', 'quit']:
                break
            
            if not line.strip():
                continue
            
            # Wrap in a simple program structure
            source = line
            
            bytecode = compiler.compile(source)
            vm = VibeLangVM(bytecode)
            result = vm.run()
            
            if result is not None:
                print(result)
        
        except VibeLangError as e:
            print(f"Error: {e}")
        except EOFError:
            break
        except KeyboardInterrupt:
            print("\nInterrupted")
            break
        except Exception as e:
            print(f"Internal error: {e}")


def compile_file(input_file: str, output_file: str):
    """Compile source file to bytecode file."""
    try:
        compiler = Compiler()
        bytecode = compiler.compile_file(input_file)
        
        # Serialize and write bytecode
        with open(output_file, 'wb') as f:
            f.write(bytecode.serialize())
        
        print(f"Compiled {input_file} -> {output_file}")
    
    except VibeLangError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Internal error: {e}", file=sys.stderr)
        sys.exit(1)


def compile_to_c(input_file: str, output_file: str):
    """Compile VibeLang to C code."""
    try:
        from src.codegen_c import CCodeGenerator
        
        compiler = Compiler()
        compiler.compile_file(input_file, skip_bytecode=True)
        
        # Generate C code from typed AST
        c_gen = CCodeGenerator()
        other_programs = [ast for path, ast in compiler.module_cache.items() if ast != compiler.ast]
        c_code = c_gen.generate(compiler.ast, other_programs)
        
        # Write C code
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(c_code)
        
        print(f"Generated C code: {input_file} -> {output_file}")
        print(f"Compile with: gcc -o output {output_file}")
    
    except VibeLangError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Internal error: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='VibeLang Compiler and Runtime')
    parser.add_argument('file', nargs='?', help='Source file to run')
    parser.add_argument('-c', '--compile', metavar='OUTPUT', help='Compile to bytecode file')
    parser.add_argument('--emit-c', metavar='OUTPUT', help='Generate C code')
    parser.add_argument('-d', '--debug', action='store_true', help='Enable debug output')
    parser.add_argument('-r', '--repl', action='store_true', help='Start REPL')
    
    args = parser.parse_args()
    
    if args.repl or (not args.file and not args.compile and not args.emit_c):
        run_repl()
    elif args.emit_c:
        if not args.file:
            print("Error: Input file required for C code generation", file=sys.stderr)
            sys.exit(1)
        compile_to_c(args.file, args.emit_c)
    elif args.compile:
        if not args.file:
            print("Error: Input file required for compilation", file=sys.stderr)
            sys.exit(1)
        compile_file(args.file, args.compile)
    elif args.file:
        run_file(args.file, debug=args.debug)
    else:
        parser.print_help()



if __name__ == '__main__':
    main()
