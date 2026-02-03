"""
Stack-based virtual machine for executing VibeLang bytecode.
"""

from typing import List, Any, Dict
from .bytecode import Bytecode, OpCode, Instruction
from .errors import RuntimeError as VibeRuntimeError


class VibeLangVM:
    """Virtual machine for executing VibeLang bytecode."""
    
    def __init__(self, bytecode: Bytecode, debug: bool = False):
        self.bytecode = bytecode
        self.debug = debug
        
        # Execution state
        self.stack: List[Any] = []
        self.variables: Dict[int, Any] = {}  # Variable index -> value
        self.ip = 0  # Instruction pointer
        self.call_stack: List[Dict] = []  # Call frames
    
    def run(self):
        """Run the bytecode."""
        while self.ip < len(self.bytecode.instructions):
            instruction = self.bytecode.instructions[self.ip]
            self.ip += 1
            
            if self.debug:
                print(f"IP: {self.ip-1:4d} | Stack: {self.stack} | {instruction}")
            
            self.execute_instruction(instruction)
        
        # Return top of stack if available
        if self.stack:
            return self.stack[-1]
        return None
    
    def execute_instruction(self, instr: Instruction):
        """Execute a single instruction."""
        opcode = instr.opcode
        operand = instr.operand
        
        # Stack operations
        if opcode == OpCode.LOAD_CONST:
            value = self.bytecode.constants[operand]
            self.stack.append(value)
        
        elif opcode == OpCode.LOAD_VAR:
            if operand not in self.variables:
                raise VibeRuntimeError(f"Undefined variable at index {operand}")
            self.stack.append(self.variables[operand])
        
        elif opcode == OpCode.STORE_VAR:
            if not self.stack:
                raise VibeRuntimeError("Stack underflow in STORE_VAR")
            value = self.stack.pop()
            self.variables[operand] = value
        
        elif opcode == OpCode.POP:
            if self.stack:
                self.stack.pop()
        
        # Arithmetic operations
        elif opcode == OpCode.ADD:
            right = self.stack.pop()
            left = self.stack.pop()
            try:
                self.stack.append(left + right)
            except TypeError:
                raise VibeRuntimeError(f"Cannot add {type(left).__name__} and {type(right).__name__}")
        
        elif opcode == OpCode.SUB:
            right = self.stack.pop()
            left = self.stack.pop()
            self.stack.append(left - right)
        
        elif opcode == OpCode.MUL:
            right = self.stack.pop()
            left = self.stack.pop()
            self.stack.append(left * right)
        
        elif opcode == OpCode.DIV:
            right = self.stack.pop()
            left = self.stack.pop()
            if right == 0:
                raise VibeRuntimeError("Division by zero")
            # Integer division if both operands are integers
            if isinstance(left, int) and isinstance(right, int):
                self.stack.append(left // right)
            else:
                self.stack.append(left / right)
        
        elif opcode == OpCode.MOD:
            right = self.stack.pop()
            left = self.stack.pop()
            self.stack.append(left % right)
        
        elif opcode == OpCode.NEG:
            value = self.stack.pop()
            self.stack.append(-value)
        
        # Comparison operations
        elif opcode == OpCode.EQ:
            right = self.stack.pop()
            left = self.stack.pop()
            self.stack.append(left == right)
        
        elif opcode == OpCode.NE:
            right = self.stack.pop()
            left = self.stack.pop()
            self.stack.append(left != right)
        
        elif opcode == OpCode.LT:
            right = self.stack.pop()
            left = self.stack.pop()
            self.stack.append(left < right)
        
        elif opcode == OpCode.LE:
            right = self.stack.pop()
            left = self.stack.pop()
            self.stack.append(left <= right)
        
        elif opcode == OpCode.GT:
            right = self.stack.pop()
            left = self.stack.pop()
            self.stack.append(left > right)
        
        elif opcode == OpCode.GE:
            right = self.stack.pop()
            left = self.stack.pop()
            self.stack.append(left >= right)
        
        # Logical operations
        elif opcode == OpCode.AND:
            right = self.stack.pop()
            left = self.stack.pop()
            self.stack.append(left and right)
        
        elif opcode == OpCode.OR:
            right = self.stack.pop()
            left = self.stack.pop()
            self.stack.append(left or right)
        
        elif opcode == OpCode.NOT:
            value = self.stack.pop()
            self.stack.append(not value)
        
        # Control flow
        elif opcode == OpCode.JUMP:
            self.ip = operand
        
        elif opcode == OpCode.JUMP_IF_FALSE:
            condition = self.stack.pop()
            if not condition:
                self.ip = operand
        
        elif opcode == OpCode.JUMP_IF_TRUE:
            condition = self.stack.pop()
            if condition:
                self.ip = operand
        
        # Function operations
        elif opcode == OpCode.CALL:
            # Save current state
            frame = {
                'return_address': self.ip,
                'variables': self.variables
            }
            self.call_stack.append(frame)
            
            # Start fresh with local variables for the function
            self.variables = {}
            
            # Jump to function
            self.ip = operand
        
        elif opcode == OpCode.RETURN:
            # Pop return value(s)
            value = None
            if operand == 1:
                value = self.stack.pop()
            elif operand > 1:
                value = []
                for _ in range(operand):
                    value.append(self.stack.pop())
                value.reverse() # Elements were popped in reverse order
            
            if self.call_stack:
                # Restore previous state
                frame = self.call_stack.pop()
                self.ip = frame['return_address']
                self.variables = frame['variables']
                
                # Push return value (single value or list of values)
                if operand > 0:
                    self.stack.append(value)
            else:
                # Return from main program
                self.ip = len(self.bytecode.instructions)
        
        # Built-in functions
        elif opcode == OpCode.PRINT:
            value = self.stack.pop() if self.stack else ""
            print(self.value_to_string(value))
            # Print returns void, push None
            self.stack.append(None)
        
        elif opcode == OpCode.LEN:
            container = self.stack.pop()
            if not isinstance(container, (list, str)):
                raise VibeRuntimeError(f"len() requires array or string, got {type(container).__name__}")
            self.stack.append(len(container))
            
        elif opcode == OpCode.ORD:
            char = self.stack.pop()
            self.stack.append(ord(char))
            
        elif opcode == OpCode.CHR:
            code = self.stack.pop()
            self.stack.append(chr(code))
            
        elif opcode == OpCode.STR:
            char = self.stack.pop()
            self.stack.append(str(char))
        
        # Array operations
        elif opcode == OpCode.BUILD_ARRAY:
            count = operand
            elements = []
            for _ in range(count):
                elements.insert(0, self.stack.pop())
            self.stack.append(elements)
        
        elif opcode == OpCode.INDEX_LOAD:
            index = self.stack.pop()
            container = self.stack.pop()
            
            if not isinstance(container, (list, str)):
                raise VibeRuntimeError(f"Cannot index type: {type(container).__name__}")
            if not isinstance(index, int):
                raise VibeRuntimeError(f"Index must be int, got {type(index).__name__}")
            if index < 0 or index >= len(container):
                raise VibeRuntimeError(f"Index out of bounds: {index}")
            
            self.stack.append(container[index])
        
        elif opcode == OpCode.INDEX_STORE:
            value = self.stack.pop()
            index = self.stack.pop()
            array = self.stack.pop()
            
            if not isinstance(array, list):
                raise VibeRuntimeError(f"Cannot index non-array type: {type(array).__name__}")
            if not isinstance(index, int):
                raise VibeRuntimeError(f"Array index must be int, got {type(index).__name__}")
            if index < 0 or index >= len(array):
                raise VibeRuntimeError(f"Array index out of bounds: {index}")
            
            array[index] = value

        elif opcode == OpCode.ARRAY_PUSH:
            value = self.stack.pop()
            array = self.stack.pop()
            if not isinstance(array, list):
                raise VibeRuntimeError(f"push() requires array, got {type(array).__name__}")
            array.append(value)
            # push() returns void, but we could return the new length
            # For now, let's push None for Void
            self.stack.append(None)
            
        elif opcode == OpCode.ARRAY_POP:
            array = self.stack.pop()
            if not isinstance(array, list):
                raise VibeRuntimeError(f"pop() requires array, got {type(array).__name__}")
            if not array:
                raise VibeRuntimeError("pop() from empty array")
            value = array.pop()
            self.stack.append(value)
        
        elif opcode == OpCode.UNPACK:
            count = operand
            container = self.stack.pop()
            if not isinstance(container, list):
                 raise VibeRuntimeError(f"UNPACK requires array/list, got {type(container).__name__}")
            if len(container) != count:
                raise VibeRuntimeError(f"UNPACK mismatch: expected {count}, got {len(container)}")
            # Push elements onto stack in reverse order so they are popped in original order
            for item in reversed(container):
                self.stack.append(item)
        
        else:
            raise VibeRuntimeError(f"Unknown opcode: {opcode}")
    
    def value_to_string(self, value: Any) -> str:
        """Convert value to string for printing."""
        if isinstance(value, bool):
            return "true" if value else "false"
        elif isinstance(value, list):
            elements = [self.value_to_string(v) for v in value]
            return f"[{', '.join(elements)}]"
        elif value is None:
            return ""
        else:
            return str(value)
