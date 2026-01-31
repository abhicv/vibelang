"""
Recursive descent parser for VibeLang.
Builds an Abstract Syntax Tree from token stream.
"""

from typing import List, Optional
from .lexer import Token, TokenType
from .ast_nodes import *
from .errors import ParserError


class Parser:
    """Parses VibeLang tokens into an AST."""
    
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0
        self.struct_names = set()
    
    def current_token(self) -> Token:
        """Get current token."""
        if self.pos >= len(self.tokens):
            return self.tokens[-1]  # EOF
        return self.tokens[self.pos]
    
    def peek_token(self, offset: int = 1) -> Token:
        """Look ahead at token."""
        pos = self.pos + offset
        if pos >= len(self.tokens):
            return self.tokens[-1]  # EOF
        return self.tokens[pos]
    
    def advance(self) -> Token:
        """Move to next token and return current."""
        token = self.current_token()
        if self.pos < len(self.tokens) - 1:
            self.pos += 1
        return token
    
    def expect(self, token_type: TokenType) -> Token:
        """Consume token of expected type or raise error."""
        token = self.current_token()
        if token.type != token_type:
            raise ParserError(
                f"Expected {token_type.name}, got {token.type.name}",
                token.line, token.column
            )
        return self.advance()
    
    def match(self, *token_types: TokenType) -> bool:
        """Check if current token matches any of the given types."""
        return self.current_token().type in token_types
    
    def parse(self) -> Program:
        """Parse the entire program."""
        # First pass to collect struct names
        old_pos = self.pos
        while not self.match(TokenType.EOF):
            if self.match(TokenType.STRUCT):
                self.advance()
                if self.match(TokenType.IDENTIFIER):
                    self.struct_names.add(self.advance().value)
                else:
                    self.pos -= 1 # Backtrack if not an identifier
                    self.advance()
            else:
                self.advance()
        self.pos = old_pos

        statements = []
        while not self.match(TokenType.EOF):
            statements.append(self.parse_statement())
        return Program(statements)
    
    def parse_statement(self) -> ASTNode:
        """Parse a statement."""
        if self.match(TokenType.IMPORT):
            return self.parse_import()
        elif self.match(TokenType.LET):
            return self.parse_variable_declaration()
        elif self.match(TokenType.FN):
            return self.parse_function_declaration()
        elif self.match(TokenType.STRUCT):
            return self.parse_struct_definition()
        elif self.match(TokenType.RETURN):
            return self.parse_return_statement()
        elif self.match(TokenType.IF):
            return self.parse_if_statement()
        elif self.match(TokenType.WHILE):
            return self.parse_while_statement()
        elif self.match(TokenType.FOR):
            return self.parse_for_statement()
        else:
            return self.parse_expression_statement()

    def parse_import(self) -> Import:
        """Parse: import "path";"""
        import_token = self.expect(TokenType.IMPORT)
        path_token = self.expect(TokenType.STRING_LITERAL)
        self.expect(TokenType.SEMICOLON)
        return Import(path_token.value, import_token.line, import_token.column)
    
    def parse_variable_declaration(self) -> VariableDeclaration:
        """Parse: let name: type = value;"""
        let_token = self.expect(TokenType.LET)
        name_token = self.expect(TokenType.IDENTIFIER)
        name = name_token.value
        
        type_annotation = None
        if self.match(TokenType.COLON):
            self.advance()
            type_annotation = self.parse_type_annotation()
        
        initializer = None
        if self.match(TokenType.ASSIGN):
            self.advance()
            initializer = self.parse_expression()
        
        self.expect(TokenType.SEMICOLON)
        
        return VariableDeclaration(name, type_annotation, initializer, let_token.line, let_token.column)
    
    def parse_function_declaration(self) -> FunctionDeclaration:
        """Parse: fn name(params) -> return_type { body }"""
        fn_token = self.expect(TokenType.FN)
        name_token = self.expect(TokenType.IDENTIFIER)
        name = name_token.value
        
        self.expect(TokenType.LPAREN)
        parameters = self.parse_parameters()
        self.expect(TokenType.RPAREN)
        
        self.expect(TokenType.ARROW)
        return_type = self.parse_type_annotation()
        
        self.expect(TokenType.LBRACE)
        body = self.parse_block()
        self.expect(TokenType.RBRACE)
        
        return FunctionDeclaration(name, parameters, return_type, body, fn_token.line, fn_token.column)
    
    def parse_struct_definition(self) -> StructDefinition:
        """Parse: struct Name { field: type, ... }"""
        struct_token = self.expect(TokenType.STRUCT)
        name_token = self.expect(TokenType.IDENTIFIER)
        name = name_token.value
        
        self.expect(TokenType.LBRACE)
        fields = []
        while not self.match(TokenType.RBRACE):
            field_name_token = self.expect(TokenType.IDENTIFIER)
            self.expect(TokenType.COLON)
            field_type = self.parse_type_annotation()
            fields.append(StructField(field_name_token.value, field_type))
            
            if self.match(TokenType.COMMA):
                self.advance()
            else:
                break
        
        self.expect(TokenType.RBRACE)
        return StructDefinition(name, fields, struct_token.line, struct_token.column)
    
    def parse_parameters(self) -> List[Parameter]:
        """Parse function parameters."""
        parameters = []
        
        if not self.match(TokenType.RPAREN):
            while True:
                name_token = self.expect(TokenType.IDENTIFIER)
                self.expect(TokenType.COLON)
                type_annotation = self.parse_type_annotation()
                parameters.append(Parameter(name_token.value, type_annotation))
                
                if not self.match(TokenType.COMMA):
                    break
                self.advance()
        
        return parameters
    
    def parse_type_annotation(self) -> TypeAnnotation:
        """Parse type annotation."""
        token = self.current_token()
        
        if self.match(TokenType.INT_TYPE):
            self.advance()
            return TypeAnnotation('int', token.line, token.column)
        elif self.match(TokenType.FLOAT_TYPE):
            self.advance()
            return TypeAnnotation('float', token.line, token.column)
        elif self.match(TokenType.BOOL_TYPE):
            self.advance()
            return TypeAnnotation('bool', token.line, token.column)
        elif self.match(TokenType.STRING_TYPE):
            token = self.advance()
            return TypeAnnotation('string', token.line, token.column)
        elif self.match(TokenType.CHAR_TYPE):
            token = self.advance()
            return TypeAnnotation('char', token.line, token.column)
        elif self.match(TokenType.LBRACKET):
            self.advance()
            element_type = self.parse_type_annotation()
            self.expect(TokenType.RBRACKET)
            return TypeAnnotation('array', token.line, token.column, element_type)
        elif self.match(TokenType.IDENTIFIER):
            # Custom struct type
            self.advance()
            return TypeAnnotation(token.value, token.line, token.column)
        else:
            raise ParserError(f"Expected type annotation, got {token.type.name}", token.line, token.column)
    
    def parse_return_statement(self) -> ReturnStatement:
        """Parse: return expr;"""
        return_token = self.expect(TokenType.RETURN)
        
        value = None
        if not self.match(TokenType.SEMICOLON):
            value = self.parse_expression()
        
        self.expect(TokenType.SEMICOLON)
        return ReturnStatement(value, return_token.line, return_token.column)
    
    def parse_if_statement(self) -> IfStatement:
        """Parse: if condition { block } else { block }"""
        if_token = self.expect(TokenType.IF)
        condition = self.parse_expression()
        
        self.expect(TokenType.LBRACE)
        then_block = self.parse_block()
        self.expect(TokenType.RBRACE)
        
        else_block = None
        if self.match(TokenType.ELSE):
            self.advance()
            self.expect(TokenType.LBRACE)
            else_block = self.parse_block()
            self.expect(TokenType.RBRACE)
        
        return IfStatement(condition, then_block, else_block, if_token.line, if_token.column)
    
    def parse_while_statement(self) -> WhileStatement:
        """Parse: while condition { block }"""
        while_token = self.expect(TokenType.WHILE)
        condition = self.parse_expression()
        
        self.expect(TokenType.LBRACE)
        body = self.parse_block()
        self.expect(TokenType.RBRACE)
        
        return WhileStatement(condition, body, while_token.line, while_token.column)
    
    def parse_for_statement(self) -> ForStatement:
        """Parse: for variable in iterable { block }"""
        for_token = self.expect(TokenType.FOR)
        var_token = self.expect(TokenType.IDENTIFIER)
        self.expect(TokenType.IN)
        iterable = self.parse_expression()
        
        self.expect(TokenType.LBRACE)
        body = self.parse_block()
        self.expect(TokenType.RBRACE)
        
        return ForStatement(var_token.value, iterable, body, for_token.line, for_token.column)
    
    def parse_block(self) -> List[ASTNode]:
        """Parse a block of statements."""
        statements = []
        while not self.match(TokenType.RBRACE, TokenType.EOF):
            statements.append(self.parse_statement())
        return statements
    
    def parse_expression_statement(self) -> ExpressionStatement:
        """Parse expression statement or assignment."""
        expr = self.parse_expression()
        
        # Check for assignment
        if self.match(TokenType.ASSIGN):
            self.advance()
            value = self.parse_expression()
            self.expect(TokenType.SEMICOLON)
            return ExpressionStatement(
                Assignment(expr, value, expr.line, expr.column),
                expr.line, expr.column
            )
        
        self.expect(TokenType.SEMICOLON)
        return ExpressionStatement(expr, expr.line, expr.column)
    
    def parse_expression(self) -> ASTNode:
        """Parse expression (lowest precedence)."""
        return self.parse_logical_or()
    
    def parse_logical_or(self) -> ASTNode:
        """Parse logical OR expression."""
        left = self.parse_logical_and()
        
        while self.match(TokenType.OR):
            op_token = self.advance()
            right = self.parse_logical_and()
            left = BinaryOp(left, 'or', right, op_token.line, op_token.column)
        
        return left
    
    def parse_logical_and(self) -> ASTNode:
        """Parse logical AND expression."""
        left = self.parse_equality()
        
        while self.match(TokenType.AND):
            op_token = self.advance()
            right = self.parse_equality()
            left = BinaryOp(left, 'and', right, op_token.line, op_token.column)
        
        return left
    
    def parse_equality(self) -> ASTNode:
        """Parse equality expression."""
        left = self.parse_comparison()
        
        while self.match(TokenType.EQ, TokenType.NE):
            op_token = self.advance()
            op = '==' if op_token.type == TokenType.EQ else '!='
            right = self.parse_comparison()
            left = BinaryOp(left, op, right, op_token.line, op_token.column)
        
        return left
    
    def parse_comparison(self) -> ASTNode:
        """Parse comparison expression."""
        left = self.parse_additive()
        
        while self.match(TokenType.LT, TokenType.LE, TokenType.GT, TokenType.GE):
            op_token = self.advance()
            op_map = {
                TokenType.LT: '<',
                TokenType.LE: '<=',
                TokenType.GT: '>',
                TokenType.GE: '>='
            }
            op = op_map[op_token.type]
            right = self.parse_additive()
            left = BinaryOp(left, op, right, op_token.line, op_token.column)
        
        return left
    
    def parse_additive(self) -> ASTNode:
        """Parse addition/subtraction expression."""
        left = self.parse_multiplicative()
        
        while self.match(TokenType.PLUS, TokenType.MINUS):
            op_token = self.advance()
            op = '+' if op_token.type == TokenType.PLUS else '-'
            right = self.parse_multiplicative()
            left = BinaryOp(left, op, right, op_token.line, op_token.column)
        
        return left
    
    def parse_multiplicative(self) -> ASTNode:
        """Parse multiplication/division/modulo expression."""
        left = self.parse_unary()
        
        while self.match(TokenType.STAR, TokenType.SLASH, TokenType.PERCENT):
            op_token = self.advance()
            op_map = {
                TokenType.STAR: '*',
                TokenType.SLASH: '/',
                TokenType.PERCENT: '%'
            }
            op = op_map[op_token.type]
            right = self.parse_unary()
            left = BinaryOp(left, op, right, op_token.line, op_token.column)
        
        return left
    
    def parse_unary(self) -> ASTNode:
        """Parse unary expression."""
        if self.match(TokenType.MINUS, TokenType.NOT):
            op_token = self.advance()
            op = '-' if op_token.type == TokenType.MINUS else 'not'
            operand = self.parse_unary()
            return UnaryOp(op, operand, op_token.line, op_token.column)
        
        return self.parse_postfix()
    
    def parse_postfix(self) -> ASTNode:
        """Parse postfix expressions (function calls, array indexing)."""
        expr = self.parse_primary()
        
        while True:
            if self.match(TokenType.LPAREN):
                # Function call
                lparen = self.advance()
                arguments = self.parse_arguments()
                self.expect(TokenType.RPAREN)
                expr = FunctionCall(expr, arguments, lparen.line, lparen.column)
            elif self.match(TokenType.LBRACKET):
                # Array indexing
                lbracket = self.advance()
                index = self.parse_expression()
                self.expect(TokenType.RBRACKET)
                expr = ArrayIndex(expr, index, lbracket.line, lbracket.column)
            elif self.match(TokenType.DOT):
                # Member access
                dot = self.advance()
                member_token = self.expect(TokenType.IDENTIFIER)
                member_name = member_token.value
                
                # Check if it's a method call or just member access
                if self.match(TokenType.LPAREN):
                    self.advance()
                    arguments = self.parse_arguments()
                    self.expect(TokenType.RPAREN)
                    expr = MethodCall(expr, member_name, arguments, dot.line, dot.column)
                else:
                    expr = MemberAccess(expr, member_name, dot.line, dot.column)
            else:
                break
        
        return expr
    
    def parse_arguments(self) -> List[ASTNode]:
        """Parse function call arguments."""
        arguments = []
        
        if not self.match(TokenType.RPAREN):
            while True:
                arguments.append(self.parse_expression())
                if not self.match(TokenType.COMMA):
                    break
                self.advance()
        
        return arguments
    
    def parse_primary(self) -> ASTNode:
        """Parse primary expression."""
        token = self.current_token()
        
        # Literals
        if self.match(TokenType.INT_LITERAL):
            self.advance()
            return IntLiteral(token.value, token.line, token.column)
        
        if self.match(TokenType.FLOAT_LITERAL):
            self.advance()
            return FloatLiteral(token.value, token.line, token.column)
        
        if self.match(TokenType.STRING_LITERAL):
            token = self.advance()
            return StringLiteral(token.value, token.line, token.column)
        
        if self.match(TokenType.CHAR_LITERAL):
            token = self.advance()
            return CharLiteral(token.value, token.line, token.column)
        
        if self.match(TokenType.TRUE):
            self.advance()
            return BoolLiteral(True, token.line, token.column)
        
        if self.match(TokenType.FALSE):
            self.advance()
            return BoolLiteral(False, token.line, token.column)
        
        if self.match(TokenType.NULL):
            self.advance()
            return NullLiteral(token.line, token.column)
        
        if self.match(TokenType.IDENTIFIER):
            token = self.advance()
            # Check if this is a struct literal: Name { field: value, ... }
            if self.match(TokenType.LBRACE) and token.value in self.struct_names:
                self.advance()
                fields = {}
                while not self.match(TokenType.RBRACE):
                    field_name_token = self.expect(TokenType.IDENTIFIER)
                    self.expect(TokenType.COLON)
                    field_value = self.parse_expression()
                    fields[field_name_token.value] = field_value
                    
                    if self.match(TokenType.COMMA):
                        self.advance()
                    else:
                        break
                self.expect(TokenType.RBRACE)
                return StructLiteral(token.value, fields, token.line, token.column)
            
            return Identifier(token.value, token.line, token.column)
        
        # Array literal
        if self.match(TokenType.LBRACKET):
            lbracket = self.advance()
            elements = []
            if not self.match(TokenType.RBRACKET):
                while True:
                    elements.append(self.parse_expression())
                    if not self.match(TokenType.COMMA):
                        break
                    self.advance()
            self.expect(TokenType.RBRACKET)
            return ArrayLiteral(elements, lbracket.line, lbracket.column)
        
        # Parenthesized expression
        if self.match(TokenType.LPAREN):
            self.advance()
            expr = self.parse_expression()
            self.expect(TokenType.RPAREN)
            return expr
        
        raise ParserError(f"Unexpected token: {token.type.name}", token.line, token.column)
