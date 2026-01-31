"""
Main compiler driver for VibeLang.
Orchestrates the compilation pipeline.
"""

from typing import Optional
from .lexer import Lexer
from .parser import Parser
from .type_checker import TypeChecker
from .codegen import CodeGenerator
from .bytecode import Bytecode
from .ast_nodes import Program


class Compiler:
    """VibeLang compiler."""
    
    def __init__(self):
        self.source = None
        self.tokens = None
        self.ast = None
        self.bytecode = None
        self.module_cache = {}  # path -> Program AST
    
    def compile(self, source: str, skip_bytecode: bool = False, filename: str = "<strings>") -> Optional[Bytecode]:
        """Compile source code to AST, and optionally to bytecode."""
        self.source = source
        
        # Lexical analysis
        lexer = Lexer(source)
        self.tokens = lexer.tokenize()
        
        # Parsing
        parser = Parser(self.tokens)
        self.ast = parser.parse()
        
        # Type checking
        type_checker = TypeChecker()
        # Provide a way for the type checker to resolve modules
        type_checker.module_resolver = self.resolve_module
        import os
        type_checker.current_file = os.path.abspath(filename)
        type_checker.check_program(self.ast)
        
        if skip_bytecode:
            return None
            
        # Code generation
        code_generator = CodeGenerator()
        other_programs = [ast for path, ast in self.module_cache.items() if ast != self.ast]
        self.bytecode = code_generator.generate(self.ast, other_programs)
        
        return self.bytecode
    
    def resolve_module(self, path: str, current_file: str) -> Program:
        """Resolve an imported module path and return its AST."""
        import os
        
        # Append .vibe extension if not present
        if not path.endswith('.vibe'):
            path += '.vibe'
            
        # Resolve path relative to current file
        base_dir = os.path.dirname(os.path.abspath(current_file))
        full_path = os.path.normpath(os.path.join(base_dir, path))
        
        if full_path in self.module_cache:
            return self.module_cache[full_path]
        
        if not os.path.exists(full_path):
            raise Exception(f"Module not found: {path} (resolved to {full_path})")
            
        with open(full_path, 'r', encoding='utf-8') as f:
            source = f.read()
            
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        
        # Store with absolute path
        self.module_cache[full_path] = ast
        return (ast, full_path)
    
    def compile_file(self, filename: str, skip_bytecode: bool = False) -> Optional[Bytecode]:
        """Compile a source file, and optionally to bytecode."""
        self.current_filename = filename
        with open(filename, 'r', encoding='utf-8') as f:
            source = f.read()
        return self.compile(source, skip_bytecode, filename=filename)
