# ============================================================
# IFÁ V4 KEY SAFETY VERIFICATION
#
# Checks:
# KEY = {RA, RD, T}
#
# Question:
# Can same KEY produce different FRAME?
#
# If yes, RMU reuse is unsafe.
# If no, RMU reuse is safe under current frame definition.
# ============================================================

from ifa_v4_rmu import compute_frame

seen = {}
collisions = []

for A in range(256):
    for B in range(256):
        frame = compute_frame(A, B)
        key = frame.key()

        if key in seen:
            old_A, old_B, old_frame = seen[key]

            if old_frame != frame:
                collisions.append(
                    (key, old_A, old_B, old_frame, A, B, frame)
                )
        else:
            seen[key] = (A, B, frame)

print("IFÁ V4 KEY SAFETY VERIFICATION")
print("=" * 70)
print("Total input pairs checked:", 256 * 256)
print("Unique keys:", len(seen))
print("Unsafe collisions:", len(collisions))

if collisions:
    print("\nFAILED: KEY is unsafe")
    print("=" * 70)

    for i, c in enumerate(collisions[:10]):
        key, A1, B1, F1, A2, B2, F2 = c
        print(f"\nCollision {i}")
        print("KEY:", key)
        print(f"A1=0x{A1:02X} B1=0x{B1:02X} FRAME1={F1.hex()}")
        print(f"A2=0x{A2:02X} B2=0x{B2:02X} FRAME2={F2.hex()}")

else:
    print("\nPASSED: KEY is safe")
    print("Same KEY always returns same full FRAME")
