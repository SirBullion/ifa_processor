import re


class Tokenizer:

    _TOKEN_PATTERN = re.compile(
        r'''"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|'''
        r"==|!=|>=|<=|>|<|\[|\]|\(|\)|,|=|"
        r"[^\s\[\](),=!<>]+"
    )

    def tokenize(self, text: str):

        text = text.strip()

        if text == "":
            return []

        return self._TOKEN_PATTERN.findall(text)


tokenizer = Tokenizer()
