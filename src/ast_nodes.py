"""
Abstract Syntax Tree node definitions for VibeLang.
"""

from dataclasses import dataclass
from typing import List, Optional, Any, Dict


class ASTNode:
    """Base class for all AST nodes."""
    def __init__(self, line: int, column: int):
        self.line = line
        self.column = column
        self.type = None  # Will be set by type checker


# Literals
@dataclass
class IntLiteral(ASTNode):
    value: int
    
    def __init__(self, value: int, line: int, column: int):
        super().__init__(line, column)
        self.value = value


@dataclass
class FloatLiteral(ASTNode):
    value: float
    
    def __init__(self, value: float, line: int, column: int):
        super().__init__(line, column)
        self.value = value


@dataclass
class StringLiteral(ASTNode):
    value: str
    
    def __init__(self, value: str, line: int, column: int):
        super().__init__(line, column)
        self.value = value


@dataclass
class CharLiteral(ASTNode):
    value: str
    
    def __init__(self, value: str, line: int, column: int):
        super().__init__(line, column)
        self.value = value

@dataclass
class BoolLiteral(ASTNode):
    value: bool
    
    def __init__(self, value: bool, line: int, column: int):
        super().__init__(line, column)
        self.value = value


@dataclass
class NullLiteral(ASTNode):
    def __init__(self, line: int, column: int):
        super().__init__(line, column)


@dataclass
class ArrayLiteral(ASTNode):
    elements: List[ASTNode]
    
    def __init__(self, elements: List[ASTNode], line: int, column: int):
        super().__init__(line, column)
        self.elements = elements


# Variables and identifiers
@dataclass
class Identifier(ASTNode):
    name: str
    
    def __init__(self, name: str, line: int, column: int):
        super().__init__(line, column)
        self.name = name


# Binary operations
@dataclass
class BinaryOp(ASTNode):
    left: ASTNode
    operator: str
    right: ASTNode
    
    def __init__(self, left: ASTNode, operator: str, right: ASTNode, line: int, column: int):
        super().__init__(line, column)
        self.left = left
        self.operator = operator
        self.right = right


# Unary operations
@dataclass
class UnaryOp(ASTNode):
    operator: str
    operand: ASTNode
    
    def __init__(self, operator: str, operand: ASTNode, line: int, column: int):
        super().__init__(line, column)
        self.operator = operator
        self.operand = operand


# Function call
@dataclass
class FunctionCall(ASTNode):
    function: ASTNode  # Usually an Identifier
    arguments: List[ASTNode]
    
    def __init__(self, function: ASTNode, arguments: List[ASTNode], line: int, column: int):
        super().__init__(line, column)
        self.function = function
        self.arguments = arguments


# Array indexing
@dataclass
class ArrayIndex(ASTNode):
    array: ASTNode
    index: ASTNode
    
    def __init__(self, array: ASTNode, index: ASTNode, line: int, column: int):
        super().__init__(line, column)
        self.array = array
        self.index = index


# Method call (e.g., array.push(value))
@dataclass
class MethodCall(ASTNode):
    object: ASTNode  # The object the method is called on
    method_name: str
    arguments: List[ASTNode]
    
    def __init__(self, object: ASTNode, method_name: str, arguments: List[ASTNode], line: int, column: int):
        super().__init__(line, column)
        self.object = object
        self.method_name = method_name
        self.arguments = arguments


# Type annotations
@dataclass
class TypeAnnotation(ASTNode):
    type_name: str
    element_type: Optional['TypeAnnotation'] = None  # For array types
    
    def __init__(self, type_name: str, line: int, column: int, element_type: Optional['TypeAnnotation'] = None):
        super().__init__(line, column)
        self.type_name = type_name
        self.element_type = element_type


@dataclass
class StructField:
    name: str
    type_annotation: TypeAnnotation
    
    def __init__(self, name: str, type_annotation: TypeAnnotation):
        self.name = name
        self.type_annotation = type_annotation


