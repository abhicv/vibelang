import unittest
from lexer import Lexer
from parser import Parser
from type_checker import TypeChecker
from type_system import *
from errors import TypeError as VibeLangTypeError

class TestTypeChecker(unittest.TestCase):
    def check(self, source):
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        program = parser.parse()
        checker = TypeChecker()
        checker.check_program(program)
        return program

    def test_type_inference(self):
        source = "let x = 10; let y = 20.5; let s = \"hello\"; let b = true;"
        program = self.check(source)
        
        self.assertIsInstance(program.statements[0].type, IntType)
        self.assertIsInstance(program.statements[1].type, FloatType)
        self.assertIsInstance(program.statements[2].type, StringType)
        self.assertIsInstance(program.statements[3].type, BoolType)

    def test_type_mismatch(self):
        source = "let x: int = \"not an int\";"
        with self.assertRaises(VibeLangTypeError):
            self.check(source)

    def test_function_types(self):
        source = """
        fn add(a: int, b: int) -> int {
            return a + b;
        }
        let res = add(1, 2);
        """
        program = self.check(source)
        self.assertIsInstance(program.statements[1].type, IntType)

    def test_array_method_types(self):
        source = """
        let a = [1, 2];
        a.push(3);
        let x = a.pop();
        """
        program = self.check(source)
        
        # a.push(3) returns VoidType
        self.assertIsInstance(program.statements[1].expression.type, VoidType)
        
        # a.pop() returns IntType
        self.assertIsInstance(program.statements[2].initializer.type, IntType)

    def test_scoping(self):
        source = """
        let x = 10;
        fn f() -> int {
            let x = 20;
            return x;
        }
        """
        # Should not raise error (shadowing is allowed)
        self.check(source)

if __name__ == '__main__':
    unittest.main()
