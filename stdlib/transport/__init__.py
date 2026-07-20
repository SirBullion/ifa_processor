"""Transport wrappers around the canonical relation-frame implementation."""

from runtime.frame_builder import calculate_transport


def transported(value, width=8):
    return calculate_transport(value, width)


__all__ = ["calculate_transport", "transported"]
