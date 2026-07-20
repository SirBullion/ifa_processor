"""Source-aware compiler diagnostics without changing parser interfaces."""

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class CompilerDiagnostic:
    filename: str
    line: int
    column: int
    message: str
    offending_token: str | None = None
    expected_token: str | None = None

    def format(self):
        parts = [f"{self.filename}:{self.line}:{self.column}: {self.message}"]
        if self.offending_token:
            parts.append(f"  offending token: {self.offending_token}")
        if self.expected_token:
            parts.append(f"  expected token: {self.expected_token}")
        return "\n".join(parts)


def diagnostic_from_exception(error, source, source_name="<source>"):
    text = str(error)
    match = re.match(r"^(.*?):(\d+):\s*(.*)$", text, re.DOTALL)
    if match:
        filename, line, message = match.group(1), int(match.group(2)), match.group(3)
    else:
        filename, line, message = source_name, 1, text
    physical = source.splitlines()
    line_text = physical[line - 1] if 0 < line <= len(physical) else ""
    token_match = re.search(
        r"Unexpected token(?: in expression)?:\s*([^\s.]+)|Unexpected\s+([^\s.]+)",
        message, re.IGNORECASE,
    )
    offending = next((x for x in token_match.groups() if x), None) if token_match else None
    expected_match = re.search(
        r"Expected(?: keyword)?\s+['\"]?([^'\"\s.,]+)", message, re.IGNORECASE
    )
    expected = expected_match.group(1) if expected_match else None
    search = offending or expected
    column = line_text.upper().find(search.upper()) + 1 if search else 0
    if column <= 0:
        column = len(line_text) - len(line_text.lstrip()) + 1
    return CompilerDiagnostic(
        filename, line, column, message, offending, expected
    )


def format_diagnostic(error, source, source_name="<source>"):
    return diagnostic_from_exception(error, source, source_name).format()
