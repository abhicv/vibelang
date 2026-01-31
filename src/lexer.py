"""
Lexical analyzer (tokenizer) for VibeLang.
Converts source code into a stream of tokens.
"""

from enum import Enum, auto
from dataclasses import dataclass
from typing import List, Optional
from .errors import VibeLangError, LexerError


class TokenType(Enum):
    # Literals
    INT_LITERAL = auto()
    FLOAT_LITERAL = auto()
    STRING_LITERAL = auto()
    TRUE = auto()
    FALSE = auto()
    
    # Identifiers and keywords
    IDENTIFIER = auto()
    
    # Keywords
    LET = auto()
    FN = auto()
    RETURN = auto()
    IF = auto()
    ELSE = auto()
    WHILE = auto()
    FOR = auto()
    IN = auto()
    IMPORT = auto()
    NULL = auto()
    
    # Types
    INT_TYPE = auto()
    FLOAT_TYPE = auto()
    BOOL_TYPE = auto()
    STRING_TYPE = auto()
    CHAR_TYPE = auto()
    
    # Operators
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    PERCENT = auto()
    
    # Comparison
    EQ = auto()
    NE = auto()
    LT = auto()
    LE = auto()
    GT = auto()
    GE = auto()
    
    # Logical
    AND = auto()
    OR = auto()
    NOT = auto()
    
    # Assignment
    ASSIGN = auto()
    
    # Delimiters
    LPAREN = auto()
    RPAREN = auto()
    LBRACE = auto()
    RBRACE = auto()
    LBRACKET = auto()
    RBRACKET = auto()
    COMMA = auto()
    SEMICOLON = auto()
    COLON = auto()
    ARROW = auto()
    DOT = auto()
    STRUCT = auto()
    CHAR_LITERAL = auto()
    
    # Special
    EOF = auto()


@dataclass
class Token:
    type: TokenType
    value: any
    line: int
    column: int
    
    def __repr__(self):
        return f"Token({self.type.name}, {self.value!r}, {self.line}:{self.column})"


