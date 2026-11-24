"""The findings register: every mistake and test finding, once.

`qv finding add` refuses a finding the register already holds: same signature,
or a title close enough to an existing one. The answer is to update that row,
so a known problem collects evidence instead of copies.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from datetime import date

from quality_vault.subject import Subject
from quality_vault.vault import Finding, Vault

STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "in", "is", "it",
    "its", "of", "on", "or", "that", "the", "to", "when", "with", "without", "not", "no",
}  # fmt: skip
SIMILAR = 0.5


def words(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in STOPWORDS}


def similarity(a: str, b: str) -> float:
    wa, wb = words(a), words(b)
    if not wa or not wb:
        return 0.0
    return len(wa & wb) / len(wa | wb)


def normalise_signature(sig: str) -> str:
    return re.sub(r"[^a-z0-9:]+", "-", sig.lower()).strip("-")


@dataclass(frozen=True)
class Duplicate:
    existing: Finding
    reason: str


def find_duplicates(v: Vault, signature: str, title: str) -> list[Duplicate]:
    sig = normalise_signature(signature)
    out: list[Duplicate] = []
    for f in v.findings:
        if normalise_signature(f.signature) == sig:
            out.append(Duplicate(f, f"same signature '{sig}'"))
        elif (score := similarity(title, f.title)) >= SIMILAR:
            out.append(Duplicate(f, f"title {round(score * 100)}% similar"))
    return out


def next_id(v: Vault) -> str:
    numbers = [int(f.id[3:]) for f in v.findings if re.fullmatch(r"TF-\d+", f.id)]
    return f"TF-{(max(numbers, default=0) + 1):03d}"


def add(
    v: Vault,
    *,
    area: str,
    title: str,
    signature: str,
    rank: str,
    reverify: str,
    today: date | None = None,
) -> str:
    dups = find_duplicates(v, signature, title)
    if dups:
        lines = [f"  {d.existing.id}: {d.existing.title} ({d.reason})" for d in dups]
        raise ValueError(
            "already in the register; add your evidence to that row instead:\n" + "\n".join(lines)
        )
    if rank not in {"R1", "R2", "R3", "R4"}:
        raise ValueError("rank must be R1 (hides other failures) to R4 (cosmetic)")
    if not reverify.strip():
        raise ValueError("every finding needs a re-verify command, or it cannot be closed later")
    fid = next_id(v)
    today = today or date.today()
    cells = [
        fid,
        today.isoformat(),
        area,
        title.replace("|", "/"),
        f"`{normalise_signature(signature)}`",
        rank,
        "open",
        f"`{reverify.replace('|', chr(92) + '|')}`",
    ]
    text = v.register_path.read_text(encoding="utf-8")
    lines = text.splitlines()
    # Insert after the last row of the register table, keeping any text below it.
    last = max(f.row.line for f in v.findings) if v.findings else _header_end(lines)
    lines.insert(last, "| " + " | ".join(cells) + " |")
    v.register_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return fid


def _header_end(lines: list[str]) -> int:
    for i, line in enumerate(lines):
        if line.startswith("| ID ") and i + 1 < len(lines):
            return i + 2
    raise ValueError("the register has no table")


@dataclass(frozen=True)
class Reverified:
    finding: Finding
    returncode: int
    output: str

    @property
    def verdict(self) -> str:
        # The command is written to FAIL while the finding is real (like a regression test).
        return "still reproduces" if self.returncode != 0 else "clean: close as stale or fixed"


def reverify_open(v: Vault, subj: Subject, timeout: int = 600) -> list[Reverified]:
    """Run each open finding's re-verify command inside the app's checkout."""
    out: list[Reverified] = []
    for f in v.findings:
        if not f.status.startswith("open") or not f.reverify:
            continue
        proc = subprocess.run(
            f.reverify,
            shell=True,
            cwd=subj.root,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        tail = (proc.stdout + proc.stderr).strip().splitlines()[-3:]
        out.append(Reverified(f, proc.returncode, "\n".join(tail)))
    return out
