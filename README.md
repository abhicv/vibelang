# VibeLang

> [!NOTE]
> **Disclaimer**: This project was fully generated using **Antigravity**.


A statically-typed programming language that compiles to custom VM bytecode.

## Features

- **Static Type System**: Strong typing with `int`, `float`, `bool`, `string`, and arrays
- **Type Inference**: Local variable types inferred from initializers
- **Functions**: First-class functions with type signatures
- **Control Flow**: `if/else`, `while`, `for` loops
- **Arrays**: Dynamic arrays with type-safe elements
- **VM Bytecode**: Compiles to efficient stack-based bytecode
- **Built-in Functions**: `print()`, `len()`

## Installation

### Prerequisites
- **Python 3.8+**: Required for the compiler and VM.
- **C Compiler (Optional)**: Required for the C backend (native compilation).
  - **Windows**: [Visual Studio Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/) (MSVC) is recommended.
  - **Linux/macOS**: `gcc` or `clang`.

### Setup
1. Clone the repository:
   ```bash
   git clone https://github.com/abhicv/vibelang.git
   cd vibelang
   ```

## Usage

### Run a VibeLang program

```bash
python main.py examples/hello.vibe
```

### Compile to bytecode

```bash
python main.py -c output.vbc examples/factorial.vibe
```

### Generate C code

```bash
python main.py --emit-c output.c examples/factorial.vibe
gcc -o factorial output.c
./factorial
```

### Interactive REPL

```bash
python main.py -r
```

### Tests & Automation

VibeLang includes a test runner that automatically manages build artifacts.

```bash
# Run all integration tests
python test_runner.py
```
> [!NOTE]
> Testing artifacts are automatically placed in a `build/` directory and cleaned up after execution.

## Language Syntax

### Variables

```vibe
// Type inference
let x = 42;
let message = "Hello";

// Explicit types
let y: int = 100;
let pi: float = 3.14;
let flag: bool = true;
```

### Functions

```vibe
fn add(a: int, b: int) -> int {
    return a + b;
}

fn greet(name: string) -> int {
    print("Hello, ");
    print(name);
    return 0;
}
```

### Control Flow

```vibe
// If-else
if x > 0 {
    print("Positive");
} else {
    print("Non-positive");
}

// While loop
let i = 0;
while i < 10 {
    print("Iteration");
    i = i + 1;
}

// For loop
let numbers = [1, 2, 3, 4, 5];
for num in numbers {
    print("Number");
}
```

### Arrays

```vibe
// Array literals
let numbers = [1, 2, 3, 4, 5];
let names = ["Alice", "Bob", "Charlie"];

// Array indexing
let first = numbers[0];
numbers[1] = 42;

// Array length
let size = len(numbers);
```

### Types

- `int` - Integer numbers
- `float` - Floating-point numbers
- `bool` - Boolean values (`true`, `false`)
- `string` - String literals
- `[type]` - Arrays (e.g., `[int]`, `[string]`)

### Operators

**Arithmetic**: `+`, `-`, `*`, `/`, `%`

**Comparison**: `==`, `!=`, `<`, `<=`, `>`, `>=`

**Logical**: `and`, `or`, `not`

**Assignment**: `=`

### Comments

```vibe
// Single-line comment

/*
   Multi-line
   comment
*/
```

## Examples

### Hello World

```vibe
fn main() -> int {
    print("Hello, VibeLang!");
    return 0;
}

main();
```

### Factorial (Recursion)

```vibe
fn factorial(n: int) -> int {
    if n <= 1 {
        return 1;
    }
    return n * factorial(n - 1);
}

fn main() -> int {
    let result = factorial(5);
    print("120");
    return 0;
}

main();
```

### Fibonacci (Loops)

```vibe
fn fibonacci(n: int) -> int {
    if n <= 1 {
        return n;
    }
    
    let a = 0;
    let b = 1;
    let i = 2;
    
    while i <= n {
        let temp = a + b;
        a = b;
        b = temp;
        i = i + 1;
    }
    
    return b;
}
```

