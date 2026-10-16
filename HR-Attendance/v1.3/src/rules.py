"""Load attendance rules from 03_MASTER_DATA/rules.toml.

rules.toml is the single source of truth for rule values (see CLAUDE.md
section 6). This module never hard-codes a rule value; it only reads,
validates and exposes the file's contents. Read-only on rules.toml.

Usage: python -m src.rules check
"""
from __future__ import annotations

import sys
try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib
from dataclasses import dataclass
from pathlib import Path

DEFAULT_RULES_PATH = Path(__file__).resolve().parent.parent / "03_MASTER_DATA" / "rules.toml"


class RuleValidationError(Exception):
    pass


class UnknownRuleError(KeyError):
    pass


@dataclass
class Rule:
    rule_id: str
    value: object
    status: str
    question: str
    source: str
    options: list | None
    label: str = ""


class Rules:
    def __init__(self, rules: dict[str, Rule]):
        self._rules = rules

    def _rule(self, rule_id: str) -> Rule:
        try:
            return self._rules[rule_id]
        except KeyError:
            raise UnknownRuleError(
                f"Unknown rule id {rule_id!r}: not found in rules.toml"
            ) from None

    def get(self, rule_id: str):
        return self._rule(rule_id).value

    def status(self, rule_id: str) -> str:
        return self._rule(rule_id).status

    def question(self, rule_id: str) -> str:
        return self._rule(rule_id).question

    def is_confirmed(self, rule_ids: list[str]) -> bool:
        """True only if every listed rule is CONFIRMED. Unknown ids raise."""
        return all(self._rule(rule_id).status == "CONFIRMED" for rule_id in rule_ids)

    def all_rules(self) -> list[Rule]:
        return list(self._rules.values())


def _validate(rule_id: str, raw: dict, allowed_status: list[str]) -> list[str]:
    errors = []
    status = raw.get("status")
    if status not in allowed_status:
        errors.append(
            f"{rule_id}: status {status!r} is not one of {allowed_status}"
        )
    if status == "CONFIRMED" and not raw.get("source"):
        errors.append(f"{rule_id}: status is CONFIRMED but source is empty")
    options = raw.get("options")
    if options:
        value = raw.get("value")
        if value not in options:
            errors.append(f"{rule_id}: value {value!r} is not in options {options}")
    return errors


def load_rules(rules_path: Path = DEFAULT_RULES_PATH) -> Rules:
    """Load and validate rules.toml. Raises RuleValidationError on any violation."""
    rules_path = Path(rules_path)
    with open(rules_path, "rb") as f:
        data = tomllib.load(f)

    allowed_status = data.get("meta", {}).get("allowed_status", [])
    raw_rules = data.get("rules", {})

    all_errors: list[str] = []
    rules: dict[str, Rule] = {}
    for rule_id, raw in raw_rules.items():
        all_errors.extend(_validate(rule_id, raw, allowed_status))
        rules[rule_id] = Rule(
            rule_id=rule_id,
            value=raw.get("value"),
            status=raw.get("status"),
            question=raw.get("question", ""),
            source=raw.get("source", ""),
            options=raw.get("options"),
            label=raw.get("label", ""),
        )

    if all_errors:
        raise RuleValidationError("\n".join(all_errors))

    return Rules(rules)


def _check(rules_path: Path = DEFAULT_RULES_PATH) -> int:
    try:
        rules = load_rules(rules_path)
    except RuleValidationError as exc:
        print("Validation errors:")
        print(str(exc))
        return 1
    except Exception as exc:  # file missing, bad TOML, etc.
        print(f"Could not load {rules_path}: {exc}")
        return 1

    all_rules = rules.all_rules()
    counts = {"CONFIRMED": 0, "ASSUMED": 0, "OPEN": 0}
    for rule in all_rules:
        counts[rule.status] = counts.get(rule.status, 0) + 1

    print(f"Total rules: {len(all_rules)}")
    for status in ("CONFIRMED", "ASSUMED", "OPEN"):
        print(f"  {status}: {counts.get(status, 0)}")

    non_confirmed = [r for r in all_rules if r.status != "CONFIRMED"]
    if non_confirmed:
        print("\nNon-confirmed rules:")
        for rule in sorted(non_confirmed, key=lambda r: r.rule_id):
            print(f"  [{rule.question or '?'}] {rule.rule_id} ({rule.status})")

    print("\nNo validation errors.")
    return 0


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "check":
        sys.exit(_check())
    print("Usage: python -m src.rules check")
    sys.exit(1)
