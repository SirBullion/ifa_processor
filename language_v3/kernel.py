#!/usr/bin/env python3

from language_v3.spec.odu import ODU_KERNEL
from language_v3.spec.dictionary import ALIASES
from language_v3.spec.numbers import NUMBER_WORDS
from language_v3.spec.operators import OPERATORS

class IfaKernel:

    def __init__(self):

        self.odu = ODU_KERNEL
        self.dictionary = ALIASES
        self.numbers = NUMBER_WORDS
        self.operators = OPERATORS

    def info(self):

        print("====================================")
        print("      IFÁ V3 ODÙ KERNEL")
        print("====================================")
        print("Grammar     :", self.odu["PROGRAM"]["rule"])
        print("Dictionary  :", len(self.dictionary))
        print("Numbers     :", len(self.numbers))
        print("Operators   :", len(self.operators))
        print("====================================")

kernel = IfaKernel()

if __name__ == "__main__":
    kernel.info()
