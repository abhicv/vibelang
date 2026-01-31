import unittest
from lexer import Lexer
from parser import Parser
from type_checker import TypeChecker
from codegen_c import CCodeGenerator

class TestCCodegen(unittest.TestCase):
    def generate_c(self, source):
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        program = parser.parse()
        checker = TypeChecker()
        checker.check_program(program)
        codegen = CCodeGenerator()
        return codegen.generate(program)

    def test_basic_structure(self):
        source = "fn main() -> int { return 0; }"
        c_code = self.generate_c(source)
        
        self.assertIn("#include <stdio.h>", c_code)
        self.assertIn("long long main_func(void)", c_code)
        self.assertIn("int main(int argc, char** argv)", c_code)

    def test_array_push_c(self):
        source = "let a = [1]; a.push(2);"
        c_code = self.generate_c(source)
        
        self.assertIn("vibe_array_new", c_code)
        self.assertIn("vibe_array_push", c_code)

    def test_nested_expressions(self):
        source = "let x = (1 + 2) * 3;"
        c_code = self.generate_c(source)
        
        self.assertIn("(1LL + 2LL) * 3LL", c_code)

if __name__ == '__main__':
    unittest.main()
