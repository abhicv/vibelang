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


long long main_func(void);
const char* to_upper(const char* s);
const char* to_lower(const char* s);
const char* substring(const char* s, long long start, long long end);
int contains(const char* s, const char* sub);
long long index_of(const char* s, const char* sub);
int starts_with(const char* s, const char* prefix);
int ends_with(const char* s, const char* suffix);

// Function: main
long long main_func(void) {
    const char* s = "Hello, VibeLang!";
    vibe_print_str(vibe_string_concat("Original: ", s));
    vibe_print_str(vibe_string_concat("Upper: ", to_upper(s)));
    vibe_print_str(vibe_string_concat("Lower: ", to_lower(s)));
    vibe_print_str(vibe_string_concat("Substring (7, 15): ", substring(s, 7LL, 15LL)));
    if (contains(s, "Vibe")) {
        vibe_print_str("Contains 'Vibe': true");
    } else {
        vibe_print_str("Contains 'Vibe': false");
    }
    if (starts_with(s, "Hello")) {
        vibe_print_str("Starts with 'Hello': true");
    } else {
        vibe_print_str("Starts with 'Hello': false");
    }
    if (ends_with(s, "!")) {
        vibe_print_str("Ends with '!': true");
    } else {
        vibe_print_str("Ends with '!': false");
    }
    vibe_print_str("Index of 'Vibe':");
    vibe_print_int(index_of(s, "Vibe"));
    vibe_print_str("Index of 'Missing':");
    vibe_print_int(index_of(s, "Missing"));
    return 0LL;
}

// Function: to_upper
const char* to_upper(const char* s) {
    const char* result = "";
    long long i = 0LL;
    while ((i < strlen(s))) {
        char c = s[i];
        long long code = vibe_ord(c);
        if (((code >= 97LL) && (code <= 122LL))) {
            (result = vibe_string_concat(result, vibe_str(vibe_chr((code - 32LL)))));
        } else {
            (result = vibe_string_concat(result, vibe_str(c)));
        }
        (i = (i + 1LL));
    }
    return result;
}

// Function: to_lower
const char* to_lower(const char* s) {
    const char* result = "";
    long long i = 0LL;
    while ((i < strlen(s))) {
        char c = s[i];
        long long code = vibe_ord(c);
        if (((code >= 65LL) && (code <= 90LL))) {
            (result = vibe_string_concat(result, vibe_str(vibe_chr((code + 32LL)))));
        } else {
            (result = vibe_string_concat(result, vibe_str(c)));
        }
        (i = (i + 1LL));
    }
    return result;
}

// Function: substring
const char* substring(const char* s, long long start, long long end) {
    if ((start < 0LL)) {
        (start = 0LL);
    }
    if ((end > strlen(s))) {
        (end = strlen(s));
    }
    if ((start >= end)) {
        return "";
    }
    const char* result = "";
    long long i = start;
    while ((i < end)) {
        (result = vibe_string_concat(result, vibe_str(s[i])));
        (i = (i + 1LL));
    }
    return result;
}

// Function: contains
int contains(const char* s, const char* sub) {
    long long slen = strlen(s);
    long long sublen = strlen(sub);
    if ((sublen == 0LL)) {
        return 1;
    }
    if ((sublen > slen)) {
        return 0;
    }
    long long i = 0LL;
    while ((i <= (slen - sublen))) {
        const char* piece = substring(s, i, (i + sublen));
        if ((i == 7LL)) {
            vibe_print_str("Checking piece:");
            vibe_print_str(piece);
            vibe_print_str("Against:");
            vibe_print_str(sub);
        }
        if ((piece == sub)) {
            return 1;
        }
        (i = (i + 1LL));
    }
    return 0;
}

// Function: index_of
long long index_of(const char* s, const char* sub) {
    if ((strlen(sub) == 0LL)) {
        return 0LL;
    }
    if ((strlen(sub) > strlen(s))) {
        return (-1LL);
    }
    long long i = 0LL;
    while ((i <= (strlen(s) - strlen(sub)))) {
        long long j = 0LL;
        int match = 1;
        while ((j < strlen(sub))) {
            if ((s[(i + j)] != sub[j])) {
                (match = 0);
                (j = strlen(sub));
            } else {
                (j = (j + 1LL));
            }
        }
        if (match) {
            return i;
        }
        (i = (i + 1LL));
    }
    return (-1LL);
}

// Function: starts_with
int starts_with(const char* s, const char* prefix) {
    if ((strlen(prefix) > strlen(s))) {
        return 0;
    }
    long long i = 0LL;
    while ((i < strlen(prefix))) {
        if ((s[i] != prefix[i])) {
            return 0;
        }
        (i = (i + 1LL));
    }
    return 1;
}

// Function: ends_with
int ends_with(const char* s, const char* suffix) {
    if ((strlen(suffix) > strlen(s))) {
        return 0;
    }
    long long offset = (strlen(s) - strlen(suffix));
    long long i = 0LL;
    while ((i < strlen(suffix))) {
        if ((s[(offset + i)] != suffix[i])) {
            return 0;
        }
        (i = (i + 1LL));
    }
    return 1;
}

// Top-level program
long long top_level_main(void) {
    main_func();
    return 0LL;
}

// Entry point
int main(int argc, char** argv) {
    (void)argc;
    (void)argv;
    top_level_main();
    return (int)main_func();
}