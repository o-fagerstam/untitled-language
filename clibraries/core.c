#include <stdio.h>
#include <stdlib.h>

void __CORE__malloc_null_chk(void* ptr, char* name) {
  if (!ptr) {
    fprintf(stderr, "Error: Failed to allocate memory for object %s\n", name);
    exit(-1);
  }
}
