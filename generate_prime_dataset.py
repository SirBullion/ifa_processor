import pandas as pd
from sympy import isprime

START = 4294967000
END   = 4294969000

primes = []
composites = []

n = START

while n <= END:

    if isprime(n):
        if len(primes) < 100:
            primes.append(n)
    else:
        if len(composites) < 100:
            composites.append(n)

    if len(primes) == 100 and len(composites) == 100:
        break

    n += 1

print("Primes:", len(primes))
print("Composites:", len(composites))

rows = []

divisors = [3,5,7,11,13,17,19,23,29,31]

for is_p, numbers in [(1, primes), (0, composites)]:

    for candidate in numbers:

        for d in divisors:

            ra = candidate & d
            rd = candidate ^ d
            r0 = (~candidate & ~d) & ((1<<64)-1)

            rows.append({
                "candidate": candidate,
                "is_prime": is_p,
                "divisor": d,
                "remainder": candidate % d,
                "divisible": int(candidate % d == 0),
                "P_A": ra.bit_count(),
                "P_D": rd.bit_count(),
                "P_0": r0.bit_count()
            })

df = pd.DataFrame(rows)

df["agreement_density"] = df.P_A / 64
df["disagreement_density"] = df.P_D / 64
df["zero_density"] = df.P_0 / 64

df.to_csv("ifa_prime_dataset_100.csv", index=False)

print(df.head())

print("\nPrime means")
print(df.groupby("is_prime")[[
    "P_A",
    "P_D",
    "P_0",
    "agreement_density",
    "disagreement_density",
    "zero_density",
    "divisible"
]].mean())

print("\n=== Prime Statistics ===")
print(df.groupby("is_prime")[["P_A","P_D","P_0"]].describe())

print("\n=== Divisible Statistics ===")
print(df.groupby("divisible")[["P_A","P_D","P_0"]].describe())
