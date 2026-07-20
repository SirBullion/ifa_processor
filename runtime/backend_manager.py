from backends.python.backend import python_backend
from backends.rtl.backend import rtl_backend
from backends.quantum.backend import quantum_backend


class BackendManager:

    def __init__(self):

        self._backends = {
            "python": python_backend,
            "rtl": rtl_backend,
            "quantum": quantum_backend,
        }

        self._active = "python"

    # --------------------------------------------

    @property
    def backend(self):

        return self._backends[self._active]

    @property
    def backend_name(self):

        return self._active

    # --------------------------------------------

    def register(self, name, backend):

        self._backends[name] = backend

    # --------------------------------------------

    def use(self, name):

        if name not in self._backends:
            raise RuntimeError(f"Unknown backend '{name}'")

        self._active = name

    # --------------------------------------------

    def available(self):

        return list(self._backends.keys())


backend_manager = BackendManager()
