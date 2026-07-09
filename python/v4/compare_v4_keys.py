from ifa_v4_rmu import compute_frame

def check_key(make_key, label):
    seen = {}
    collisions = []

    for A in range(256):
        for B in range(256):
            frame = compute_frame(A, B)
            key = make_key(frame)

            if key in seen:
                old_A, old_B, old_frame = seen[key]
                if old_frame != frame:
                    collisions.append((key, old_A, old_B, old_frame, A, B, frame))
            else:
                seen[key] = (A, B, frame)

    print("\n" + label)
    print("=" * 70)
    print("pairs checked:", 256 * 256)
    print("unique keys:", len(seen))
    print("unsafe collisions:", len(collisions))

    if collisions:
        print("\nFirst 5 collisions:")
        for i, c in enumerate(collisions[:5]):
            key, A1, B1, F1, A2, B2, F2 = c
            print(f"\nCollision {i}")
            print("KEY:", key)
            print(f"A1=0x{A1:02X} B1=0x{B1:02X} {F1.hex()}")
            print(f"A2=0x{A2:02X} B2=0x{B2:02X} {F2.hex()}")
    else:
        print("SAFE: same key always gives same full frame")


def main():
    check_key(
        lambda f: (f.RA, f.RD, f.T),
        "KEY1 = {RA, RD, T}"
    )

    check_key(
        lambda f: (f.RA, f.RD, f.R0, f.T),
        "KEY2 = {RA, RD, R0, T}"
    )


if __name__ == "__main__":
    main()
