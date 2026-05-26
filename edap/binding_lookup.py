from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Mapping

from edap.bindings import Binding, REQUIRED_BINDINGS, read_bindings


KEY_ALIASES = {
    "Space": "space",
    "Return": "enter",
    "Enter": "enter",
    "Tab": "tab",
    "Escape": "escape",
    "Esc": "escape",
    "Backspace": "backspace",
    "Delete": "delete",
    "Insert": "insert",
    "Home": "home",
    "End": "end",
    "PageUp": "page_up",
    "PageDown": "page_down",
    "UpArrow": "up",
    "DownArrow": "down",
    "LeftArrow": "left",
    "RightArrow": "right",
    "LeftShift": "left_shift",
    "RightShift": "right_shift",
    "LeftAlt": "left_alt",
    "RightAlt": "right_alt",
    "LeftControl": "left_control",
    "RightControl": "right_control",
}


@dataclass(frozen=True)
class NormalizedBinding:
    key: str
    modifier: str | None = None

    def to_dict(self) -> dict[str, str | None]:
        return asdict(self)


@dataclass(frozen=True)
class BindingLookupResult:
    action: str
    status: str
    binding: NormalizedBinding | None = None
    reason: str | None = None

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "action": self.action,
            "status": self.status,
        }
        if self.binding is not None:
            payload["binding"] = self.binding.to_dict()
        if self.reason is not None:
            payload["reason"] = self.reason
        return payload


class BindingLookup:
    def __init__(self, results: Mapping[str, BindingLookupResult]) -> None:
        self._results = dict(results)

    def resolve(self, action: str) -> BindingLookupResult:
        return self._results.get(
            action,
            BindingLookupResult(
                action=action,
                status="missing",
                reason="action was not loaded into the binding lookup",
            ),
        )

    def get(self, action: str) -> NormalizedBinding | None:
        result = self.resolve(action)
        return result.binding if result.status == "ok" else None

    def supported_actions(self) -> dict[str, NormalizedBinding]:
        return {
            action: result.binding
            for action, result in self._results.items()
            if result.status == "ok" and result.binding is not None
        }

    def issues(self) -> dict[str, BindingLookupResult]:
        return {
            action: result
            for action, result in self._results.items()
            if result.status != "ok"
        }

    def to_dict(self) -> dict[str, dict[str, object]]:
        return {
            action: result.to_dict()
            for action, result in sorted(self._results.items())
        }


def normalize_action_binding(binding: Binding) -> NormalizedBinding:
    key = normalize_internal_key_name(binding.key)
    modifier = normalize_internal_key_name(binding.modifier) if binding.modifier else None
    return NormalizedBinding(key=key, modifier=modifier)


def normalize_internal_key_name(token: str) -> str:
    if token in KEY_ALIASES:
        return KEY_ALIASES[token]
    if len(token) == 1 and token.isalnum():
        return token.lower()
    if token.startswith("NumPad") and token[6:].isdigit():
        return f"numpad_{token[6:]}"
    if token.startswith("F") and token[1:].isdigit():
        return token.lower()
    if token.isalpha():
        return token.lower()
    raise ValueError(f"unsupported binding token: {token}")


def build_binding_lookup(
    bindings: Mapping[str, Binding],
    missing_actions: Iterable[str] = (),
    actions: Iterable[str] | None = None,
) -> BindingLookup:
    wanted = list(actions or REQUIRED_BINDINGS)
    missing = set(missing_actions)
    results: dict[str, BindingLookupResult] = {}

    for action in wanted:
        binding = bindings.get(action)
        if binding is None or action in missing:
            results[action] = BindingLookupResult(
                action=action,
                status="missing",
                reason="no keyboard binding was resolved for this action",
            )
            continue
        try:
            normalized = normalize_action_binding(binding)
        except ValueError as exc:
            results[action] = BindingLookupResult(
                action=action,
                status="unsupported",
                reason=str(exc),
            )
            continue
        results[action] = BindingLookupResult(
            action=action,
            status="ok",
            binding=normalized,
        )

    return BindingLookup(results)


def load_binding_lookup(bindings_file: Path, actions: list[str] | None = None) -> BindingLookup:
    bindings, missing = read_bindings(bindings_file, keys_to_obtain=actions)
    return build_binding_lookup(bindings, missing_actions=missing, actions=actions)
