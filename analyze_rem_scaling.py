widths = [2, 4, 8, 16, 32, 64, 128, 256]

print("WIDTH | CPU bits | IFA REM bits | overhead")
print("------------------------------------------")

for w in widths:
    cpu_bits = w
    ifa_bits = 5 * w   # Y, R_A, R_D, R_0, T
    overhead = ifa_bits / cpu_bits

    print(f"{w:5d} | {cpu_bits:8d} | {ifa_bits:12d} | {overhead:7.1f}x")
