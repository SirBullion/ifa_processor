# IFÁ V3 Ontology

## Core Computational Ontology

| IFÁ Term | Meaning | Computing Role |
|---|---|---|
| OHÙN IFÁ | Voice of Ifá | Terminal / shell |
| Ọ̀RỌ̀ | Word / code / script | Source code, assembly, machine expression |
| ODÙ | Odù | Kernel / activity space |
| ÒFIN | Law / rule | Grammar |
| ÌTUMỌ̀ | Meaning | Semantic analysis |
| ÌṢẸ́ | Work | Execution |
| ÀBÁJÁDE | Outcome | Result / output |
| ADÓ | Gourd/container | Register |
| OYÈLÁ | Output/result expression | Output register / result |

---

## Execution Flow

User enters Ọ̀RỌ̀ through OHÙN IFÁ.

OHÙN IFÁ sends Ọ̀RỌ̀ to ODÙ.

ODÙ applies ÒFIN.

ODÙ derives ÌTUMỌ̀.

ÌTUMỌ̀ becomes ÌṢẸ́.

ÌṢẸ́ produces ÀBÁJÁDE.

---

## Flow Diagram

USER
  ↓
OHÙN IFÁ
  ↓
Ọ̀RỌ̀
  ↓
ODÙ
  ↓
ÒFIN
  ↓
ÌTUMỌ̀
  ↓
ÌṢẸ́
  ↓
ÀBÁJÁDE

---

## Design Rule

The IFÁ processor does not execute "instructions."

It receives Ọ̀RỌ̀, interprets ÌTUMỌ̀ through ODÙ, performs ÌṢẸ́, and produces ÀBÁJÁDE.


## YÀRÁ ODÙ

YÀRÁ is an Odù execution room.

A YÀRÁ gives a human-readable name to an execution address and may later
contain relation memory, security context, frame state, and reversible state.

Current mapping:

    YARA OGBE -> address 0x00

The programmer enters a YÀRÁ by Odù name while the processor continues to
execute using its physical address.
