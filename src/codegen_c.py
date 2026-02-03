"""
C code generator for VibeLang.
Transpiles typed AST to C code.
"""

from typing import Dict, List, Set
from .ast_nodes import *
from .type_system import *
from .errors import CodeGenError


class CCodeGenerator:
    """Generates C code from typed AST."""
    
    def __init__(self):
        self.output: List[str] = []
        self.indent_level = 0
        self.temp_counter = 0
        self.functions: Set[str] = set()
        self.forward_decls: List[str] = []
        self.current_func_return_type: Optional[Type] = None
        self.required_tuples: Set[str] = set()
        self.tuple_definitions: Dict[str, List[str]] = {} # name -> [field_types]
    
    def generate(self, program: Program, other_programs: List[Program] = None) -> str:
        """Generate C code for entire program (and imported modules)."""
        all_programs = [program]
        if other_programs:
            all_programs.extend(other_programs)
            
        # Collect all statements from all programs
        all_statements = []
        for p in all_programs:
            all_statements.extend(p.statements)
            
        # Collect function names for forward declarations
        for statement in all_statements:
            if isinstance(statement, FunctionDeclaration):
                self.functions.add(statement.name)
            # Scan for tuple types
            self._scan_types(statement)
        
        # Generate header
        self._generate_header()
        
        # Generate forward declarations for runtime and user functions
        self.output.extend([
            "// Runtime function prototypes",
            "void* vibe_array_get(VArray* arr, size_t index);",
            "void vibe_array_push(VArray* arr, void* element);",
            "long long main_func(void);",
            "long long top_level_main(void);",
            "",
        ])
        
        self.output.append("")
        
        # Generate built-in functions
        self._generate_builtins()
        
        # Generate struct definitions
        # Deduplicate by name
        seen_structs = set()
        for statement in all_statements:
            if isinstance(statement, StructDefinition):
                if statement.name not in seen_structs:
                    self._generate_struct_definition(statement)
                    seen_structs.add(statement.name)
        
        # Generate tuple structs
        self._generate_tuple_structs()
        
        self.output.append("")

        for statement in all_statements:
            if isinstance(statement, FunctionDeclaration):
                self._generate_forward_decl(statement)
        
        self.output.append("")
        
        # Generate function definitions
        # Deduplicate by name
        seen_functions = set()
        for statement in all_statements:
            if isinstance(statement, FunctionDeclaration):
                if statement.name not in seen_functions:
                    self._generate_function(statement)
                    seen_functions.add(statement.name)
        
        # Generate top_level_main for top-level statements
        # Only from the MAIN program
        top_level_stmts = [s for s in program.statements if not isinstance(s, (FunctionDeclaration, StructDefinition, Import))]
        
        self.output.append("// Top-level program")
        self.output.append("long long top_level_main(void) {")
        self.indent_level += 1
        
        # Set current_func_return_type for top_level_main
        old_return_type = self.current_func_return_type
        self.current_func_return_type = IntType() # top_level_main returns long long
        
        for stmt in top_level_stmts:
            self._generate_statement(stmt)
            
        # Ensure it returns something
        self._emit("return 0LL;")
        self.indent_level -= 1
        self.output.append("}")
        self.output.append("")
        
        # Restore old return type
        self.current_func_return_type = old_return_type
        
        # Generate main entry point
        self._generate_main_entry()
        
        return '\n'.join(self.output)
    
    def _generate_header(self):
        """Generate C header includes and type definitions."""
        self.output.extend([
            "#include <stdio.h>",
            "#include <stdlib.h>",
            "#include <string.h>",
            "#include <stdbool.h>",
            "",
            "// Array type definition",
            "typedef struct {",
            "    void* data;",
            "    size_t length;",
            "    size_t capacity;",
            "    size_t element_size;",
            "} VArray;",
            "",
        ])
    
    def _generate_builtins(self):
        """Generate built-in function implementations."""
        self.output.extend([
            "// Built-in functions",
            "void vibe_print_str(const char* str) {",
            "    printf(\"%s\\n\", str);",
            "}",
            "",
            "void vibe_print_char(char val) {",
            "    printf(\"%c\\n\", val);",
            "}",
            "",
            "void vibe_print_int(long long val) {",
            "    printf(\"%lld\\n\", val);",
            "}",
            "",
            "void vibe_print_float(double val) {",
            "    printf(\"%g\\n\", val);",
            "}",
            "",
            "void vibe_print_bool(int val) {",
            "    printf(\"%s\\n\", val ? \"true\" : \"false\");",
            "}",
            "",
            "size_t vibe_len(VArray* arr) {",
            "    return arr->length;",
            "}",
            "",
            "VArray* vibe_array_new(size_t element_size, size_t initial_capacity) {",
            "    VArray* arr = (VArray*)malloc(sizeof(VArray));",
            "    arr->element_size = element_size;",
            "    arr->capacity = initial_capacity;",
            "    arr->length = 0;",
            "    arr->data = malloc(element_size * initial_capacity);",
            "    return arr;",
            "}",
            "",
            "void vibe_array_push(VArray* arr, void* element) {",
            "    if (arr->length >= arr->capacity) {",
            "        arr->capacity *= 2;",
            "        arr->data = realloc(arr->data, arr->element_size * arr->capacity);",
            "    }",
            "    memcpy((char*)arr->data + (arr->length * arr->element_size), element, arr->element_size);",
            "    arr->length++;",
            "}",
            "",
            "VArray* vibe_array_with_elements(size_t element_size, size_t count, void* elements) {",
            "    VArray* arr = vibe_array_new(element_size, count > 0 ? count : 1);",
            "    if (count > 0) {",
            "        memcpy(arr->data, elements, element_size * count);",
            "        arr->length = count;",
            "    }",
            "    return arr;",
            "}",
            "",
            "void* vibe_array_get_after_push(VArray* arr, void* element) {",
            "    vibe_array_push(arr, element);",
            "    return vibe_array_get(arr, arr->length - 1);",
            "}",
            "",
            "void* vibe_array_pop_ptr(VArray* arr) {",
            "    if (arr->length == 0) {",
            "        fprintf(stderr, \"pop() from empty array\\n\");",
            "        exit(1);",
            "    }",
            "    arr->length--;",
            "    return (char*)arr->data + (arr->length * arr->element_size);",
            "}",
            "",
            "void* vibe_array_get(VArray* arr, size_t index) {",
            "    if (index >= arr->length) {",
            "        fprintf(stderr, \"Array index out of bounds: %zu\\n\", index);",
            "        exit(1);",
            "    }",
            "    return (char*)arr->data + (index * arr->element_size);",
            "}",
            "",
            "void vibe_array_set(VArray* arr, size_t index, void* element) {",
            "    if (index >= arr->length) {",
            "        fprintf(stderr, \"Array index out of bounds: %zu\\n\", index);",
            "        exit(1);",
            "    }",
            "    memcpy((char*)arr->data + (index * arr->element_size), element, arr->element_size);",
            "}",
            "",
            "void vibe_array_pop(VArray* arr, void* out_element) {",
            "    if (arr->length == 0) {",
            "        fprintf(stderr, \"pop() from empty array\\n\");",
            "        exit(1);",
            "    }",
            "    arr->length--;",
            "    memcpy(out_element, (char*)arr->data + (arr->length * arr->element_size), arr->element_size);",
            "}",
            "",
            "const char* vibe_string_concat(const char* s1, const char* s2) {",
            "    size_t len1 = strlen(s1);",
            "    size_t len2 = strlen(s2);",
            "    char* res = malloc(len1 + len2 + 1);",
            "    strcpy(res, s1);",
            "    strcat(res, s2);",
            "    return res;",
            "}",
            "",
            "const char* vibe_read_str() {",
            "    char buffer[1024];",
            "    if (fgets(buffer, sizeof(buffer), stdin)) {",
            "        size_t len = strlen(buffer);",
            "        if (len > 0 && buffer[len-1] == '\\n') buffer[len-1] = '\\0';",
            "        char* res = malloc(strlen(buffer) + 1);",
            "        strcpy(res, buffer);",
            "        return res;",
            "    }",
            "    return \"\";",
            "}",
            "",
            "long long vibe_read_int() {",
            "    long long val;",
            "    if (scanf(\"%lld\", &val) == 1) {",
            "        int c;",
            "        while ((c = getchar()) != '\\n' && c != EOF);",
            "        return val;",
            "    }",
            "    return 0LL;",
            "}",
            "",
            "long long vibe_ord(char c) {",
            "    return (long long)c;",
            "}",
            "",
            "char vibe_chr(long long code) {",
            "    return (char)code;",
            "}",
            "",
            "const char* vibe_str(char c) {",
            "    char* s = (char*)malloc(2);",
            "    s[0] = c;",
            "    s[1] = '\\0';",
            "    return s;",
            "}",
            "",
        ])
    
    def _generate_forward_decl(self, node: FunctionDeclaration):
        """Generate forward declaration for function."""
        return_type = self._c_type(node.return_type)
        func_name = "main_func" if node.name == "main" else node.name
        
        params = []
        for param in node.parameters:
            param_type = self._c_type(param.type_annotation)
            params.append(f"{param_type} {param.name}")
        
        params_str = ", ".join(params) if params else "void"
        self.output.append(f"{return_type} {func_name}({params_str});")
    
    def _generate_function(self, node: FunctionDeclaration):
        """Generate function definition."""
        return_type = self._c_type(node.return_type)
        func_name = "main_func" if node.name == "main" else node.name
        
        params = []
        for param in node.parameters:
            param_type = self._c_type(param.type_annotation)
            params.append(f"{param_type} {param.name}")
        
        params_str = ", ".join(params) if params else "void"
        
        self.output.append(f"// Function: {node.name}")
        self.output.append(f"{return_type} {func_name}({params_str}) {{")
        self.indent_level += 1
        
        old_return_type = self.current_func_return_type
        self.current_func_return_type = type_from_annotation(node.return_type)
        
        # Generate function body
        for statement in node.body:
            self._generate_statement(statement)
            
        self.current_func_return_type = old_return_type
        
        self.indent_level -= 1
        self.output.append("}")
        self.output.append("")
    
    def _generate_main_entry(self):
        """Generate main() entry point."""
        # We try to call main_func() if it was defined, but we need to check if it's in our functions set
        main_ret = "(int)main_func()" if "main" in self.functions else "0"
        self.output.extend([
            "// Entry point",
            "int main(int argc, char** argv) {",
            "    (void)argc;",
            "    (void)argv;",
            "    top_level_main();",
            f"    return {main_ret};",
            "}",
        ])
    
    def _generate_statement(self, node: ASTNode):
        """Generate code for a statement."""
        if isinstance(node, VariableDeclaration):
            self._generate_variable_decl(node)
        elif isinstance(node, Assignment):
            self._generate_assignment(node)
        elif isinstance(node, IfStatement):
            self._generate_if_statement(node)
        elif isinstance(node, WhileStatement):
            self._generate_while_statement(node)
        elif isinstance(node, StructDefinition):
            pass
        elif isinstance(node, Import):
            pass
        elif isinstance(node, ForStatement):
            self._generate_for_statement(node)
        elif isinstance(node, ReturnStatement):
            self._generate_return_statement(node)
        elif isinstance(node, ExpressionStatement):
            # Special handling for print calls which are statements
            if isinstance(node.expression, FunctionCall) and isinstance(node.expression.function, Identifier) and node.expression.function.name == 'print':
                self._generate_expression(node.expression)
                return

            # Special handling for array push which is often a statement
            if isinstance(node.expression, MethodCall) and node.expression.method_name == 'push':
                obj_code = self._generate_expression(node.expression.object)
                val_code = self._generate_expression(node.expression.arguments[0])
                elem_type = self._infer_c_type(node.expression.object.type.element_type)
                self._emit(f"{{ {elem_type} _tmp = {val_code}; vibe_array_push({obj_code}, &_tmp); }}")
                return

            # Check if ExpressionStatement is a Destructuring Assignment
            if isinstance(node.expression, Assignment) and len(node.expression.targets) > 1:
                self._generate_destructuring_assignment(node.expression)
                return

            expr_code = self._generate_expression(node.expression)
            self._emit(f"{expr_code};")
        else:
            raise CodeGenError(f"Unknown statement type: {type(node).__name__}", node.line, node.column)
    
    def _generate_variable_decl(self, node: VariableDeclaration):
        """Generate variable declaration."""
        if len(node.names) > 1:
             # Destructuring
             struct_type = self._infer_c_type(node.type)
             
             if not node.initializer:
                 raise CodeGenError("Destructuring declaration requires initializer", node.line, node.column)
                 
             init_code = self._generate_expression(node.initializer)
             
             tmp_var = f"_tuple_tmp_{self.temp_counter}"
             self.temp_counter += 1
             
             self._emit(f"{struct_type} {tmp_var} = {init_code};")
             
             for i, name in enumerate(node.names):
                  # node.type is MultiType
                  var_c_type = self._infer_c_type(node.type.types[i])
                  self._emit(f"{var_c_type} {name} = {tmp_var}.v{i};")
        else:
            # Single variable
            var_type = self._c_type(node.type_annotation) if node.type_annotation else self._infer_c_type(node.type)
            
            if node.initializer:
                init_code = self._generate_expression(node.initializer)
                self._emit(f"{var_type} {node.name} = {init_code};")
            else:
                self._emit(f"{var_type} {node.name};")
    
    def _generate_assignment(self, node: Assignment):
        """Generate assignment statement."""
        # Note: Destructuring assignment handles len(targets) > 1 specially in _generate_destructuring_assignment.
        # This method handles single assignments or cases passed down?
        # Actually _generate_statement dispatch calls _generate_destructuring_assignment if targets > 1.
        # But if we call this directly for expression context (unsupported for destructuring), checks remain.
        
        if isinstance(node.target, Identifier):
            value_code = self._generate_expression(node.value)
            self._emit(f"{node.target.name} = {value_code};")
        elif isinstance(node.target, ArrayIndex):
            array_code = self._generate_expression(node.target.array)
            index_code = self._generate_expression(node.target.index)
            value_code = self._generate_expression(node.value)
            
            # Get element type
            element_type = self._infer_c_type(node.target.type)
            self._emit(f"{{")
            self.indent_level += 1
            self._emit(f"{element_type} _tmp_val = {value_code};")
            self._emit(f"vibe_array_set({array_code}, {index_code}, &_tmp_val);")
            self.indent_level -= 1
            self._emit(f"}}")
        elif isinstance(node.target, MemberAccess):
            obj_code = self._generate_expression(node.target.object)
            value_code = self._generate_expression(node.value)
            self._emit(f"{obj_code}->{node.target.member_name} = {value_code};")
        else:
            raise CodeGenError(f"Invalid assignment target: {type(node.target).__name__}", node.line, node.column)

    def _generate_destructuring_assignment(self, node: Assignment):
        """Generate destructuring assignment."""
        struct_type = self._infer_c_type(node.type)
        
        value_code = self._generate_expression(node.value)
        
        tmp_var = f"_tuple_tmp_{self.temp_counter}"
        self.temp_counter += 1
        
        self._emit(f"{{ {struct_type} {tmp_var} = {value_code};")
        self.indent_level += 1
        
        for i, target in enumerate(node.targets):
             if isinstance(target, Identifier):
                 self._emit(f"{target.name} = {tmp_var}.v{i};")
             else:
                 raise CodeGenError("Destructuring only supported for simple variables", node.line, node.column)
        
        self.indent_level -= 1
        self._emit("}")
    
    def _generate_if_statement(self, node: IfStatement):
        """Generate if statement."""
        condition_code = self._generate_expression(node.condition)
        self._emit(f"if ({condition_code}) {{")
        self.indent_level += 1
        
        for statement in node.then_block:
            self._generate_statement(statement)
        
        self.indent_level -= 1
        
        if node.else_block:
            self._emit("} else {")
            self.indent_level += 1
            
            for statement in node.else_block:
                self._generate_statement(statement)
            
            self.indent_level -= 1
        
    
        self._emit("}")
    
    def _generate_while_statement(self, node: WhileStatement):
        """Generate while loop."""
        condition_code = self._generate_expression(node.condition)
        self._emit(f"while ({condition_code}) {{")
        self.indent_level += 1
        
        for statement in node.body:
            self._generate_statement(statement)
        
        self.indent_level -= 1
        self._emit("}")
    
    def _generate_for_statement(self, node: ForStatement):
        """Generate for loop."""
        iterable_code = self._generate_expression(node.iterable)
        
        # Generate for loop using array
        self._emit("{")
        self.indent_level += 1
        
        self._emit(f"VArray* _iter_arr = {iterable_code};")
        self._emit(f"for (size_t _i = 0; _i < _iter_arr->length; _i++) {{")
        self.indent_level += 1
        
        # Get element type
        element_type = self._infer_c_type(node.iterable.type.element_type)
        self._emit(f"{element_type} {node.variable} = *({element_type}*)vibe_array_get(_iter_arr, _i);")
        
        for statement in node.body:
            self._generate_statement(statement)
        
        self.indent_level -= 1
        self._emit("}")
        self.indent_level -= 1
        self._emit("}")
    
    def _generate_return_statement(self, node: ReturnStatement):
        """Generate return statement."""
        if node.values:
            if len(node.values) == 1:
                value_code = self._generate_expression(node.values[0])
                self._emit(f"return {value_code};")
            else:
                # Multiple return values (tuple)
                struct_type = self._infer_c_type(self.current_func_return_type)
                values = [self._generate_expression(v) for v in node.values]
                values_str = ", ".join(values)
                self._emit(f"return ({struct_type}){{ {values_str} }};")
        else:
            if isinstance(self.current_func_return_type, VoidType):
                self._emit("return;")
            else:
                self._emit("return 0;")
    
    def _generate_expression(self, node: ASTNode) -> str:
        """Generate code for expression and return the expression string."""
        if isinstance(node, IntLiteral):
            return f"{node.value}LL"
        
        elif isinstance(node, FloatLiteral):
            return str(node.value)
        
        elif isinstance(node, StringLiteral):
            # Escape string
            escaped = node.value.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
            return f'"{escaped}"'
        
        elif isinstance(node, CharLiteral):
            # Escape character if necessary
            val = node.value
            if val == '\n': val = '\\n'
            elif val == '\t': val = '\\t'
            elif val == '\r': val = '\\r'
            elif val == '\'': val = '\\\''
            elif val == '\\': val = '\\\\'
            return f"'{val}'"
        
        elif isinstance(node, BoolLiteral):
            return "1" if node.value else "0"
        
        elif isinstance(node, NullLiteral):
            return "NULL"
        
        elif isinstance(node, ArrayLiteral):
            return self._generate_array_literal(node)
        
        elif isinstance(node, Identifier):
            return node.name
        
        elif isinstance(node, BinaryOp):
            return self._generate_binary_op(node)
        
        elif isinstance(node, UnaryOp):
            return self._generate_unary_op(node)
        
        elif isinstance(node, FunctionCall):
            return self._generate_function_call(node)
        
        elif isinstance(node, MethodCall):
            return self._generate_method_call(node)
        
        elif isinstance(node, ArrayIndex):
            array_code = self._generate_expression(node.array)
            index_code = self._generate_expression(node.index)
            if isinstance(node.array.type, StringType):
                return f"{array_code}[{index_code}]"
            element_type = self._infer_c_type(node.type)
            return f"(*({element_type}*)vibe_array_get({array_code}, {index_code}))"
        
        elif isinstance(node, StructLiteral):
            return self._generate_struct_literal(node)
        
        elif isinstance(node, MemberAccess):
            obj_code = self._generate_expression(node.object)
            return f"{obj_code}->{node.member_name}"
        
        elif isinstance(node, Assignment):
            # Handle assignment as expression (returns assigned value)
            if isinstance(node.target, Identifier):
                value_code = self._generate_expression(node.value)
                return f"({node.target.name} = {value_code})"
            elif isinstance(node.target, MemberAccess):
                obj_code = self._generate_expression(node.target.object)
                value_code = self._generate_expression(node.value)
                return f"({obj_code}->{node.target.member_name} = {value_code})"
            elif isinstance(node.target, ArrayIndex):
                # This is complex, just generate it as a statement would be better
                # For now, we'll raise an error
                raise CodeGenError("Array assignment not supported in expression context", node.line, node.column)
            else:
                raise CodeGenError(f"Invalid assignment target in expression: {type(node.target).__name__}", node.line, node.column)
        
        else:
            raise CodeGenError(f"Unknown expression type: {type(node).__name__}", node.line, node.column)
    
    def _generate_array_literal(self, node: ArrayLiteral) -> str:
        """Generate array literal."""
        # Determine element type and size
        element_type = node.type.element_type
        c_element_type = self._infer_c_type(element_type)
        element_size = self._c_sizeof(c_element_type)
        
        if not node.elements:
            return f"vibe_array_new({element_size}, 0)"
        
        # Use C99 compound literal for the elements array
        # Example: vibe_array_with_elements(sizeof(int), 3, (int[]){1, 2, 3})
        elements_code = [self._generate_expression(elem) for elem in node.elements]
        elements_str = ", ".join(elements_code)
        
        return f"vibe_array_with_elements({element_size}, {len(node.elements)}, ({c_element_type}[]){{ {elements_str} }})"
    
    def _generate_binary_op(self, node: BinaryOp) -> str:
        """Generate binary operation."""
        left_code = self._generate_expression(node.left)
        right_code = self._generate_expression(node.right)
        
        op_map = {
            '+': '+',
            '-': '-',
            '*': '*',
            '/': '/',
            '%': '%',
            '==': '==',
            '!=': '!=',
            '<': '<',
            '<=': '<=',
            '>': '>',
            '>=': '>=',
            'and': '&&',
            'or': '||',
        }
        
        c_op = op_map.get(node.operator)
        if c_op:
            if node.operator == '+' and isinstance(node.left.type, StringType) and isinstance(node.right.type, StringType):
                return f"vibe_string_concat({left_code}, {right_code})"
            return f"({left_code} {c_op} {right_code})"
        else:
            raise CodeGenError(f"Unknown binary operator: {node.operator}", node.line, node.column)
    
    def _generate_unary_op(self, node: UnaryOp) -> str:
        """Generate unary operation."""
        operand_code = self._generate_expression(node.operand)
        
        if node.operator == '-':
            return f"(-{operand_code})"
        elif node.operator == 'not':
            return f"(!{operand_code})"
        else:
            raise CodeGenError(f"Unknown unary operator: {node.operator}", node.line, node.column)
    
    def _generate_function_call(self, node: FunctionCall) -> str:
        """Generate function call."""
        if isinstance(node.function, Identifier):
            func_name = node.function.name
            
            # Handle built-in functions
            if func_name == 'print':
                # Generate argument
                if node.arguments:
                    arg_type = node.arguments[0].type
                    arg_code = self._generate_expression(node.arguments[0])
                    if isinstance(arg_type, IntType):
                        self._emit(f"vibe_print_int({arg_code});")
                    elif isinstance(arg_type, FloatType):
                        self._emit(f"vibe_print_float({arg_code});")
                    elif isinstance(arg_type, BoolType):
                        self._emit(f"vibe_print_bool({arg_code});")
                    elif isinstance(arg_type, CharType):
                        self._emit(f"vibe_print_char({arg_code});")
                    elif isinstance(arg_type, StringType):
                        self._emit(f"vibe_print_str({arg_code});")
                    else:
                        self._emit(f"vibe_print_str(\"[object]\");")
                else:
                    self._emit("vibe_print_str(\"\");")
                return "" # Print is a statement, returns nothing in C context
            
            elif func_name == 'len':
                if node.arguments:
                    arg = node.arguments[0]
                    arg_code = self._generate_expression(arg)
                    if isinstance(arg.type, StringType):
                        return f"strlen({arg_code})"
                    return f"vibe_len({arg_code})"
                return "0"
            
            elif func_name == 'ord':
                arg_code = self._generate_expression(node.arguments[0])
                return f"vibe_ord({arg_code})"
            
            elif func_name == 'chr':
                arg_code = self._generate_expression(node.arguments[0])
                return f"vibe_chr({arg_code})"
            
            elif func_name == 'str':
                arg_code = self._generate_expression(node.arguments[0])
                return f"vibe_str({arg_code})"
            
            elif func_name == 'read_str':
                return "vibe_read_str()"
            
            elif func_name == 'read_int':
                return "vibe_read_int()"
            
            # User-defined function
            actual_name = "main_func" if func_name == "main" else func_name
            args = [self._generate_expression(arg) for arg in node.arguments]
            args_str = ", ".join(args) if args else ""
            return f"{actual_name}({args_str})"
        
        else:
            raise CodeGenError("Function calls must use identifiers", node.line, node.column)

    def _generate_method_call(self, node: MethodCall) -> str:
        """Generate code for method call."""
        obj_code = self._generate_expression(node.object)
        obj_type = node.object.type
        
        if isinstance(obj_type, ArrayType):
            if node.method_name == 'push':
                val_code = self._generate_expression(node.arguments[0])
                elem_type = self._infer_c_type(obj_type.element_type)
                # Use comma operator for expression context: (tmp=val, push(obj, &tmp), obj)
                # This is still a bit tricky for MSVC if it's not a statement.
                # Most of the time it's a statement, which we handle in _generate_statement.
                # If it's an expression, we'll use a hacky but portable approach.
                return f"(*({elem_type}*)vibe_array_get_after_push({obj_code}, &({elem_type}){{ {val_code} }}))"
            
            elif node.method_name == 'pop':
                elem_type = self._infer_c_type(obj_type.element_type)
                # We need a way to return the popped value.
                return f"(*({elem_type}*)vibe_array_pop_ptr({obj_code}))"
            
            else:
                raise CodeGenError(f"Unknown method '{node.method_name}' on array", node.line, node.column)
        
        raise CodeGenError(f"Methods not supported for type {obj_type}", node.line, node.column)
    
    def _c_type(self, type_annotation: TypeAnnotation) -> str:
        """Convert type annotation to C type string."""
        if hasattr(type_annotation, 'type') and type_annotation.type:
            return self._infer_c_type(type_annotation.type)
        
        # Fallback for untyped or simple cases
        if type_annotation.type_name == 'int':
            return 'long long'
        elif type_annotation.type_name == 'float':
            return 'double'
        elif type_annotation.type_name == 'bool':
            return 'int'
        elif type_annotation.type_name == 'string':
            return 'const char*'
        elif type_annotation.type_name == 'char':
            return 'char'
        elif type_annotation.type_name == 'array':
            return 'VArray*'
        elif type_annotation.type_name == 'tuple':
             # Resolve element types
             field_c_types = []
             if type_annotation.types:
                 for t in type_annotation.types:
                     field_c_types.append(self._c_type(t))
             return self._get_tuple_struct_name(field_c_types)
        elif type_annotation.type_name:
            # Assume it's a struct name
            return f'{type_annotation.type_name}*'
        else:
            return 'void'
    
    def _infer_c_type(self, vibe_type: Type) -> str:
        """Convert VibeLang Type to C type string."""
        if isinstance(vibe_type, IntType):
            return 'long long'
        elif isinstance(vibe_type, FloatType):
            return 'double'
        elif isinstance(vibe_type, BoolType):
            return 'int'
        elif isinstance(vibe_type, StringType):
            return 'const char*'
        elif isinstance(vibe_type, CharType):
            return 'char'
        elif isinstance(vibe_type, ArrayType):
            return 'VArray*'
        elif isinstance(vibe_type, StructType):
            return f'{vibe_type.name}*'
        elif isinstance(vibe_type, MultiType):
            field_types = [self._infer_c_type(t) for t in vibe_type.types]
            return self._get_tuple_struct_name(field_types)
        else:
            return 'void'
    
    def _generate_struct_definition(self, node: StructDefinition):
        """Generate C struct definition."""
        self.output.append(f"typedef struct {node.name} {node.name};")
        self.output.append(f"struct {node.name} {{")
        self.indent_level += 1
        for field in node.fields:
            # Use the type we collected during struct check
            field_type_obj = node.type.fields[field.name]
            field_type = self._infer_c_type(field_type_obj)
            self._emit(f"{field_type} {field.name};")
        self.indent_level -= 1
        self.output.append("};")
        self.output.append("")
        
        # Generate heap-allocated constructor
        self.output.append(f"// Header for {node.name} constructor")
        param_list = []
        for field in node.fields:
            field_type = self._infer_c_type(node.type.fields[field.name])
            param_list.append(f"{field_type} {field.name}")
        params_str = ", ".join(param_list)
        
        self.output.append(f"{node.name}* vibe_new_{node.name}({params_str}) {{")
        self.indent_level += 1
        self._emit(f"{node.name}* _res = ({node.name}*)malloc(sizeof({node.name}));")
        for field in node.fields:
            self._emit(f"_res->{field.name} = {field.name};")
        self._emit("return _res;")
        self.indent_level -= 1
        self.output.append("}")
        self.output.append("")

    def _generate_struct_literal(self, node: StructLiteral) -> str:
        """Generate C struct literal (heap allocated)."""
        field_values = []
        for name in node.type.fields: # Use field list from type to maintain order
            value = node.fields[name]
            field_values.append(self._generate_expression(value))
        
        values_str = ", ".join(field_values)
        return f"vibe_new_{node.name}({values_str})"
    
    def _c_sizeof(self, c_type: str) -> str:
        """Get sizeof expression for C type."""
        return f"sizeof({c_type})"
    
    def _emit(self, code: str):
        """Emit a line of code with proper indentation."""
        indent = "    " * self.indent_level
        self.output.append(indent + code)

    def _get_tuple_struct_name(self, field_types: List[str]) -> str:
        """Get or create struct name for tuple type."""
        # Create a canonical name based on types
        parts = []
        for t in field_types:
            clean_t = t.replace(' ', '').replace('*', 'Ptr')
            parts.append(clean_t)
        
        name = f"Tuple_{'_'.join(parts)}"
        
        if name not in self.required_tuples:
            self.required_tuples.add(name)
            self.tuple_definitions[name] = field_types
            
        return name

    def _generate_tuple_structs(self):
        """Generate C structs for collected tuple types."""
        if not self.required_tuples:
            return
            
        self.output.append("// Tuple structs")
        for name in sorted(self.required_tuples):
            field_types = self.tuple_definitions[name]
            self.output.append(f"typedef struct {{")
            self.indent_level += 1
            for i, f_type in enumerate(field_types):
                self._emit(f"{f_type} v{i};")
            self.indent_level -= 1
            self.output.append(f"}} {name};")
            self.output.append("")

    def _scan_types(self, node: ASTNode):
        """Recursively scan for tuple types."""
        if isinstance(node, FunctionDeclaration):
            if node.return_type:
                self._c_type(node.return_type) # Side effect: registers tuple
            for param in node.parameters:
                if param.type_annotation:
                    self._c_type(param.type_annotation)
            for stmt in node.body:
                self._scan_types(stmt)
                
        elif isinstance(node, VariableDeclaration):
            if node.type_annotation:
                self._c_type(node.type_annotation)
        
        elif isinstance(node, StructDefinition):
            for field in node.fields:
                self._c_type(field.type)
                
        # We don't need to scan expressions deeply unless they contain casts or definitions,
        # but type annotations usually appear in declarations.
