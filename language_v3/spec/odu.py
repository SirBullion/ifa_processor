# IFÁ V3 — ODÙ Kernel Specification
#
# ODÙ is the kernel/activity space of the IFÁ machine.
# It owns the language grammar, operators, values, and number classes.

ODU_KERNEL = {

    "PROGRAM": {
        "rule": "STATEMENT*",
        "meaning": "A program is a sequence of statements.",
    },

    "STATEMENT": {
        "forms": [
            "BERE",
            "DURO",
            "TE ODU",
            "BINARY_EXPR",
        ],
        "meaning": "A statement is one executable IFÁ language unit.",
    },

    "BINARY_EXPR": {
        "rule": "OPERATOR VALUE ATI VALUE",
        "meaning": "A binary expression applies an operator to two values.",
        "examples": [
            "PAPO 2 ATI 1",
            "YO 5 ATI 2",
            "SEDA 0xA5 ATI 0x11",
        ],
    },

    "OPERATORS": {
        "arithmetic": [
            "PAPO",
            "YO",
            "SOPO",
            "PIN",
            "IYOKU",
            "ILOPOMO",
            "AFIKUNMO",
        ],
        "relation": [
            "SEDA",
            "FARAPO",
            "YATO",
            "YI",
            "GBE",
            "PADA",
        ],
    },

    "VALUES": {
        "types": [
            "INTEGER",
            "HEX",
            "NUMBER_WORD",
            "REGISTER",
            "ADÓ",
        ],
    },

    "ADO": {
        "meaning": "Register/gourd/state container.",
        "forms": [
            "A",
            "B",
            "ADO",
            "ADO1",
            "ADO2",
        ],
    },

    "OYELA": {
        "meaning": "Output/result expression of the machine.",
        "forms": [
            "Y",
            "OYELA",
        ],
    },

    "NUMBERS": {
        "OKAN": 1,
        "MEJI": 2,
        "META": 3,
        "MERIN": 4,
        "MARUN": 5,
        "MEFA": 6,
        "MEJE": 7,
        "MEJO": 8,
        "MESAN": 9,
        "MEWA": 10,
    },

    "OUTPUT": {
        "TE ODU": "Print current Odù relation state.",
        "DAIFA": "Print the sixteen Ojú Odù.",
    },
}
