# IFÁ Tonal Interface Contract

IFÁ uses Yoruba àmì ohùn as functional interface information. The marks are
not decoration: they distinguish an input action from acceptance, permission,
and rejection.

| Interface text | System meaning |
|---|---|
| `KỌ WỌLÉ >` | Write/enter input here. |
| `Ó WỌLÉ` | The input entered the interface and was accepted for processing. |
| `Ó LÈ WỌLÉ — ÀṢẸ` | Security phase: authorization was granted; it may enter. |
| `Ó LÈ WỌLÉ — ÀTÚNṢE` | Execution phase: a recoverable input (at least 75% confidence) was corrected and may execute. |
| `KÒ WỌLÉ` | It did not enter or was rejected by validation, permission, or execution. |

Example:

```text
KỌ WỌLÉ > 2+2
Ó WỌLÉ
4
```

Rejected input:

```text
KỌ WỌLÉ > BADUNKNOWN
Ó WỌLÉ
KÒ WỌLÉ: unknown input
```

The second example is not contradictory. `Ó WỌLÉ` confirms that the interface
received the text. `KÒ WỌLÉ` reports that the submitted meaning did not pass
language, permission, or execution validation.

Permission example:

```text
Ó LÈ WỌLÉ — ÀṢẸ: Permission granted: OGBE → OYEKU
```

Execution correction example:

```text
KỌ WỌLÉ > SUM FIST 7 PTIME
Ó WỌLÉ
Ó LÈ WỌLÉ — ÀTÚNṢE
Suggested : SUM THE FIRST 7 PRIME NUMBERS
Primes    : 2 + 3 + 5 + 7 + 11 + 13 + 17
Result    : 58
```

The suffixes keep the two meanings separate: `ÀṢẸ` is checked in the security phase; `ÀTÚNṢE` is emitted only by execution correction. They cannot authorize one another. Below 75% confidence, execution returns `KÒ WỌLÉ` and does not run the suggestion.

This contract applies to the `oduifa` GUI, OHÙN shell, IFÁ monitor, audit
runner, first-time guide, and user-facing diagnostics.
