"""Read the two structures the vault is written in: YAML front matter and Markdown tables.

The vault stays plain Markdown so people read it on GitHub and agents read it as text.
Only tables and front matter carry meaning the checks rely on.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

_SEPARATOR = re.compile(r"^\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)*\|?\s*$")


@dataclass
class Row:
    cells: dict[str, str]
    path: Path
    line: int

    def __getitem__(self, key: str) -> str:
        return self.cells.get(key, "")

    @property
    def where(self) -> str:
        return f"{self.path}:{self.line}"


@dataclass
class Table:
    header: list[str]
    rows: list[Row] = field(default_factory=list)
    line: int = 0


@dataclass
class Document:
    path: Path
    meta: dict[str, Any]
    text: str
    tables: list[Table]

    def table_with(self, *columns: str) -> Table | None:
        """The first table whose header contains all of these columns."""
        for t in self.tables:
            if all(c in t.header for c in columns):
                return t
        return None


def split_cells(line: str) -> list[str]:
    body = line.strip()
    if body.startswith("|"):
        body = body[1:]
    if body.endswith("|"):
        body = body[:-1]
    # A pipe inside backticks or escaped as \| is part of the cell.
    cells, buf, in_code, i = [], [], False, 0
    while i < len(body):
        ch = body[i]
        if ch == "\\" and i + 1 < len(body) and body[i + 1] == "|":
            buf.append("|")
            i += 2
            continue
        if ch == "`":
            in_code = not in_code
        if ch == "|" and not in_code:
            cells.append("".join(buf).strip())
            buf = []
        else:
            buf.append(ch)
        i += 1
    cells.append("".join(buf).strip())
    return cells


def parse(path: Path) -> Document:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    meta: dict[str, Any] = {}
    start = 0
    if lines and lines[0].strip() == "---":
        for j in range(1, len(lines)):
            if lines[j].strip() == "---":
                meta = yaml.safe_load("\n".join(lines[1:j])) or {}
                start = j + 1
                break

    tables: list[Table] = []
    i = start
    in_fence = False
    while i < len(lines):
        line = lines[i]
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            i += 1
            continue
        if (
            not in_fence
            and line.lstrip().startswith("|")
            and i + 1 < len(lines)
            and _SEPARATOR.match(lines[i + 1].strip())
        ):
            header = split_cells(line)
            table = Table(header=header, line=i + 1)
            i += 2
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                cells = split_cells(lines[i])
                cells += [""] * (len(header) - len(cells))
                table.rows.append(Row(dict(zip(header, cells, strict=False)), path, i + 1))
                i += 1
            tables.append(table)
            continue
        i += 1
    return Document(path=path, meta=meta, text=text, tables=tables)


def strip_code(value: str) -> str:
    """`services.request_leave` -> services.request_leave"""
    return value.strip().strip("`").strip()


def split_list(value: str) -> list[str]:
    return [strip_code(v) for v in re.split(r"[,;]", value) if strip_code(v)]