class Lexer:
    """Tokenizes VibeLang source code."""
    
    KEYWORDS = {
        'let': TokenType.LET,
        'fn': TokenType.FN,
        'return': TokenType.RETURN,
        'if': TokenType.IF,
        'else': TokenType.ELSE,
        'while': TokenType.WHILE,
        'for': TokenType.FOR,
        'in': TokenType.IN,
        'true': TokenType.TRUE,
        'false': TokenType.FALSE,
        'int': TokenType.INT_TYPE,
        'float': TokenType.FLOAT_TYPE,
        'bool': TokenType.BOOL_TYPE,
        'string': TokenType.STRING_TYPE,
        'char': TokenType.CHAR_TYPE,
        'and': TokenType.AND,
        'or': TokenType.OR,
        'not': TokenType.NOT,
        'struct': TokenType.STRUCT,
        'import': TokenType.IMPORT,
        'null': TokenType.NULL,
    }
    
    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.line = 1
        self.column = 1
        self.tokens: List[Token] = []
    
    def current_char(self) -> Optional[str]:
        """Get current character without advancing."""
        if self.pos >= len(self.source):
            return None
        return self.source[self.pos]
    
    def peek_char(self, offset: int = 1) -> Optional[str]:
        """Look ahead at character without advancing."""
        pos = self.pos + offset
        if pos >= len(self.source):
            return None
        return self.source[pos]
    
    def advance(self) -> Optional[str]:
        """Move to next character and return current."""
        if self.pos >= len(self.source):
            return None
        char = self.source[self.pos]
        self.pos += 1
        if char == '\n':
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return char
    
    def skip_whitespace(self):
        """Skip whitespace characters."""
        while self.current_char() and self.current_char() in ' \t\n\r':
            self.advance()
    
    def skip_line_comment(self):
        """Skip single-line comment starting with //"""
        self.advance()  # /
        self.advance()  # /
        while self.current_char() and self.current_char() != '\n':
            self.advance()
    
    def skip_block_comment(self):
        """Skip multi-line comment /* ... */"""
        start_line = self.line
        self.advance()  # /
        self.advance()  # *
        
        while True:
            if self.current_char() is None:
                raise LexerError("Unterminated block comment", start_line, 1)
            if self.current_char() == '*' and self.peek_char() == '/':
                self.advance()  # *
                self.advance()  # /
                break
            self.advance()
    
    def read_number(self) -> Token:
        """Read integer or float literal."""
        start_line = self.line
        start_column = self.column
        num_str = ''
        is_float = False
        
        while self.current_char() and (self.current_char().isdigit() or self.current_char() == '.'):
            if self.current_char() == '.':
                if is_float:
                    raise LexerError("Invalid number format", self.line, self.column)
                is_float = True
            num_str += self.current_char()
            self.advance()
        
        if is_float:
            return Token(TokenType.FLOAT_LITERAL, float(num_str), start_line, start_column)
        else:
            return Token(TokenType.INT_LITERAL, int(num_str), start_line, start_column)
    
    def read_string(self) -> Token:
        """Read string literal."""
        start_line = self.line
        start_column = self.column
        self.advance()  # opening quote
        
        string_value = ''
        while self.current_char() and self.current_char() != '"':
            if self.current_char() == '\\':
                self.advance()
                next_char = self.current_char()
                if next_char == 'n':
                    string_value += '\n'
                elif next_char == 't':
                    string_value += '\t'
                elif next_char == '\\':
                    string_value += '\\'
                elif next_char == '"':
                    string_value += '"'
                else:
                    string_value += next_char
                self.advance()
            else:
                string_value += self.current_char()
                self.advance()
        
        if self.current_char() != '"':
            raise LexerError("Unterminated string", start_line, start_column)
        
        self.advance()  # closing quote
        return Token(TokenType.STRING_LITERAL, string_value, start_line, start_column)
    
    def read_char_literal(self) -> Token:
        """Read character literal."""
        start_line = self.line
        start_column = self.column
        self.advance()  # opening quote
        
        char_value = ''
        if self.current_char() == '\\':
            self.advance()
            next_char = self.current_char()
            if next_char == 'n': char_value = '\n'
            elif next_char == 't': char_value = '\t'
            elif next_char == 'r': char_value = '\r'
            elif next_char == '\\': char_value = '\\'
            elif next_char == '\'': char_value = '\''
            else: char_value = next_char
            self.advance()
        else:
            char_value = self.current_char()
            self.advance()
            
        if self.current_char() != '\'':
            raise LexerError("Unterminated character literal", start_line, start_column)
            
        self.advance()  # closing quote
        return Token(TokenType.CHAR_LITERAL, char_value, start_line, start_column)
    
    def read_identifier(self) -> Token:
        """Read identifier or keyword."""
        start_line = self.line
        start_column = self.column
        identifier = ''
        
        while self.current_char() and (self.current_char().isalnum() or self.current_char() == '_'):
            identifier += self.current_char()
            self.advance()
        
        token_type = self.KEYWORDS.get(identifier, TokenType.IDENTIFIER)
        value = identifier if token_type == TokenType.IDENTIFIER else None
        
        return Token(token_type, value, start_line, start_column)
    
    def tokenize(self) -> List[Token]:
        """Tokenize the entire source code."""
        while self.pos < len(self.source):
            self.skip_whitespace()
            
            if self.current_char() is None:
                break
            
            # Comments
            if self.current_char() == '/' and self.peek_char() == '/':
                self.skip_line_comment()
                continue
            
            if self.current_char() == '/' and self.peek_char() == '*':
                self.skip_block_comment()
                continue
            
            # Numbers
            if self.current_char().isdigit():
                self.tokens.append(self.read_number())
                continue
            
            # Strings
            if self.current_char() == '"':
                self.tokens.append(self.read_string())
                continue
            
            if self.current_char() == '\'':
                self.tokens.append(self.read_char_literal())
                continue
            
            # Identifiers and keywords
            if self.current_char().isalpha() or self.current_char() == '_':
                self.tokens.append(self.read_identifier())
                continue
            
            # Operators and delimiters
            start_line = self.line
            start_column = self.column
            char = self.current_char()
            
            # Two-character operators
            if char == '=' and self.peek_char() == '=':
                self.advance()
                self.advance()
                self.tokens.append(Token(TokenType.EQ, None, start_line, start_column))
            elif char == '!' and self.peek_char() == '=':
                self.advance()
                self.advance()
                self.tokens.append(Token(TokenType.NE, None, start_line, start_column))
            elif char == '<' and self.peek_char() == '=':
                self.advance()
                self.advance()
                self.tokens.append(Token(TokenType.LE, None, start_line, start_column))
            elif char == '>' and self.peek_char() == '=':
                self.advance()
                self.advance()
                self.tokens.append(Token(TokenType.GE, None, start_line, start_column))
            elif char == '-' and self.peek_char() == '>':
                self.advance()
                self.advance()
                self.tokens.append(Token(TokenType.ARROW, None, start_line, start_column))
            # Single-character operators
            elif char == '+':
                self.advance()
                self.tokens.append(Token(TokenType.PLUS, None, start_line, start_column))
            elif char == '-':
                self.advance()
                self.tokens.append(Token(TokenType.MINUS, None, start_line, start_column))
            elif char == '*':
                self.advance()
                self.tokens.append(Token(TokenType.STAR, None, start_line, start_column))
            elif char == '/':
                self.advance()
                self.tokens.append(Token(TokenType.SLASH, None, start_line, start_column))
            elif char == '%':
                self.advance()
                self.tokens.append(Token(TokenType.PERCENT, None, start_line, start_column))
            elif char == '<':
                self.advance()
                self.tokens.append(Token(TokenType.LT, None, start_line, start_column))
            elif char == '>':
                self.advance()
                self.tokens.append(Token(TokenType.GT, None, start_line, start_column))
            elif char == '=':
                self.advance()
                self.tokens.append(Token(TokenType.ASSIGN, None, start_line, start_column))
            elif char == '(':
                self.advance()
                self.tokens.append(Token(TokenType.LPAREN, None, start_line, start_column))
            elif char == ')':
                self.advance()
                self.tokens.append(Token(TokenType.RPAREN, None, start_line, start_column))
            elif char == '{':
                self.advance()
                self.tokens.append(Token(TokenType.LBRACE, None, start_line, start_column))
            elif char == '}':
                self.advance()
                self.tokens.append(Token(TokenType.RBRACE, None, start_line, start_column))
            elif char == '[':
                self.advance()
                self.tokens.append(Token(TokenType.LBRACKET, None, start_line, start_column))
            elif char == ']':
                self.advance()
                self.tokens.append(Token(TokenType.RBRACKET, None, start_line, start_column))
            elif char == ',':
                self.advance()
                self.tokens.append(Token(TokenType.COMMA, None, start_line, start_column))
            elif char == ';':
                self.advance()
                self.tokens.append(Token(TokenType.SEMICOLON, None, start_line, start_column))
            elif char == ':':
                self.advance()
                self.tokens.append(Token(TokenType.COLON, None, start_line, start_column))
            elif char == '.':
                self.advance()
                self.tokens.append(Token(TokenType.DOT, None, start_line, start_column))
            else:
                raise LexerError(f"Unexpected character: '{char}'", self.line, self.column)
        
        # Add EOF token
        self.tokens.append(Token(TokenType.EOF, None, self.line, self.column))
        return self.tokens
