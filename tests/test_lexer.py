import unittest
from lexer import Lexer, TokenType

class TestLexer(unittest.TestCase):
    def test_literals(self):
        source = '123 45.67 "hello" true false'
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        
        self.assertEqual(tokens[0].type, TokenType.INT_LITERAL)
        self.assertEqual(tokens[0].value, 123)
        
        self.assertEqual(tokens[1].type, TokenType.FLOAT_LITERAL)
        self.assertEqual(tokens[1].value, 45.67)
        
        self.assertEqual(tokens[2].type, TokenType.STRING_LITERAL)
        self.assertEqual(tokens[2].value, "hello")
        
        self.assertEqual(tokens[3].type, TokenType.TRUE)
        self.assertEqual(tokens[4].type, TokenType.FALSE)

    def test_identifiers_and_keywords(self):
        source = "let fn if else while for in return int float bool string"
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        
        expected_types = [
            TokenType.LET, TokenType.FN, TokenType.IF, TokenType.ELSE,
            TokenType.WHILE, TokenType.FOR, TokenType.IN, TokenType.RETURN,
            TokenType.INT_TYPE, TokenType.FLOAT_TYPE, TokenType.BOOL_TYPE, TokenType.STRING_TYPE
        ]
        
        for i, expected_type in enumerate(expected_types):
            self.assertEqual(tokens[i].type, expected_type)

    def test_operators(self):
        source = "+ - * / % == != < <= > >= and or not = -> . ( ) [ ] { } , : ;"
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        
        expected_types = [
            TokenType.PLUS, TokenType.MINUS, TokenType.STAR, TokenType.SLASH, TokenType.PERCENT,
            TokenType.EQ, TokenType.NE, TokenType.LT, TokenType.LE, TokenType.GT, TokenType.GE,
            TokenType.AND, TokenType.OR, TokenType.NOT, TokenType.ASSIGN, TokenType.ARROW, TokenType.DOT,
            TokenType.LPAREN, TokenType.RPAREN, TokenType.LBRACKET, TokenType.RBRACKET,
            TokenType.LBRACE, TokenType.RBRACE, TokenType.COMMA, TokenType.COLON, TokenType.SEMICOLON
        ]
        
        for i, expected_type in enumerate(expected_types):
            self.assertEqual(tokens[i].type, expected_type)

    def test_comments_and_whitespace(self):
        source = """
        // This is a comment
        let x = 10;  // Inline comment
        /* Multiline
           comment */
        let y = 20;
        """
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        
        # Should only contain tokens for 'let x = 10;' and 'let y = 20;' + EOF
        self.assertEqual(len(tokens), 11) # 5 + 5 + 1
        self.assertEqual(tokens[0].type, TokenType.LET)
        self.assertEqual(tokens[5].type, TokenType.LET)

if __name__ == '__main__':
    unittest.main()
