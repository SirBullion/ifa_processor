# Module System

`GBA "path.ifa"` imports a source file once and compiles it as a module. `MODULE Name` supplies its namespace. Existing modules without an export declaration retain export-all compatibility.

Explicit exports use the existing call grammar inside a module:

```ifa
MODULE MATH
ISE DOUBLE(X)
    RETURN DAGBA X ATI 2
PARI
EXPORT("DOUBLE")
```

Exported functions receive an unqualified callable alias. Private functions remain qualified and are callable by functions in the same module, but external direct calls are rejected. Unknown export names are compiler errors.
