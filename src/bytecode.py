"""
Bytecode instruction definitions for VibeLang VM.
"""

from enum import Enum, auto
from .ast_nodes import Program
from dataclasses import dataclass
from typing import List, Any
import struct


class OpCode(Enum):
    """VM instruction opcodes."""
    # Stack operations
    LOAD_CONST = auto()      # Push constant onto stack
    LOAD_VAR = auto()        # Push variable value onto stack
    STORE_VAR = auto()       # Pop value and store in variable
    POP = auto()             # Pop top of stack
    
    # Arithmetic operations
    ADD = auto()
    SUB = auto()
    MUL = auto()
    DIV = auto()
    MOD = auto()
    NEG = auto()             # Unary negation
    
    # Comparison operations
    EQ = auto()
    NE = auto()
    LT = auto()
    LE = auto()
    GT = auto()
    GE = auto()
    
    # Logical operations
    AND = auto()
    OR = auto()
    NOT = auto()
    
    # Control flow
    JUMP = auto()            # Unconditional jump
    JUMP_IF_FALSE = auto()   # Jump if top of stack is false
    JUMP_IF_TRUE = auto()    # Jump if top of stack is true
    
    # Function operations
    CALL = auto()            # Call function
    RETURN = auto()          # Return from function
    
    # Built-in functions
    PRINT = auto()
    LEN = auto()
    ORD = auto()
    CHR = auto()
    STR = auto()
    
    # Array operations
    BUILD_ARRAY = auto()     # Build array from stack values
    INDEX_LOAD = auto()      # Load array element
    INDEX_STORE = auto()     # Store array element
    ARRAY_PUSH = auto()      # Push element to array
    ARRAY_POP = auto()       # Pop element from array
    UNPACK = auto()          # Unpack array/tuple onto stack


@dataclass
class Instruction:
    """Single bytecode instruction."""
    opcode: OpCode
    operand: Any = None
    
    def __repr__(self):
        if self.operand is not None:
            return f"{self.opcode.name} {self.operand}"
        return self.opcode.name


class Bytecode:
    """Container for compiled bytecode."""
    
    def __init__(self):
        self.instructions: List[Instruction] = []
        self.constants: List[Any] = []
    
    def add_instruction(self, opcode: OpCode, operand: Any = None) -> int:
        """Add instruction and return its index."""
        self.instructions.append(Instruction(opcode, operand))
        return len(self.instructions) - 1
    
    def add_constant(self, value: Any) -> int:
        """Add constant to pool and return its index."""
        for i, const in enumerate(self.constants):
            if type(const) == type(value) and const == value:
                return i
        idx = len(self.constants)
        self.constants.append(value)
        return idx
    
    def patch_instruction(self, index: int, opcode: OpCode, operand: Any = None):
        """Modify instruction at given index."""
        self.instructions[index] = Instruction(opcode, operand)
    
    def current_index(self) -> int:
        """Get current instruction index."""
        return len(self.instructions)
    
    def disassemble(self) -> str:
        """Disassemble bytecode for debugging."""
        lines = ["=== Bytecode ==="]
        lines.append(f"Constants: {self.constants}")
        lines.append("\nInstructions:")
        for i, instr in enumerate(self.instructions):
            lines.append(f"{i:4d}: {instr}")
        return '\n'.join(lines)
    
    def serialize(self) -> bytes:
        """Serialize bytecode to bytes."""
        # Simple serialization format
        data = bytearray()
        
        # Write constants
        data.extend(struct.pack('I', len(self.constants)))
        for const in self.constants:
            if isinstance(const, int):
                data.append(0)  # Type tag for int
                data.extend(struct.pack('q', const))
            elif isinstance(const, float):
                data.append(1)  # Type tag for float
                data.extend(struct.pack('d', const))
            elif isinstance(const, str):
                data.append(2)  # Type tag for string
                encoded = const.encode('utf-8')
                data.extend(struct.pack('I', len(encoded)))
                data.extend(encoded)
            elif isinstance(const, bool):
                data.append(3)  # Type tag for bool
                data.append(1 if const else 0)
        
        # Write instructions
        data.extend(struct.pack('I', len(self.instructions)))
        for instr in self.instructions:
            data.append(instr.opcode.value)
            if instr.operand is not None:
                data.extend(struct.pack('i', instr.operand))
            else:
                data.extend(struct.pack('i', -1))  # No operand marker
        
        return bytes(data)
    
    @staticmethod
    def deserialize(data: bytes) -> 'Bytecode':
        """Deserialize bytecode from bytes."""
        bytecode = Bytecode()
        pos = 0
        
        # Read constants
        const_count = struct.unpack('I', data[pos:pos+4])[0]
        pos += 4
        
        for _ in range(const_count):
            type_tag = data[pos]
            pos += 1
            
            if type_tag == 0:  # int
                value = struct.unpack('q', data[pos:pos+8])[0]
                pos += 8
                bytecode.constants.append(value)
            elif type_tag == 1:  # float
                value = struct.unpack('d', data[pos:pos+8])[0]
                pos += 8
                bytecode.constants.append(value)
            elif type_tag == 2:  # string
                length = struct.unpack('I', data[pos:pos+4])[0]
                pos += 4
                value = data[pos:pos+length].decode('utf-8')
                pos += length
                bytecode.constants.append(value)
            elif type_tag == 3:  # bool
                value = bool(data[pos])
                pos += 1
                bytecode.constants.append(value)
        
        # Read instructions
        instr_count = struct.unpack('I', data[pos:pos+4])[0]
        pos += 4
        
        for _ in range(instr_count):
            opcode_value = data[pos]
            pos += 1
            opcode = OpCode(opcode_value)
            
            operand = struct.unpack('i', data[pos:pos+4])[0]
            pos += 4
            
            if operand == -1:
                operand = None
            
            bytecode.instructions.append(Instruction(opcode, operand))
        
        return bytecode
