import unittest
from bytecode import Bytecode, OpCode
from vm import VibeLangVM

class TestVM(unittest.TestCase):
    def test_arithmetic(self):
        bc = Bytecode()
        bc.add_constant(10)
        bc.add_constant(20)
        bc.add_instruction(OpCode.LOAD_CONST, 0)
        bc.add_instruction(OpCode.LOAD_CONST, 1)
        bc.add_instruction(OpCode.ADD)
        
        vm = VibeLangVM(bc)
        result = vm.run()
        self.assertEqual(result, 30)

    def test_variables(self):
        bc = Bytecode()
        bc.add_constant(100)
        bc.add_instruction(OpCode.LOAD_CONST, 0)
        bc.add_instruction(OpCode.STORE_VAR, 0)
        bc.add_instruction(OpCode.LOAD_VAR, 0)
        
        vm = VibeLangVM(bc)
        result = vm.run()
        self.assertEqual(result, 100)

    def test_jumps(self):
        bc = Bytecode()
        bc.add_constant(True)
        bc.add_constant(10)
        bc.add_constant(20)
        
        bc.add_instruction(OpCode.LOAD_CONST, 0) # 0
        bc.add_instruction(OpCode.JUMP_IF_FALSE, 4) # 1: skip to index 4 (LOAD_CONST 2)
        bc.add_instruction(OpCode.LOAD_CONST, 1) # 2: loads 10
        bc.add_instruction(OpCode.JUMP, 5) # 3: skip to end
        bc.add_instruction(OpCode.LOAD_CONST, 2) # 4: loads 20
        
        vm = VibeLangVM(bc)
        result = vm.run()
        self.assertEqual(result, 10)

    def test_array_ops(self):
        bc = Bytecode()
        bc.add_constant(1)
        bc.add_constant(2)
        bc.add_instruction(OpCode.LOAD_CONST, 0)
        bc.add_instruction(OpCode.LOAD_CONST, 1)
        bc.add_instruction(OpCode.BUILD_ARRAY, 2)
        bc.add_instruction(OpCode.STORE_VAR, 0) # Store array in var 0
        
        # push 3
        bc.add_constant(3)
        bc.add_instruction(OpCode.LOAD_VAR, 0)
        bc.add_instruction(OpCode.LOAD_CONST, 2)
        bc.add_instruction(OpCode.ARRAY_PUSH)
        bc.add_instruction(OpCode.POP) # pop None from push()
        
        # pop
        bc.add_instruction(OpCode.LOAD_VAR, 0)
        bc.add_instruction(OpCode.ARRAY_POP)
        
        vm = VibeLangVM(bc)
        result = vm.run()
        self.assertEqual(result, 3)

if __name__ == '__main__':
    unittest.main()
