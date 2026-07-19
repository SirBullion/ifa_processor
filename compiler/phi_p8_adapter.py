#!/usr/bin/env python3
"""
IFÁ Processor V4.5
Φ-P8 Compiler Adapter

Purpose
-------
Provide one stable compiler-facing interface to the existing Φ-P8
implementation elsewhere in the IFÁ Processor repository.

The compiler must follow:

    Binary
        ↓
    real Φ-P8
        ↓
    relation canonicalisation

This adapter deliberately does not invent a second Φ-P8 transform.
"""

from __future__ import annotations

import importlib
import os
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PhiP8Backend:
    module_name: str
    function_name: str
    function: Callable[[Any], Any]


# Add a candidate here only when it corresponds to an existing project module.
DEFAULT_CANDIDATES: tuple[tuple[str, str], ...] = (
    ("core.phi_p8", "phi_p8"),
    ("core.phi_p8", "transform_phi_p8"),
    ("core.phi_p8_transform", "phi_p8"),
    ("core.phi_p8_transform", "transform"),
    ("processor.phi_p8", "phi_p8"),
    ("processor.phi_p8", "transform"),
    ("architecture.phi_p8", "phi_p8"),
    ("architecture.phi_p8", "transform"),
    ("relation.phi_p8", "phi_p8"),
    ("relation.phi_p8", "transform"),
    ("rtl_model.phi_p8", "phi_p8"),
    ("language_v3.phi_p8", "phi_p8"),
    ("python.v5.ifa_phi_p8", "phi_p8"),
)


_backend: PhiP8Backend | None = None


def _load_explicit_backend() -> PhiP8Backend | None:
    """
    Load a backend specified as:

        IFA_PHI_P8_BACKEND=module.path:function_name
    """

    specification = os.environ.get(
        "IFA_PHI_P8_BACKEND",
        "",
    ).strip()

    if not specification:
        return None

    if ":" not in specification:
        raise RuntimeError(
            "IFA_PHI_P8_BACKEND must use "
            "'module.path:function_name' format."
        )

    module_name, function_name = specification.split(
        ":",
        1,
    )

    module = importlib.import_module(module_name)

    function = getattr(
        module,
        function_name,
        None,
    )

    if not callable(function):
        raise RuntimeError(
            f"{module_name}.{function_name} is not callable."
        )

    return PhiP8Backend(
        module_name=module_name,
        function_name=function_name,
        function=function,
    )


def _load_candidate_backend() -> PhiP8Backend | None:
    """
    Try known repository module layouts.
    """

    for module_name, function_name in DEFAULT_CANDIDATES:
        try:
            module = importlib.import_module(
                module_name
            )
        except ImportError:
            continue

        function = getattr(
            module,
            function_name,
            None,
        )

        if callable(function):
            return PhiP8Backend(
                module_name=module_name,
                function_name=function_name,
                function=function,
            )

    return None


def get_phi_p8_backend() -> PhiP8Backend:
    """
    Return the real Φ-P8 backend.

    Failure is explicit because silently reverting to ordinary binary would
    make relation-equivalence results appear valid when they are not based
    on the actual IFÁ transform.
    """

    global _backend

    if _backend is not None:
        return _backend

    _backend = (
        _load_explicit_backend()
        or _load_candidate_backend()
    )

    if _backend is None:
        raise RuntimeError(
            "No real Φ-P8 implementation could be imported.\n"
            "\n"
            "Locate the existing implementation with:\n"
            "\n"
            "  grep -RIn --include='*.py' "
            "\"def .*phi.*p8\\|def .*Phi.*P8\\|Φ-P8\" .\n"
            "\n"
            "Then select it with:\n"
            "\n"
            "  export IFA_PHI_P8_BACKEND="
            "'module.path:function_name'\n"
            "\n"
            "Example:\n"
            "\n"
            "  export IFA_PHI_P8_BACKEND="
            "'core.phi_p8:phi_p8'\n"
        )

    return _backend


def _normalise_phi_output(value: Any) -> tuple[int, ...] | str:
    """
    Convert backend output into a stable, hashable representation.

    Supported outputs:
        int
        binary string
        list/tuple of bits or coordinates
        objects with to_tuple()
        objects with bits
        objects with coordinates
    """

    if isinstance(value, bool):
        return (int(value),)

    if isinstance(value, int):
        if value < 0:
            return str(value)

        width = max(
            8,
            value.bit_length(),
        )

        return tuple(
            int(bit)
            for bit in f"{value:0{width}b}"
        )

    if isinstance(value, str):
        compact = value.strip().replace(
            " ",
            "",
        )

        if compact and set(compact) <= {"0", "1"}:
            return tuple(
                int(bit)
                for bit in compact
            )

        return value.strip()

    if isinstance(value, (list, tuple)):
        return tuple(value)

    to_tuple = getattr(
        value,
        "to_tuple",
        None,
    )

    if callable(to_tuple):
        return tuple(to_tuple())

    if hasattr(value, "bits"):
        return tuple(value.bits)

    if hasattr(value, "coordinates"):
        return tuple(value.coordinates)

    return repr(value)


def phi_p8(value: Any) -> tuple[int, ...] | str:
    """
    Apply the repository's real Φ-P8 transform.
    """

    backend = get_phi_p8_backend()

    transformed = backend.function(value)

    return _normalise_phi_output(
        transformed
    )


def backend_description() -> str:
    backend = get_phi_p8_backend()

    return (
        f"{backend.module_name}:"
        f"{backend.function_name}"
    )


if __name__ == "__main__":
    print("=" * 72)
    print("IFÁ PROCESSOR V4.5 Φ-P8 ADAPTER")
    print("=" * 72)

    try:
        print(
            "Backend:",
            backend_description(),
        )

        for test_value in (0, 1, 2, 3, 8, 15, 255):
            print(
                f"{test_value:>3} -> "
                f"{phi_p8(test_value)}"
            )

    except RuntimeError as error:
        print(error)
        raise SystemExit(1)