@dataclass
class StructDefinition(ASTNode):
    name: str
    fields: List[StructField]
    
    def __init__(self, name: str, fields: List[StructField], line: int, column: int):
        super().__init__(line, column)
        self.name = name
        self.fields = fields


@dataclass
class StructLiteral(ASTNode):
    name: str
    fields: Dict[str, ASTNode]
    
    def __init__(self, name: str, fields: Dict[str, ASTNode], line: int, column: int):
        super().__init__(line, column)
        self.name = name
        self.fields = fields


@dataclass
class MemberAccess(ASTNode):
    object: ASTNode
    member_name: str
    
    def __init__(self, object: ASTNode, member_name: str, line: int, column: int):
        super().__init__(line, column)
        self.object = object
        self.member_name = member_name


# Statements
@dataclass
class VariableDeclaration(ASTNode):
    name: str
    type_annotation: Optional[TypeAnnotation]
    initializer: Optional[ASTNode]
    
    def __init__(self, name: str, type_annotation: Optional[TypeAnnotation], 
                 initializer: Optional[ASTNode], line: int, column: int):
        super().__init__(line, column)
        self.name = name
        self.type_annotation = type_annotation
        self.initializer = initializer


@dataclass
class Assignment(ASTNode):
    target: ASTNode  # Identifier or ArrayIndex
    value: ASTNode
    
    def __init__(self, target: ASTNode, value: ASTNode, line: int, column: int):
        super().__init__(line, column)
        self.target = target
        self.value = value


@dataclass
class IfStatement(ASTNode):
    condition: ASTNode
    then_block: List[ASTNode]
    else_block: Optional[List[ASTNode]]
    
    def __init__(self, condition: ASTNode, then_block: List[ASTNode], 
                 else_block: Optional[List[ASTNode]], line: int, column: int):
        super().__init__(line, column)
        self.condition = condition
        self.then_block = then_block
        self.else_block = else_block


@dataclass
class WhileStatement(ASTNode):
    condition: ASTNode
    body: List[ASTNode]
    
    def __init__(self, condition: ASTNode, body: List[ASTNode], line: int, column: int):
        super().__init__(line, column)
        self.condition = condition
        self.body = body


@dataclass
class ForStatement(ASTNode):
    variable: str
    iterable: ASTNode
    body: List[ASTNode]
    
    def __init__(self, variable: str, iterable: ASTNode, body: List[ASTNode], line: int, column: int):
        super().__init__(line, column)
        self.variable = variable
        self.iterable = iterable
        self.body = body


@dataclass
class ReturnStatement(ASTNode):
    value: Optional[ASTNode]
    
    def __init__(self, value: Optional[ASTNode], line: int, column: int):
        super().__init__(line, column)
        self.value = value


@dataclass
class ExpressionStatement(ASTNode):
    expression: ASTNode
    
    def __init__(self, expression: ASTNode, line: int, column: int):
        super().__init__(line, column)
        self.expression = expression


@dataclass
class Import(ASTNode):
    path: str
    
    def __init__(self, path: str, line: int, column: int):
        super().__init__(line, column)
        self.path = path


# Function definition
@dataclass
class Parameter:
    name: str
    type_annotation: TypeAnnotation
    
    def __init__(self, name: str, type_annotation: TypeAnnotation):
        self.name = name
        self.type_annotation = type_annotation


@dataclass
class FunctionDeclaration(ASTNode):
    name: str
    parameters: List[Parameter]
    return_type: TypeAnnotation
    body: List[ASTNode]
    
    def __init__(self, name: str, parameters: List[Parameter], return_type: TypeAnnotation,
                 body: List[ASTNode], line: int, column: int):
        super().__init__(line, column)
        self.name = name
        self.parameters = parameters
        self.return_type = return_type
        self.body = body


# Program (root node)
@dataclass
class Program(ASTNode):
    statements: List[ASTNode]
    
    def __init__(self, statements: List[ASTNode]):
        super().__init__(1, 1)
        self.statements = statements
