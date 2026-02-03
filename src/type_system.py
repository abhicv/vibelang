"""
Type system definitions for VibeLang.
"""

from dataclasses import dataclass
from typing import Optional, List, Dict


class Type:
    """Base class for all types."""
    def __eq__(self, other):
        return type(self) == type(other)
    
    def __hash__(self):
        return hash(type(self))
    
    def __str__(self):
        return self.__class__.__name__


class IntType(Type):
    """Integer type."""
    def __str__(self):
        return 'int'


class FloatType(Type):
    """Floating-point type."""
    def __str__(self):
        return 'float'


class BoolType(Type):
    """Boolean type."""
    def __str__(self):
        return 'bool'


class StringType(Type):
    """String type."""
    def __str__(self):
        return 'string'


class CharType(Type):
    """Character type."""
    def __str__(self):
        return 'char'


@dataclass
class ArrayType(Type):
    """Array type with element type."""
    element_type: Type
    
    def __eq__(self, other):
        return isinstance(other, ArrayType) and self.element_type == other.element_type
    
    def __hash__(self):
        return hash(('array', self.element_type))
    
    def __str__(self):
        return f'[{self.element_type}]'


@dataclass
class FunctionType(Type):
    """Function type with parameter types and return type."""
    parameter_types: List[Type]
    return_type: Type
    
    def __eq__(self, other):
        return (isinstance(other, FunctionType) and 
                self.parameter_types == other.parameter_types and
                self.return_type == other.return_type)
    
    def __hash__(self):
        return hash(('function', tuple(self.parameter_types), self.return_type))
    
    def __str__(self):
        params = ', '.join(str(t) for t in self.parameter_types)
        return f'fn({params}) -> {self.return_type}'


@dataclass
class StructType(Type):
    """User-defined struct type."""
    name: str
    fields: Dict[str, Type]
    
    def __eq__(self, other):
        return isinstance(other, StructType) and self.name == other.name
    
    def __hash__(self):
        return hash(('struct', self.name))
    
    def __str__(self):
        return self.name


@dataclass
class MultiType(Type):
    """Multiple return values type."""
    types: List[Type]
    
    def __eq__(self, other):
        return isinstance(other, MultiType) and self.types == other.types
    
    def __hash__(self):
        return hash(('multi', tuple(self.types)))
    
    def __str__(self):
        return f"({', '.join(str(t) for t in self.types)})"


class VoidType(Type):
    """Void type (for functions that don't return a value)."""
    def __str__(self):
        return 'void'


class NullType(Type):
    """Null type (for the null literal)."""
    def __str__(self):
        return 'null'


def type_from_annotation(annotation) -> Type:
    """Convert type annotation to Type object."""
    if annotation.type_name == 'int':
        return IntType()
    elif annotation.type_name == 'float':
        return FloatType()
    elif annotation.type_name == 'bool':
        return BoolType()
    elif annotation.type_name == 'string':
        return StringType()
    elif annotation.type_name == 'array':
        element_type = type_from_annotation(annotation.element_type)
        return ArrayType(element_type)
    elif annotation.type_name == 'tuple':
        types = [type_from_annotation(t) for t in annotation.types]
        return MultiType(types)
    else:
        # Assume struct
        return StructType(annotation.type_name, {})


def is_numeric_type(t: Type) -> bool:
    """Check if type is numeric (int or float)."""
    return isinstance(t, (IntType, FloatType))


def can_coerce(from_type: Type, to_type: Type) -> bool:
    """Check if from_type can be coerced to to_type."""
    if from_type == to_type:
        return True
    
    # Int can be coerced to float
    if isinstance(from_type, IntType) and isinstance(to_type, FloatType):
        return True
    
    # Null can be coerced to array or struct
    if isinstance(from_type, NullType) and (isinstance(to_type, ArrayType) or isinstance(to_type, StructType)):
        return True
    
    # MultiType coercion
    if isinstance(from_type, MultiType) and isinstance(to_type, MultiType):
        if len(from_type.types) != len(to_type.types):
            return False
        return all(can_coerce(f, t) for f, t in zip(from_type.types, to_type.types))
    
    return False


def common_type(type1: Type, type2: Type) -> Optional[Type]:
    """Find common type for two types (for binary operations)."""
    if type1 == type2:
        return type1
    
    # Int and float -> float
    if isinstance(type1, IntType) and isinstance(type2, FloatType):
        return FloatType()
    if isinstance(type1, FloatType) and isinstance(type2, IntType):
        return FloatType()
    
    return None
