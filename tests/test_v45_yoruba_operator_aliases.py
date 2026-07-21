import unittest

from interpreter.interpreter import Interpreter
from parser.parser import parser


class V45YorubaOperatorAliasTests(unittest.TestCase):
    def execute(self, source):
        return Interpreter().execute(
            parser.parse_program(source, source_name="<accent-test>")
        )

    def test_all_documented_prefix_spellings(self):
        cases = {
            "PÀPỌ̀ 6 ATI 2": 8,
            "YỌ 6 ATI 2": 4,
            "DÁGBA 6 ATI 2": 12,
            "PÍN 6 ATI 2": 3,
            "KÙ 7 ATI 2": 1,
            "GBÉ 3 ATI 2": 9,
            "ṢẸ̀DÁ 6 ATI 2": 0,
            "JÙ 6 ATI 2": 1,
            "KERÉ 6 ATI 2": 0,
        }
        for source, expected in cases.items():
            with self.subTest(source=source):
                self.assertEqual(self.execute(source), expected)

    def test_documented_infix_relation_spellings(self):
        cases = {
            "6 ṢẸ̀DÁ 6": 1,
            "6 JÙ 2": 1,
            "2 KERÉ 6": 1,
        }
        for source, expected in cases.items():
            with self.subTest(source=source):
                self.assertEqual(self.execute(source), expected)


if __name__ == "__main__":
    unittest.main()
