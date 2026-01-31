"""
Code generator for VibeLang.
Converts typed AST to bytecode.
"""

from typing import Dict, List, Optional
from .bytecode import Bytecode, OpCode
from .ast_nodes import *
from .type_system import *
from .errors import CodeGenError


class CodeGenerator:
    """Generates bytecode from typed AST."""
    
    def __init__(self):
        self.bytecode = Bytecode()
        self.variables: Dict[str, int] = {}  # Variable name -> index
        self.var_counter = 0
        self.functions: Dict[str, int] = {}  # Function name -> address
        self.loop_stack: List[tuple] = []  # Stack of (continue_label, break_label)
        self.function_fixups: List[tuple] = []  # List of (instr_index, function_name)
    
    def generate(self, program: Program, other_programs: List[Program] = None) -> Bytecode:
        """Generate bytecode for entire program."""
        all_programs = [program]
        if other_programs:
            all_programs.extend(other_programs)
            
        # First pass: collect function addresses
        for p in all_programs:
            for statement in p.statements:
                if isinstance(statement, FunctionDeclaration):
                    self.functions[statement.name] = -1  # Placeholder
        
        # Second pass: generate code for all functions in all modules
        for p in all_programs:
            for statement in p.statements:
                if isinstance(statement, FunctionDeclaration):
                    self.generate_function_declaration(statement)
                    
        # Third pass: generate code for top-level statements of the MAIN program ONLY
        for statement in program.statements:
            if not isinstance(statement, (FunctionDeclaration, StructDefinition, Import)):
                self.generate_statement(statement)
        
        # Add halt instruction
        self.bytecode.add_instruction(OpCode.RETURN)
        
        # Final pass: Patch function calls
        for instr_idx, func_name in self.function_fixups:
            addr = self.functions.get(func_name)
            if addr is None or addr == -1:
                # Should have been caught by type checker, but be safe
                raise CodeGenError(f"Undefined function: {func_name}", 0, 0)
            self.bytecode.patch_instruction(instr_idx, OpCode.CALL, addr)
        
        return self.bytecode
    
    def generate_statement(self, node: ASTNode):
        """Generate code for a statement."""
        if isinstance(node, VariableDeclaration):
            self.generate_variable_declaration(node)
        elif isinstance(node, FunctionDeclaration):
            self.generate_function_declaration(node)
        elif isinstance(node, Assignment):
            self.generate_assignment(node)
        elif isinstance(node, IfStatement):
            self.generate_if_statement(node)
        elif isinstance(node, WhileStatement):
            self.generate_while_statement(node)
        elif isinstance(node, ForStatement):
            self.generate_for_statement(node)
        elif isinstance(node, ReturnStatement):
            self.generate_return_statement(node)
        elif isinstance(node, StructDefinition):
            pass
        elif isinstance(node, Import):
            pass
        elif isinstance(node, ExpressionStatement):
            self.generate_expression(node.expression)
            # Pop result if not used
            if not isinstance(node.expression, Assignment):
                self.bytecode.add_instruction(OpCode.POP)
        else:
            raise CodeGenError(f"Unknown statement type: {type(node).__name__}", node.line, node.column)
    
    def generate_variable_declaration(self, node: VariableDeclaration):
        """Generate code for variable declaration."""
        # Allocate variable index
        var_index = self.var_counter
        self.variables[node.name] = var_index
        self.var_counter += 1
        
        # Generate initializer if present
        if node.initializer:
            self.generate_expression(node.initializer)
            self.bytecode.add_instruction(OpCode.STORE_VAR, var_index)
        else:
            # Initialize with default value
            const_index = self.bytecode.add_constant(0)
            self.bytecode.add_instruction(OpCode.LOAD_CONST, const_index)
            self.bytecode.add_instruction(OpCode.STORE_VAR, var_index)
    
    def generate_function_declaration(self, node: FunctionDeclaration):
        """Generate code for function declaration."""
        # Skip over function body during main execution
        jump_over_func = self.bytecode.add_instruction(OpCode.JUMP, 0)
        
        # Record function start address
        func_start = self.bytecode.current_index()
        self.functions[node.name] = func_start
        
        # Save current variable context
        old_variables = self.variables.copy()
        old_var_counter = self.var_counter
        
        # Reset for function scope
        self.variables = {}
        self.var_counter = 0
        
        # Allocate parameters
        for param in node.parameters:
            var_index = self.var_counter
            self.variables[param.name] = var_index
            self.var_counter += 1
        
        # Parameters are already on stack from CALL, store them
        for i in range(len(node.parameters) - 1, -1, -1):
            self.bytecode.add_instruction(OpCode.STORE_VAR, i)
        
        # Generate function body
        for statement in node.body:
            self.generate_statement(statement)
        
        # Ensure function returns (add default return if missing)
        if not node.body or not isinstance(node.body[-1], ReturnStatement):
            # Return default value based on return type
            if isinstance(node.return_type, IntType):
                const_index = self.bytecode.add_constant(0)
            elif isinstance(node.return_type, FloatType):
                const_index = self.bytecode.add_constant(0.0)
            elif isinstance(node.return_type, BoolType):
                const_index = self.bytecode.add_constant(False)
            elif isinstance(node.return_type, StringType):
                const_index = self.bytecode.add_constant("")
            else:
                const_index = self.bytecode.add_constant(0)
            
            self.bytecode.add_instruction(OpCode.LOAD_CONST, const_index)
            self.bytecode.add_instruction(OpCode.RETURN)
        
        # Patch jump to skip over function
        after_func = self.bytecode.current_index()
        self.bytecode.patch_instruction(jump_over_func, OpCode.JUMP, after_func)
        
        # Restore variable context
        self.variables = old_variables
        self.var_counter = old_var_counter
    
    def generate_assignment(self, node: Assignment):
        """Generate code for assignment."""
        if isinstance(node.target, Identifier):
            # Simple variable assignment
            self.generate_expression(node.value)
            var_index = self.variables.get(node.target.name)
            if var_index is None:
                raise CodeGenError(f"Undefined variable: {node.target.name}", node.line, node.column)
            self.bytecode.add_instruction(OpCode.STORE_VAR, var_index)
        
        elif isinstance(node.target, ArrayIndex):
            # Array element assignment
            self.generate_expression(node.target.array)
            self.generate_expression(node.target.index)
            self.generate_expression(node.value)
            self.bytecode.add_instruction(OpCode.INDEX_STORE)
        
        else:
            raise CodeGenError(f"Invalid assignment target: {type(node.target).__name__}", node.line, node.column)
    
    def generate_if_statement(self, node: IfStatement):
        """Generate code for if statement."""
        # Generate condition
        self.generate_expression(node.condition)
        
        # Jump to else/end if condition is false
        jump_to_else = self.bytecode.add_instruction(OpCode.JUMP_IF_FALSE, 0)
        
        # Generate then block
        for statement in node.then_block:
            self.generate_statement(statement)
        
        if node.else_block:
            # Jump over else block
            jump_to_end = self.bytecode.add_instruction(OpCode.JUMP, 0)
            
            # Patch jump to else
            else_start = self.bytecode.current_index()
            self.bytecode.patch_instruction(jump_to_else, OpCode.JUMP_IF_FALSE, else_start)
            
            # Generate else block
            for statement in node.else_block:
                self.generate_statement(statement)
            
            # Patch jump to end
            end_index = self.bytecode.current_index()
            self.bytecode.patch_instruction(jump_to_end, OpCode.JUMP, end_index)
        else:
            # Patch jump to end
            end_index = self.bytecode.current_index()
            self.bytecode.patch_instruction(jump_to_else, OpCode.JUMP_IF_FALSE, end_index)
    
    def generate_while_statement(self, node: WhileStatement):
        """Generate code for while loop."""
        loop_start = self.bytecode.current_index()
        
        # Generate condition
        self.generate_expression(node.condition)
        
        # Jump to end if condition is false
        jump_to_end = self.bytecode.add_instruction(OpCode.JUMP_IF_FALSE, 0)
        
        # Generate body
        for statement in node.body:
            self.generate_statement(statement)
        
        # Jump back to start
        self.bytecode.add_instruction(OpCode.JUMP, loop_start)
        
        # Patch jump to end
        end_index = self.bytecode.current_index()
        self.bytecode.patch_instruction(jump_to_end, OpCode.JUMP_IF_FALSE, end_index)
    
    def generate_for_statement(self, node: ForStatement):
        """Generate code for for loop (simplified - iterates over array)."""
        # This is a simplified implementation
        # A full implementation would use an iterator pattern
        
        # Generate iterable
        self.generate_expression(node.iterable)
        
        # Store array in temporary variable
        temp_array_index = self.var_counter
        self.var_counter += 1
        self.bytecode.add_instruction(OpCode.STORE_VAR, temp_array_index)
        
        # Initialize loop variable
        loop_var_index = self.var_counter
        self.variables[node.variable] = loop_var_index
        self.var_counter += 1
        
        # Initialize counter
        counter_index = self.var_counter
        self.var_counter += 1
        const_zero = self.bytecode.add_constant(0)
        self.bytecode.add_instruction(OpCode.LOAD_CONST, const_zero)
        self.bytecode.add_instruction(OpCode.STORE_VAR, counter_index)
        
        # Loop start
        loop_start = self.bytecode.current_index()
        
        # Check if counter < array length
        self.bytecode.add_instruction(OpCode.LOAD_VAR, counter_index)
        self.bytecode.add_instruction(OpCode.LOAD_VAR, temp_array_index)
        self.bytecode.add_instruction(OpCode.LEN)
        self.bytecode.add_instruction(OpCode.LT)
        
        # Jump to end if false
        jump_to_end = self.bytecode.add_instruction(OpCode.JUMP_IF_FALSE, 0)
        
        # Load current element into loop variable
        self.bytecode.add_instruction(OpCode.LOAD_VAR, temp_array_index)
        self.bytecode.add_instruction(OpCode.LOAD_VAR, counter_index)
        self.bytecode.add_instruction(OpCode.INDEX_LOAD)
        self.bytecode.add_instruction(OpCode.STORE_VAR, loop_var_index)
        
        # Generate body
        for statement in node.body:
            self.generate_statement(statement)
        
        # Increment counter
        self.bytecode.add_instruction(OpCode.LOAD_VAR, counter_index)
        const_one = self.bytecode.add_constant(1)
        self.bytecode.add_instruction(OpCode.LOAD_CONST, const_one)
        self.bytecode.add_instruction(OpCode.ADD)
        self.bytecode.add_instruction(OpCode.STORE_VAR, counter_index)
        
        # Jump back to start
        self.bytecode.add_instruction(OpCode.JUMP, loop_start)
        
        # Patch jump to end
        end_index = self.bytecode.current_index()
        self.bytecode.patch_instruction(jump_to_end, OpCode.JUMP_IF_FALSE, end_index)
    
    def generate_return_statement(self, node: ReturnStatement):
        """Generate code for return statement."""
        if node.value:
            self.generate_expression(node.value)
        else:
            # Return void/default value
            const_index = self.bytecode.add_constant(0)
            self.bytecode.add_instruction(OpCode.LOAD_CONST, const_index)
        
        self.bytecode.add_instruction(OpCode.RETURN)
    
    def generate_expression(self, node: ASTNode):
        """Generate code for expression."""
        if isinstance(node, IntLiteral):
            const_index = self.bytecode.add_constant(node.value)
            self.bytecode.add_instruction(OpCode.LOAD_CONST, const_index)
        
        elif isinstance(node, FloatLiteral):
            const_index = self.bytecode.add_constant(node.value)
            self.bytecode.add_instruction(OpCode.LOAD_CONST, const_index)
        
        elif isinstance(node, StringLiteral):
            const_index = self.bytecode.add_constant(node.value)
            self.bytecode.add_instruction(OpCode.LOAD_CONST, const_index)
        
        elif isinstance(node, BoolLiteral):
            self.bytecode.add_constant(node.value)
            self.bytecode.add_instruction(OpCode.LOAD_CONST, len(self.bytecode.constants) - 1)
        
        elif isinstance(node, NullLiteral):
            self.bytecode.add_constant(None)
            self.bytecode.add_instruction(OpCode.LOAD_CONST, len(self.bytecode.constants) - 1)
        elif isinstance(node, ArrayLiteral):
            # Push all elements onto stack
            for elem in node.elements:
                self.generate_expression(elem)
            # Build array
            self.bytecode.add_instruction(OpCode.BUILD_ARRAY, len(node.elements))
        
        elif isinstance(node, Identifier):
            var_index = self.variables.get(node.name)
            if var_index is not None:
                self.bytecode.add_instruction(OpCode.LOAD_VAR, var_index)
            else:
                # Must be a function reference
                if node.name in self.functions:
                    const_index = self.bytecode.add_constant(node.name)
                    self.bytecode.add_instruction(OpCode.LOAD_CONST, const_index)
                else:
                    raise CodeGenError(f"Undefined identifier: {node.name}", node.line, node.column)
        
        elif isinstance(node, BinaryOp):
            self.generate_binary_op(node)
        
        elif isinstance(node, UnaryOp):
            self.generate_unary_op(node)
        
        elif isinstance(node, FunctionCall):
            self.generate_function_call(node)
        
        elif isinstance(node, MethodCall):
            self.generate_method_call(node)
        
        elif isinstance(node, ArrayIndex):
            self.generate_expression(node.array)
            self.generate_expression(node.index)
            self.bytecode.add_instruction(OpCode.INDEX_LOAD)
        
        elif isinstance(node, Assignment):
            self.generate_assignment(node)
            # Assignment also produces a value (the assigned value)
            if isinstance(node.target, Identifier):
                var_index = self.variables[node.target.name]
                self.bytecode.add_instruction(OpCode.LOAD_VAR, var_index)
        
        elif isinstance(node, StructLiteral):
            # Bytecode doesn't support structs yet
            raise CodeGenError("Bytecode generation for structs not yet implemented", node.line, node.column)
        
        elif isinstance(node, MemberAccess):
            # Bytecode doesn't support structs yet
            raise CodeGenError("Bytecode generation for structs not yet implemented", node.line, node.column)
        
        else:
            raise CodeGenError(f"Unknown expression type: {type(node).__name__}", node.line, node.column)
    
    def generate_binary_op(self, node: BinaryOp):
        """Generate code for binary operation."""
        self.generate_expression(node.left)
        self.generate_expression(node.right)
        
        op_map = {
            '+': OpCode.ADD,
            '-': OpCode.SUB,
            '*': OpCode.MUL,
            '/': OpCode.DIV,
            '%': OpCode.MOD,
            '==': OpCode.EQ,
            '!=': OpCode.NE,
            '<': OpCode.LT,
            '<=': OpCode.LE,
            '>': OpCode.GT,
            '>=': OpCode.GE,
            'and': OpCode.AND,
            'or': OpCode.OR,
        }
        
        opcode = op_map.get(node.operator)
        if opcode:
            self.bytecode.add_instruction(opcode)
        else:
            raise CodeGenError(f"Unknown binary operator: {node.operator}", node.line, node.column)
    
    def generate_unary_op(self, node: UnaryOp):
        """Generate code for unary operation."""
        self.generate_expression(node.operand)
        
        if node.operator == '-':
            self.bytecode.add_instruction(OpCode.NEG)
        elif node.operator == 'not':
            self.bytecode.add_instruction(OpCode.NOT)
        else:
            raise CodeGenError(f"Unknown unary operator: {node.operator}", node.line, node.column)
    
    def generate_function_call(self, node: FunctionCall):
        """Generate code for function call."""
        # Handle built-in functions
        if isinstance(node.function, Identifier):
            func_name = node.function.name
            
            if func_name == 'print':
                # Generate argument
                if node.arguments:
                    self.generate_expression(node.arguments[0])
                self.bytecode.add_instruction(OpCode.PRINT)
                return
            
            elif func_name == 'len':
                # Generate argument
                if node.arguments:
                    self.generate_expression(node.arguments[0])
                self.bytecode.add_instruction(OpCode.LEN)
                return
        
        # User-defined function
        # Push arguments onto stack (in order)
        for arg in node.arguments:
            self.generate_expression(arg)
        
        # Get function address
        if isinstance(node.function, Identifier):
            func_name = node.function.name
            func_addr = self.functions.get(func_name, -1)
            
            # Emit CALL, even if address is not yet known
            instr_idx = self.bytecode.add_instruction(OpCode.CALL, func_addr)
            
            # If address is not yet known (-1), record for patching
            if func_addr == -1:
                self.function_fixups.append((instr_idx, func_name))
        else:
            raise CodeGenError("Function calls must use identifiers", node.line, node.column)

    def generate_method_call(self, node: MethodCall):
        """Generate code for method call."""
        # Push object onto stack
        self.generate_expression(node.object)
        
        # Method-specific handling
        if node.method_name == 'push':
            # Push argument
            self.generate_expression(node.arguments[0])
            self.bytecode.add_instruction(OpCode.ARRAY_PUSH)
        elif node.method_name == 'pop':
            self.bytecode.add_instruction(OpCode.ARRAY_POP)
        else:
            raise CodeGenError(f"Unknown method '{node.method_name}'", node.line, node.column)
