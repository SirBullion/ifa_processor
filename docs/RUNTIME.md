# Runtime

Runtime is the stable execution boundary. It validates an `ExecutionRequest`, delegates it to the active backend through BackendManager, and returns the backend result. Program sequencing, functions, recursion, scopes, arrays, and branches belong above Runtime; native arithmetic belongs below it.

Call frames contain parameters and locals and link to a parent frame. Globals remain visible unless shadowed. Arithmetic inside every frame still travels through Runtime and the selected backend.
