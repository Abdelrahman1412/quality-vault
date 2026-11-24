"""vault.yaml: which app the vault describes, and how the app's code splits into modules."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


class ConfigError(ValueError):
    pass


@dataclass(frozen=True)
class Module:
    name: str
    prefix: str  # rule ids look like <prefix>-R01, test cases <prefix>-TC01
    symbols: tuple[str, ...]  # "<file stem>.<name>" the module owns


@dataclass(frozen=True)
class Config:
    root: Path  # the folder holding vault.yaml
    project: str
    vault_dir: Path
    subject_path: Path
    subject_scan: tuple[str, ...]
    subject_tests: str
    seed_contract: str | None
    layers: tuple[str, ...]
    justify_from: str | None
    modules: tuple[Module, ...]
    ignored: dict[str, str] = field(default_factory=dict)  # symbol -> reason

    def module(self, name: str) -> Module:
        for m in self.modules:
            if m.name == name:
                return m
        raise KeyError(name)

    @property
    def owner(self) -> dict[str, str]:
        return {s: m.name for m in self.modules for s in m.symbols}


def _req(raw: dict[str, Any], key: str, where: str) -> Any:
    if key not in raw:
        raise ConfigError(f"{where}: missing '{key}'")
    return raw[key]


def load(path: Path | str = "vault.yaml", subject_override: str | None = None) -> Config:
    path = Path(path).resolve()
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    root = path.parent
    subject = _req(raw, "subject", "vault.yaml")
    env_var = subject.get("env_var")
    subject_path = subject_override or (env_var and os.environ.get(env_var)) or subject["path"]

    modules: list[Module] = []
    prefixes: set[str] = set()
    for name, m in (_req(raw, "modules", "vault.yaml") or {}).items():
        prefix = _req(m, "prefix", f"modules.{name}")
        if not isinstance(prefix, str) or not prefix.isalnum():
            # YAML reads a bare OFF, NO or ON as a boolean: quote prefixes.
            raise ConfigError(f'modules.{name}: prefix must be a quoted string like "LV"')
        if prefix in prefixes:
            raise ConfigError(f"modules.{name}: prefix {prefix} is used twice")
        prefixes.add(prefix)
        modules.append(Module(name=name, prefix=prefix, symbols=tuple(m.get("symbols", []))))

    seen: dict[str, str] = {}
    for m in modules:
        for s in m.symbols:
            if s in seen:
                raise ConfigError(f"{s} is owned by both {seen[s]} and {m.name}")
            seen[s] = m.name

    tests = raw.get("test_layers", {})
    layers = tuple(tests.get("order", ["unit", "service", "api", "e2e"]))
    justify_from = tests.get("justify_from")
    if justify_from is not None and justify_from not in layers:
        raise ConfigError(f"test_layers.justify_from '{justify_from}' is not a layer")

    return Config(
        root=root,
        project=raw.get("project", "Unnamed project"),
        vault_dir=root / raw.get("vault_dir", "vault"),
        subject_path=(root / subject_path).resolve(),
        subject_scan=tuple(_req(subject, "scan", "subject")),
        subject_tests=subject.get("tests", "tests"),
        seed_contract=subject.get("seed_contract"),
        layers=layers,
        justify_from=justify_from,
        modules=tuple(modules),
        ignored={k: str(v) for k, v in (raw.get("ignore") or {}).items()},
    )
