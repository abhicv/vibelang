"""
Error handling and reporting for VibeLang compiler.
"""

class VibeLangError(Exception):
    """Base exception for all VibeLang errors."""
    def __init__(self, message, line=None, column=None, source_line=None):
        self.message = message
        self.line = line
        self.column = column
        self.source_line = source_line
        super().__init__(self.format_error())
    
    def format_error(self):
        """Format error message with location information."""
        if self.line is not None and self.column is not None:
            error_msg = f"Error at line {self.line}, column {self.column}: {self.message}"
            if self.source_line:
                error_msg += f"\n  {self.source_line}"
                error_msg += f"\n  {' ' * (self.column - 1)}^"
            return error_msg
        return f"Error: {self.message}"


class LexerError(VibeLangError):
    """Raised during lexical analysis."""
    pass


class ParserError(VibeLangError):
    """Raised during parsing."""
    pass


class TypeError(VibeLangError):
    """Raised during type checking."""
    pass


class CodeGenError(VibeLangError):
    """Raised during code generation."""
    pass


class RuntimeError(VibeLangError):
    """Raised during VM execution."""
    pass
