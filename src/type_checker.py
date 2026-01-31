"""
Type checker and semantic analyzer for VibeLang.
"""

from typing import Dict, List, Optional
from .ast_nodes import *
from .type_system import *
from .errors import TypeError as VibeLangTypeError


class SymbolTable:
    """Manages variable and function scopes."""
    
    def __init__(self, parent: Optional['SymbolTable'] = None):
        self.parent = parent
        self.symbols: Dict[str, Type] = {}
    
    def define(self, name: str, type_: Type):
        """Define a symbol in current scope."""
        if name in self.symbols:
            raise VibeLangTypeError(f"Variable '{name}' already defined in this scope")
        self.symbols[name] = type_
    
    def lookup(self, name: str) -> Optional[Type]:
        """Look up symbol in current and parent scopes."""
        if name in self.symbols:
            return self.symbols[name]
        if self.parent:
            return self.parent.lookup(name)
        return None
    
    def update(self, name: str, type_: Type):
        """Update existing symbol."""
        if name in self.symbols:
            self.symbols[name] = type_
            return
        if self.parent:
            self.parent.update(name, type_)
        else:
            raise VibeLangTypeError(f"Variable '{name}' not defined")


class TypeChecker:
    """Performs type checking and semantic analysis."""
    
    def __init__(self):
        self.symbol_table = SymbolTable()
        self.current_function_return_type: Optional[Type] = None
        self.struct_types: Dict[str, StructType] = {}
        
        # Built-in functions
        self.symbol_table.define('print', FunctionType([StringType()], VoidType()))
        self.symbol_table.define('len', FunctionType([ArrayType(IntType())], IntType()))
        self.symbol_table.define('read_str', FunctionType([], StringType()))
        self.symbol_table.define('read_int', FunctionType([], IntType()))
        
        self.module_resolver = None  # Set by Compiler
        self.current_file = "<unknown>"
        # Track modules being checked to avoid recursion
        self.checked_modules = set()
    
    def check_program(self, program: Program):
        """Type check entire program."""
        # 1. Handle imports first
        for statement in program.statements:
            if isinstance(statement, Import):
                self.check_import(statement)
                
        # 2. Collect local definitions (hoisting)
        self._collect_definitions(program)
        
        # 3. Check everything else
        for statement in program.statements:
            if isinstance(statement, (Import, StructDefinition)):
                continue
            self.check_statement(statement)

    def _collect_definitions(self, program: Program):
        """Collect all top-level definitions."""
        # First pass: Register all struct names
        for stmt in program.statements:
            if isinstance(stmt, StructDefinition):
                if stmt.name not in self.struct_types:
                    self.struct_types[stmt.name] = StructType(stmt.name, {})
                    
        # Second pass: Fill in struct fields and function types
        for stmt in program.statements:
            if isinstance(stmt, StructDefinition):
                self.check_struct_definition(stmt)
            elif isinstance(stmt, FunctionDeclaration):
                # Just define the function type in symbol table
                param_types = [self.get_type_from_annotation(p.type_annotation) for p in stmt.parameters]
                return_type = self.get_type_from_annotation(stmt.return_type)
                self.symbol_table.define(stmt.name, FunctionType(param_types, return_type))
    
    def check_statement(self, node: ASTNode):
        """Type check a statement."""
        if isinstance(node, Import):
            self.check_import(node)
        elif isinstance(node, StructDefinition):
            self.check_struct_definition(node)
        elif isinstance(node, VariableDeclaration):
            self.check_variable_declaration(node)
        elif isinstance(node, FunctionDeclaration):
            self.check_function_declaration(node)
        elif isinstance(node, Assignment):
            self.check_assignment(node)
        elif isinstance(node, IfStatement):
            self.check_if_statement(node)
        elif isinstance(node, WhileStatement):
            self.check_while_statement(node)
        elif isinstance(node, ForStatement):
            self.check_for_statement(node)
        elif isinstance(node, ReturnStatement):
            self.check_return_statement(node)
        elif isinstance(node, ExpressionStatement):
            self.check_expression(node.expression)
        else:
            raise VibeLangTypeError(f"Unknown statement type: {type(node).__name__}", node.line, node.column)

    def check_import(self, node: Import):
        """Type check an import statement."""
        if not self.module_resolver:
            raise VibeLangTypeError("Module resolver not set", node.line, node.column)
            
        try:
            module_ast, full_path = self.module_resolver(node.path, self.current_file)
        except Exception as e:
            raise VibeLangTypeError(str(e), node.line, node.column)
            
        # Avoid circular imports
        if full_path in self.checked_modules:
            return
            
        # Create a new type checker for the imported module
        imported_checker = TypeChecker()
        imported_checker.module_resolver = self.module_resolver
        imported_checker.current_file = full_path
        # Pass the set of checked modules to the next level
        imported_checker.checked_modules = self.checked_modules
        imported_checker.checked_modules.add(full_path)
        
        # Check the imported module
        imported_checker.check_program(module_ast)
        
        # Merge symbols
        # For now, merge all functions and structs
        for name, type_ in imported_checker.symbol_table.symbols.items():
            # Skip built-ins
            if name in ['print', 'len', 'read_str', 'read_int']:
                continue
            try:
                self.symbol_table.define(name, type_)
            except VibeLangTypeError:
                # Already defined, skip or error? For now, skip to allow re-imports
                pass
                
        for name, struct_type in imported_checker.struct_types.items():
            if name not in self.struct_types:
                self.struct_types[name] = struct_type
    
    def check_variable_declaration(self, node: VariableDeclaration):
        """Type check variable declaration."""
        # Check initializer type
        initializer_type = None
        if node.initializer:
            # Pass type hint if available
            expected_type = self.get_type_from_annotation(node.type_annotation) if node.type_annotation else None
            initializer_type = self.check_expression(node.initializer, expected_type)
        
        # Determine variable type
        if node.type_annotation:
            var_type = self.get_type_from_annotation(node.type_annotation)
            
            # Check type compatibility with initializer
            if initializer_type and not can_coerce(initializer_type, var_type):
                raise VibeLangTypeError(
                    f"Cannot assign {initializer_type} to variable of type {var_type}",
                    node.line, node.column
                )
        else:
            # Type inference
            if not initializer_type:
                raise VibeLangTypeError(
                    f"Variable '{node.name}' requires type annotation or initializer",
                    node.line, node.column
                )
            var_type = initializer_type
        
        # Define variable in symbol table
        self.symbol_table.define(node.name, var_type)
        node.type = var_type
    
    def check_function_declaration(self, node: FunctionDeclaration):
        """Type check function declaration."""
        # Build function type
        param_types = [self.get_type_from_annotation(p.type_annotation) for p in node.parameters]
        return_type = self.get_type_from_annotation(node.return_type)
        func_type = FunctionType(param_types, return_type)
        
        # Define function in current scope if not already defined (by hoisting)
        if self.symbol_table.lookup(node.name) != func_type:
            try:
                self.symbol_table.define(node.name, func_type)
            except VibeLangTypeError:
                # Type mismatch or already defined differently
                pass
        
        # Create new scope for function body
        self.symbol_table = SymbolTable(self.symbol_table)
        
        # Define parameters in function scope
        for param in node.parameters:
            param_type = self.get_type_from_annotation(param.type_annotation)
            self.symbol_table.define(param.name, param_type)
        
        # Check function body
        old_return_type = self.current_function_return_type
        self.current_function_return_type = return_type
        
        for statement in node.body:
            self.check_statement(statement)
        
        self.current_function_return_type = old_return_type
        
        # Exit function scope
        self.symbol_table = self.symbol_table.parent
        
        node.type = func_type
    
    def check_struct_definition(self, node: StructDefinition):
        """Type check struct definition."""
        # Struct name should already be in self.struct_types from _collect_definitions
        struct_type = self.struct_types.get(node.name)
        if not struct_type:
            struct_type = StructType(node.name, {})
            self.struct_types[node.name] = struct_type
        
        # Build field types
        field_types = {}
        for field in node.fields:
            field_types[field.name] = self.get_type_from_annotation(field.type_annotation)
        
        struct_type.fields = field_types
        node.type = struct_type
        return struct_type
    
    def get_type_from_annotation(self, annotation: TypeAnnotation) -> Type:
        """Convert type annotation to Type object, supporting structs."""
        t = None
        if annotation.type_name == 'int':
            t = IntType()
        elif annotation.type_name == 'float':
            t = FloatType()
        elif annotation.type_name == 'bool':
            t = BoolType()
        elif annotation.type_name == 'string':
            t = StringType()
        elif annotation.type_name == 'char':
            t = CharType()
        elif annotation.type_name == 'array':
            element_type = self.get_type_from_annotation(annotation.element_type)
            t = ArrayType(element_type)
        elif annotation.type_name == 'void':
            t = VoidType()
        elif annotation.type_name in self.struct_types:
            t = self.struct_types[annotation.type_name]
        else:
            raise VibeLangTypeError(f"Unknown type: {annotation.type_name}", annotation.line, annotation.column)
        
        annotation.type = t
        return t
    
    def check_assignment(self, node: Assignment):
        """Type check assignment."""
        target_type = self.check_expression(node.target)
        value_type = self.check_expression(node.value, expected_type=target_type)
        
        if not can_coerce(value_type, target_type):
            raise VibeLangTypeError(
                f"Cannot assign {value_type} to {target_type}",
                node.line, node.column
            )
        
        node.type = target_type
    
    def check_if_statement(self, node: IfStatement):
        """Type check if statement."""
        condition_type = self.check_expression(node.condition)
        
        if not isinstance(condition_type, BoolType):
            raise VibeLangTypeError(
                f"If condition must be bool, got {condition_type}",
                node.line, node.column
            )
        
        # Check then block
        self.symbol_table = SymbolTable(self.symbol_table)
        for statement in node.then_block:
            self.check_statement(statement)
        self.symbol_table = self.symbol_table.parent
        
        # Check else block
        if node.else_block:
            self.symbol_table = SymbolTable(self.symbol_table)
            for statement in node.else_block:
                self.check_statement(statement)
            self.symbol_table = self.symbol_table.parent
    
    def check_while_statement(self, node: WhileStatement):
        """Type check while statement."""
        condition_type = self.check_expression(node.condition)
        
        if not isinstance(condition_type, BoolType):
            raise VibeLangTypeError(
                f"While condition must be bool, got {condition_type}",
                node.line, node.column
            )
        
        # Check body
        self.symbol_table = SymbolTable(self.symbol_table)
        for statement in node.body:
            self.check_statement(statement)
        self.symbol_table = self.symbol_table.parent
    
    def check_for_statement(self, node: ForStatement):
        """Type check for statement."""
        iterable_type = self.check_expression(node.iterable)
        
        if not isinstance(iterable_type, ArrayType):
            raise VibeLangTypeError(
                f"For loop requires array, got {iterable_type}",
                node.line, node.column
            )
        
        # Create new scope with loop variable
        self.symbol_table = SymbolTable(self.symbol_table)
        self.symbol_table.define(node.variable, iterable_type.element_type)
        
        for statement in node.body:
            self.check_statement(statement)
        
        self.symbol_table = self.symbol_table.parent
    
    def check_return_statement(self, node: ReturnStatement):
        """Type check return statement."""
        if self.current_function_return_type is None:
            raise VibeLangTypeError(
                "Return statement outside function",
                node.line, node.column
            )
        
        if node.value:
            return_type = self.check_expression(node.value)
            if not can_coerce(return_type, self.current_function_return_type):
                raise VibeLangTypeError(
                    f"Cannot return {return_type}, expected {self.current_function_return_type}",
                    node.line, node.column
                )
        else:
            if not isinstance(self.current_function_return_type, VoidType):
                raise VibeLangTypeError(
                    f"Function must return {self.current_function_return_type}",
                    node.line, node.column
                )
    
    def check_expression(self, node: ASTNode, expected_type: Optional[Type] = None) -> Type:
        """Type check expression and return its type."""
        if isinstance(node, IntLiteral):
            node.type = IntType()
            return node.type
        
        elif isinstance(node, FloatLiteral):
            node.type = FloatType()
            return node.type
        
        elif isinstance(node, StringLiteral):
            node.type = StringType()
            return node.type
        
        elif isinstance(node, CharLiteral):
            node.type = CharType()
            return node.type
        
        elif isinstance(node, BoolLiteral):
            node.type = BoolType()
            return node.type
        
        elif isinstance(node, NullLiteral):
            node.type = NullType()
            return node.type
        elif isinstance(node, ArrayLiteral):
            if not node.elements:
                if expected_type and isinstance(expected_type, ArrayType):
                    node.type = expected_type
                    return expected_type
                raise VibeLangTypeError(
                    "Cannot infer type of empty array",
                    node.line, node.column
                )
            
            element_hint = expected_type.element_type if isinstance(expected_type, ArrayType) else None
            element_type = self.check_expression(node.elements[0], element_hint)
            for elem in node.elements[1:]:
                elem_type = self.check_expression(elem)
                if elem_type != element_type:
                    raise VibeLangTypeError(
                        f"Array elements must have same type, got {element_type} and {elem_type}",
                        node.line, node.column
                    )
            
            node.type = ArrayType(element_type)
            return node.type
        
        elif isinstance(node, Identifier):
            var_type = self.symbol_table.lookup(node.name)
            if var_type is None:
                raise VibeLangTypeError(
                    f"Undefined variable: '{node.name}'",
                    node.line, node.column
                )
            node.type = var_type
            return var_type
        
        elif isinstance(node, BinaryOp):
            return self.check_binary_op(node)
        
        elif isinstance(node, UnaryOp):
            return self.check_unary_op(node)
        
        elif isinstance(node, FunctionCall):
            return self.check_function_call(node)
        
        elif isinstance(node, MethodCall):
            return self.check_method_call(node)
        
        elif isinstance(node, ArrayIndex):
            return self.check_array_index(node)
        
        elif isinstance(node, StructLiteral):
            return self.check_struct_literal(node)
        
        elif isinstance(node, MemberAccess):
            return self.check_member_access(node)
        
        elif isinstance(node, Assignment):
            self.check_assignment(node)
            return node.type
        
        else:
            raise VibeLangTypeError(
                f"Unknown expression type: {type(node).__name__}",
                node.line, node.column
            )
    
    def check_binary_op(self, node: BinaryOp) -> Type:
        """Type check binary operation."""
        left_type = self.check_expression(node.left)
        right_type = self.check_expression(node.right)
        
        # Arithmetic operators
        if node.operator in ['+', '-', '*', '/', '%']:
            if node.operator == '+' and isinstance(left_type, StringType) and isinstance(right_type, StringType):
                node.type = StringType()
                return node.type
            
            if not (is_numeric_type(left_type) and is_numeric_type(right_type)):
                raise VibeLangTypeError(
                    f"Operator '{node.operator}' requires numeric types, got {left_type} and {right_type}",
                    node.line, node.column
                )
            
            result_type = common_type(left_type, right_type)
            node.type = result_type
            return result_type
        
        # Comparison operators
        elif node.operator in ['<', '<=', '>', '>=']:
            if not (is_numeric_type(left_type) and is_numeric_type(right_type)):
                raise VibeLangTypeError(
                    f"Operator '{node.operator}' requires numeric types, got {left_type} and {right_type}",
                    node.line, node.column
                )
            node.type = BoolType()
            return node.type
        
        # Equality operators
        elif node.operator in ['==', '!=']:
            if left_type == right_type:
                node.type = BoolType()
                return node.type
            
            # Allow comparison with null
            if (isinstance(left_type, NullType) and (isinstance(right_type, ArrayType) or isinstance(right_type, StructType))) or \
               (isinstance(right_type, NullType) and (isinstance(left_type, ArrayType) or isinstance(left_type, StructType))):
                node.type = BoolType()
                return node.type
                
            raise VibeLangTypeError(
                f"Cannot compare {left_type} and {right_type}",
                node.line, node.column
            )
        
        # Logical operators
        elif node.operator in ['and', 'or']:
            if not (isinstance(left_type, BoolType) and isinstance(right_type, BoolType)):
                raise VibeLangTypeError(
                    f"Operator '{node.operator}' requires bool types, got {left_type} and {right_type}",
                    node.line, node.column
                )
            node.type = BoolType()
            return node.type
        
        else:
            raise VibeLangTypeError(
                f"Unknown binary operator: {node.operator}",
                node.line, node.column
            )
    
    def check_unary_op(self, node: UnaryOp) -> Type:
        """Type check unary operation."""
        operand_type = self.check_expression(node.operand)
        
        if node.operator == '-':
            if not is_numeric_type(operand_type):
                raise VibeLangTypeError(
                    f"Unary minus requires numeric type, got {operand_type}",
                    node.line, node.column
                )
            node.type = operand_type
            return operand_type
        
        elif node.operator == 'not':
            if not isinstance(operand_type, BoolType):
                raise VibeLangTypeError(
                    f"Logical not requires bool type, got {operand_type}",
                    node.line, node.column
                )
            node.type = BoolType()
            return node.type
        
        else:
            raise VibeLangTypeError(
                f"Unknown unary operator: {node.operator}",
                node.line, node.column
            )
    
    def check_function_call(self, node: FunctionCall) -> Type:
        """Type check function call."""
        func_type = self.check_expression(node.function)
        
        if not isinstance(func_type, FunctionType):
            raise VibeLangTypeError(
                f"Cannot call non-function type: {func_type}",
                node.line, node.column
            )
        
        # Check argument count
        if len(node.arguments) != len(func_type.parameter_types):
            raise VibeLangTypeError(
                f"Function expects {len(func_type.parameter_types)} arguments, got {len(node.arguments)}",
                node.line, node.column
            )
        
        # Check argument types
        for i, (arg, param_type) in enumerate(zip(node.arguments, func_type.parameter_types)):
            arg_type = self.check_expression(arg, expected_type=param_type)
            
            # Special case for print - accept any type
            if isinstance(node.function, Identifier) and node.function.name == 'print':
                continue
            
            # Special case for len - accept any array type
            if isinstance(node.function, Identifier) and node.function.name == 'len':
                if not isinstance(arg_type, ArrayType):
                    raise VibeLangTypeError(
                        f"len() requires array type, got {arg_type}",
                        node.line, node.column
                    )
                continue
            
            if not can_coerce(arg_type, param_type):
                raise VibeLangTypeError(
                    f"Argument {i+1}: cannot pass {arg_type} to parameter of type {param_type}",
                    node.line, node.column
                )
        
        node.type = func_type.return_type
        return func_type.return_type
    
    def check_array_index(self, node: ArrayIndex) -> Type:
        """Type check array indexing."""
        array_type = self.check_expression(node.array)
        index_type = self.check_expression(node.index)
        
        if isinstance(array_type, StringType):
            if not isinstance(index_type, IntType):
                raise VibeLangTypeError(
                    f"String index must be int, got {index_type}",
                    node.line, node.column
                )
            node.type = CharType()
            return CharType()
            
        if not isinstance(array_type, ArrayType):
            raise VibeLangTypeError(
                f"Cannot index non-array type: {array_type}",
                node.line, node.column
            )
        
        if not isinstance(index_type, IntType):
            raise VibeLangTypeError(
                f"Array index must be int, got {index_type}",
                node.line, node.column
            )
        
        node.type = array_type.element_type
        return array_type.element_type

    def check_struct_literal(self, node: StructLiteral) -> Type:
        """Type check struct literal."""
        if node.name not in self.struct_types:
            raise VibeLangTypeError(f"Unknown struct type: {node.name}", node.line, node.column)
        
        struct_type = self.struct_types[node.name]
        
        # Check field count
        if len(node.fields) != len(struct_type.fields):
            raise VibeLangTypeError(
                f"Struct '{node.name}' expects {len(struct_type.fields)} fields, got {len(node.fields)}",
                node.line, node.column
            )
        
        # Check field names and types
        for field_name, field_value in node.fields.items():
            if field_name not in struct_type.fields:
                raise VibeLangTypeError(
                    f"Struct '{node.name}' has no field '{field_name}'",
                    node.line, node.column
                )
            
            expected_type = struct_type.fields[field_name]
            actual_type = self.check_expression(field_value, expected_type)
            
            if not can_coerce(actual_type, expected_type):
                raise VibeLangTypeError(
                    f"Field '{field_name}': cannot assign {actual_type} to {expected_type}",
                    node.line, node.column
                )
        
        node.type = struct_type
        return struct_type

    def check_member_access(self, node: MemberAccess) -> Type:
        """Type check member access."""
        obj_type = self.check_expression(node.object)
        
        if not isinstance(obj_type, StructType):
            raise VibeLangTypeError(
                f"Cannot access member '{node.member_name}' on non-struct type {obj_type}",
                node.line, node.column
            )
        
        if node.member_name not in obj_type.fields:
            raise VibeLangTypeError(
                f"Struct '{obj_type.name}' has no member '{node.member_name}'",
                node.line, node.column
            )
        
        node.type = obj_type.fields[node.member_name]
        return node.type

    def check_method_call(self, node: MethodCall) -> Type:
        """Type check method call."""
        obj_type = self.check_expression(node.object)
        
        if isinstance(obj_type, ArrayType):
            if node.method_name == 'push':
                if len(node.arguments) != 1:
                    raise VibeLangTypeError(
                        f"push() expects 1 argument, got {len(node.arguments)}",
                        node.line, node.column
                    )
                arg_type = self.check_expression(node.arguments[0], expected_type=obj_type.element_type)
                if not can_coerce(arg_type, obj_type.element_type):
                    raise VibeLangTypeError(
                        f"Cannot push {arg_type} to array of {obj_type.element_type}",
                        node.line, node.column
                    )
                node.type = VoidType()
                return node.type
            
            elif node.method_name == 'pop':
                if len(node.arguments) != 0:
                    raise VibeLangTypeError(
                        f"pop() expects 0 arguments, got {len(node.arguments)}",
                        node.line, node.column
                    )
                node.type = obj_type.element_type
                return node.type
            
            else:
                raise VibeLangTypeError(
                    f"Array has no method '{node.method_name}'",
                    node.line, node.column
                )
        
        raise VibeLangTypeError(
            f"Type {obj_type} has no methods",
            node.line, node.column
        )