### Array Operations

```vibe
fn sum_array(arr: [int]) -> int {
    let total = 0;
    for element in arr {
        total = total + element;
    }
    return total;
}

fn main() -> int {
    let numbers = [1, 2, 3, 4, 5];
    let total = sum_array(numbers);
    return 0;
}
```

## Architecture

VibeLang uses a multi-stage compilation pipeline with two backends:

### VM Backend (Bytecode)
```
Source Code → Lexer → Tokens → Parser → AST → Type Checker → Typed AST → Code Generator → Bytecode → VM
```

### C Backend (Native Code)
```
Source Code → Lexer → Tokens → Parser → AST → Type Checker → Typed AST → C Code Generator → C Code → gcc/clang → Native Binary
```

### Components

- **Lexer** ([src/lexer.py](file:///c:/Development/ML/vibe-code/vibelang/src/lexer.py)): Tokenizes source code
- **Parser** ([src/parser.py](file:///c:/Development/ML/vibe-code/vibelang/src/parser.py)): Builds Abstract Syntax Tree
- **Type Checker** ([src/type_checker.py](file:///c:/Development/ML/vibe-code/vibelang/src/type_checker.py)): Validates types and semantics
- **Code Generator** ([src/codegen.py](file:///c:/Development/ML/vibe-code/vibelang/src/codegen.py)): Generates VM bytecode
- **C Code Generator** ([src/codegen_c.py](file:///c:/Development/ML/vibe-code/vibelang/src/codegen_c.py)): Generates C code
- **Virtual Machine** ([src/vm.py](file:///c:/Development/ML/vibe-code/vibelang/src/vm.py)): Executes bytecode
- **Compiler** ([src/compiler.py](file:///c:/Development/ML/vibe-code/vibelang/src/compiler.py)): Orchestrates the pipeline

### VM Instruction Set

Stack-based bytecode with instructions for:
- Stack operations: `LOAD_CONST`, `LOAD_VAR`, `STORE_VAR`, `POP`
- Arithmetic: `ADD`, `SUB`, `MUL`, `DIV`, `MOD`, `NEG`
- Comparison: `EQ`, `NE`, `LT`, `LE`, `GT`, `GE`
- Logical: `AND`, `OR`, `NOT`
- Control flow: `JUMP`, `JUMP_IF_FALSE`, `JUMP_IF_TRUE`
- Functions: `CALL`, `RETURN`
- Built-ins: `PRINT`, `LEN`
- Arrays: `BUILD_ARRAY`, `INDEX_LOAD`, `INDEX_STORE`

### C Code Generation

The C backend transpiles VibeLang to C99 code:
- Maps VibeLang types to C types (int→long long, arrays→structs)
- Generates runtime support for arrays
- Produces readable, debuggable C code
- Enables native compilation for better performance

## Error Handling

VibeLang provides detailed error messages with line and column information:

```
Error at line 5, column 12: Cannot assign float to variable of type int
  let x: int = 3.14;
               ^
```

## Project Structure

```
vibelang/
├── src/                # Core compiler & VM source files
│   ├── __init__.py
│   ├── ast_nodes.py
│   ├── compiler.py
│   ├── vm.py
│   └── ...
├── examples/           # VibeLang example programs
├── tests/              # Unit tests
├── main.py             # Main CLI entry point
├── test_runner.py      # Integration test runner
├── run_tests.py        # Unit test runner
├── vibe_compile.bat    # MSVC build helper script
└── README.md           # Documentation
```

## Future Enhancements

Potential improvements for VibeLang:

- **More types**: Structs, enums, tuples
- **Standard library**: Math, string manipulation, I/O
- **Optimizations**: Constant folding, dead code elimination
- **Better error recovery**: Continue parsing after errors
- **Debugger**: Step-through debugging support
- **Module system**: Import/export functionality
- **Generics**: Parametric polymorphism
- **Pattern matching**: Advanced control flow

## License

This is an educational project demonstrating compiler construction principles.

## Author

Created as a demonstration of a complete compiler implementation in Python.
