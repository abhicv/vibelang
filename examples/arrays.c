#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>

// Array type definition
typedef struct {
    void* data;
    size_t length;
    size_t capacity;
    size_t element_size;
} VArray;

// Runtime function prototypes
void* vibe_array_get(VArray* arr, size_t index);
void vibe_array_push(VArray* arr, void* element);
long long main_func(void);
long long top_level_main(void);


// Built-in functions
void vibe_print_str(const char* str) {
    printf("%s\n", str);
}

void vibe_print_char(char val) {
    printf("%c\n", val);
}

void vibe_print_int(long long val) {
    printf("%lld\n", val);
}

void vibe_print_float(double val) {
    printf("%g\n", val);
}

void vibe_print_bool(int val) {
    printf("%s\n", val ? "true" : "false");
}

size_t vibe_len(VArray* arr) {
    return arr->length;
}

VArray* vibe_array_new(size_t element_size, size_t initial_capacity) {
    VArray* arr = (VArray*)malloc(sizeof(VArray));
    arr->element_size = element_size;
    arr->capacity = initial_capacity;
    arr->length = 0;
    arr->data = malloc(element_size * initial_capacity);
    return arr;
}

void vibe_array_push(VArray* arr, void* element) {
    if (arr->length >= arr->capacity) {
        arr->capacity *= 2;
        arr->data = realloc(arr->data, arr->element_size * arr->capacity);
    }
    memcpy((char*)arr->data + (arr->length * arr->element_size), element, arr->element_size);
    arr->length++;
}

VArray* vibe_array_with_elements(size_t element_size, size_t count, void* elements) {
    VArray* arr = vibe_array_new(element_size, count > 0 ? count : 1);
    if (count > 0) {
        memcpy(arr->data, elements, element_size * count);
        arr->length = count;
    }
    return arr;
}

void* vibe_array_get_after_push(VArray* arr, void* element) {
    vibe_array_push(arr, element);
    return vibe_array_get(arr, arr->length - 1);
}

void* vibe_array_pop_ptr(VArray* arr) {
    if (arr->length == 0) {
        fprintf(stderr, "pop() from empty array\n");
        exit(1);
    }
    arr->length--;
    return (char*)arr->data + (arr->length * arr->element_size);
}

void* vibe_array_get(VArray* arr, size_t index) {
    if (index >= arr->length) {
        fprintf(stderr, "Array index out of bounds: %zu\n", index);
        exit(1);
    }
    return (char*)arr->data + (index * arr->element_size);
}

void vibe_array_set(VArray* arr, size_t index, void* element) {
    if (index >= arr->length) {
        fprintf(stderr, "Array index out of bounds: %zu\n", index);
        exit(1);
    }
    memcpy((char*)arr->data + (index * arr->element_size), element, arr->element_size);
}

void vibe_array_pop(VArray* arr, void* out_element) {
    if (arr->length == 0) {
        fprintf(stderr, "pop() from empty array\n");
        exit(1);
    }
    arr->length--;
    memcpy(out_element, (char*)arr->data + (arr->length * arr->element_size), arr->element_size);
}

const char* vibe_string_concat(const char* s1, const char* s2) {
    size_t len1 = strlen(s1);
    size_t len2 = strlen(s2);
    char* res = malloc(len1 + len2 + 1);
    strcpy(res, s1);
    strcat(res, s2);
    return res;
}

const char* vibe_read_str() {
    char buffer[1024];
    if (fgets(buffer, sizeof(buffer), stdin)) {
        size_t len = strlen(buffer);
        if (len > 0 && buffer[len-1] == '\n') buffer[len-1] = '\0';
        char* res = malloc(strlen(buffer) + 1);
        strcpy(res, buffer);
        return res;
    }
    return "";
}

long long vibe_read_int() {
    long long val;
    if (scanf("%lld", &val) == 1) {
        int c;
        while ((c = getchar()) != '\n' && c != EOF);
        return val;
    }
    return 0LL;
}

long long vibe_ord(char c) {
    return (long long)c;
}

char vibe_chr(long long code) {
    return (char)code;
}

const char* vibe_str(char c) {
    char* s = (char*)malloc(2);
    s[0] = c;
    s[1] = '\0';
    return s;
}


long long sum_array(VArray* arr);
long long main_func(void);

// Function: sum_array
long long sum_array(VArray* arr) {
    long long total = 0LL;
    {
        VArray* _iter_arr = arr;
        for (size_t _i = 0; _i < _iter_arr->length; _i++) {
            long long element = *(long long*)vibe_array_get(_iter_arr, _i);
            (total = (total + element));
        }
    }
    return total;
}

// Function: main
long long main_func(void) {
    VArray* numbers = vibe_array_with_elements(sizeof(long long), 5, (long long[]){ 1LL, 2LL, 3LL, 4LL, 5LL });
    vibe_print_str("Array: [1, 2, 3, 4, 5]");
    long long total = sum_array(numbers);
    vibe_print_str("Sum: ");
    vibe_print_str("15");
    long long length = vibe_len(numbers);
    vibe_print_str("Length: ");
    vibe_print_str("5");
    long long first = (*(long long*)vibe_array_get(numbers, 0LL));
    vibe_print_str("First element: ");
    vibe_print_str("1");
    return 0LL;
}

// Top-level program
long long top_level_main(void) {
    return 0LL;
}

// Entry point
int main(int argc, char** argv) {
    (void)argc;
    (void)argv;
    top_level_main();
    return (int)main_func();
}