import unittest
from lexer import Lexer
from parser import Parser
from ast_nodes import *

class TestParser(unittest.TestCase):
    def parse(self, source):
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        return parser.parse()

    def test_expression_precedence(self):
        source = "1 + 2 * 3;"
        program = self.parse(source)
        expr_stmt = program.statements[0]
        self.assertIsInstance(expr_stmt, ExpressionStatement)
        
        binary_op = expr_stmt.expression
        self.assertEqual(binary_op.operator, '+')
        self.assertIsInstance(binary_op.left, IntLiteral)
        self.assertIsInstance(binary_op.right, BinaryOp)
        self.assertEqual(binary_op.right.operator, '*')

    def test_variable_declaration(self):
        source = "let x: int = 10;"
        program = self.parse(source)
        var_decl = program.statements[0]
        self.assertIsInstance(var_decl, VariableDeclaration)
        self.assertEqual(var_decl.name, "x")
        self.assertEqual(var_decl.type_annotation.type_name, "int")
        self.assertIsInstance(var_decl.initializer, IntLiteral)

    def test_function_declaration(self):
        source = "fn add(a: int, b: int) -> int { return a + b; }"
        program = self.parse(source)
        func_decl = program.statements[0]
        self.assertIsInstance(func_decl, FunctionDeclaration)
        self.assertEqual(func_decl.name, "add")
        self.assertEqual(len(func_decl.parameters), 2)
        self.assertEqual(func_decl.return_type.type_name, "int")

    def test_if_else(self):
        source = "if true { print(1); } else { print(0); }"
        program = self.parse(source)
        if_stmt = program.statements[0]
        self.assertIsInstance(if_stmt, IfStatement)
        self.assertIsInstance(if_stmt.condition, BoolLiteral)
        self.assertEqual(len(if_stmt.then_block), 1)
        self.assertEqual(len(if_stmt.else_block), 1)

    def test_array_operations(self):
        source = "let a = [1, 2]; let val = a[0]; a.push(3);"
        program = self.parse(source)
        
        # let a = [1, 2];
        self.assertIsInstance(program.statements[0].initializer, ArrayLiteral)
        
        # let val = a[0];
        self.assertIsInstance(program.statements[1].initializer, ArrayIndex)
        
        # a.push(3);
        expr_stmt = program.statements[2]
        self.assertIsInstance(expr_stmt.expression, MethodCall)
        self.assertEqual(expr_stmt.expression.method_name, "push")

if __name__ == '__main__':
    unittest.main()
