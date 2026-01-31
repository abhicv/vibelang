import unittest
from lexer import Lexer
from parser import Parser
from type_checker import TypeChecker
from codegen import CodeGenerator
from bytecode import OpCode

class TestCodegen(unittest.TestCase):
    def compile(self, source):
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        program = parser.parse()
        checker = TypeChecker()
        checker.check_program(program)
        codegen = CodeGenerator()
        codegen.generate(program)
        return codegen.bytecode

    def test_basic_arithmetic(self):
        source = "1 + 2;"
        bytecode = self.compile(source)
        
        # JUMP 5, LOAD_CONST 0, LOAD_CONST 1, ADD, POP, RETURN
        opcodes = [instr.opcode for instr in bytecode.instructions]
        self.assertIn(OpCode.ADD, opcodes)
        self.assertIn(OpCode.LOAD_CONST, opcodes)

    def test_variable_ops(self):
        source = "let x = 10; x = 20;"
        bytecode = self.compile(source)
        
        opcodes = [instr.opcode for instr in bytecode.instructions]
        self.assertIn(OpCode.STORE_VAR, opcodes)
        self.assertIn(OpCode.LOAD_VAR, opcodes)

    def test_control_flow_jumps(self):
        source = "if true { 1; } else { 2; }"
        bytecode = self.compile(source)
        
        opcodes = [instr.opcode for instr in bytecode.instructions]
        self.assertIn(OpCode.JUMP_IF_FALSE, opcodes)
        self.assertIn(OpCode.JUMP, opcodes)

    def test_array_methods_codegen(self):
        source = "let a = [1]; a.push(2); a.pop();"
        bytecode = self.compile(source)
        
        opcodes = [instr.opcode for instr in bytecode.instructions]
        self.assertIn(OpCode.ARRAY_PUSH, opcodes)
        self.assertIn(OpCode.ARRAY_POP, opcodes)

if __name__ == '__main__':
    unittest.main()
