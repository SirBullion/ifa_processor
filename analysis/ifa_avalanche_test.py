#!/usr/bin/env python3
from collections import Counter


def int_to_bits8(x: int) -> list[int]:
    """Convert integer 0–255 to 8-bit list, MSB first."""
    return [(x >> i) & 1 for i in range(7, -1, -1)]


def bits_to_int(bits: list[int]) -> int:
    """Convert bit list to integer."""
    value = 0
    for bit in bits:
        value = (value << 1) | bit
    return value


def phi_pair(a: int, b: int) -> tuple[int, int]:
    """
    Anchor–Agreement transform:
        (A, B) -> (A, A == B)

    Agreement = 1 when A == B, else 0.
    """
    anchor = a
    agreement = 1 ^ (a ^ b)   # XNOR
    return anchor, agreement


def phi_p8(x: int) -> int:
    """Apply Anchor–Agreement transform independently to four 2-bit pairs."""
    input_bits = int_to_bits8(x)
    output_bits = []

    for i in range(0, 8, 2):
        output_bits.extend(phi_pair(input_bits[i], input_bits[i + 1]))

    return bits_to_int(output_bits)


def hamming_distance(a: int, b: int) -> int:
    """Hamming distance between two 8-bit integers."""
    return (a ^ b).bit_count()


def run_avalanche_test() -> None:
    histogram = Counter()
    total_changed_bits = 0
    total_tests = 0

    for x in range(256):
        y = phi_p8(x)

        for bit_position in range(8):
            flipped_x = x ^ (1 << bit_position)
            flipped_y = phi_p8(flipped_x)

            distance = hamming_distance(y, flipped_y)

            histogram[distance] += 1
            total_changed_bits += distance
            total_tests += 1

    average_change = total_changed_bits / total_tests

    print("=" * 70)
    print("IFÁ Φ-P8 AVALANCHE / DIFFUSION TEST")
    print("=" * 70)
    print("Total tests:", total_tests)
    print("Average output bit changes:", average_change)
    print("Histogram:", dict(sorted(histogram.items())))

    print()
    print("Interpretation:")
    print("A secure 8-bit block cipher would aim for about 4 changed output bits on average.")
    print("If the average is much lower, the transform is structured and reversible,")
    print("but it is not encryption by itself.")


if __name__ == "__main__":
    run_avalanche_test()

