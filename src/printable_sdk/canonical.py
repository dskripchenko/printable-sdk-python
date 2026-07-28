"""PHP-compatible payload canonicalization.

Byte-identical to the Printable server (``App\\Auth\\HashSigner``):

- recursive key sort for objects (lists keep their order);
- PHP ``JSON_NUMERIC_CHECK`` semantics: numeric strings become numbers
  ("42" -> 42, "100.0" -> 100, "1e3" -> 1000, "007" -> 7);
- empty objects encode as ``[]`` (PHP array semantics);
- objects with sequential "0".."n" keys encode as arrays;
- unicode and slashes are not escaped.

Known limitation (same as PHP): integers beyond 2**53 lose precision
on the JavaScript side; Python/PHP agree on arbitrary ints.
"""

from __future__ import annotations

import json
import re
from typing import Any

_NUMERIC_RE = re.compile(r"^[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?$")


def _is_numeric_string(value: str) -> bool:
    return bool(_NUMERIC_RE.match(value.strip())) and value.strip() != ""


def _to_number(value: str) -> int | float:
    number = float(value.strip())
    if number.is_integer():
        return int(number)
    return number


def _php_ksort_keys(keys: list[str]) -> list[str]:
    """PHP ksort: числовые ключи сравниваются как числа, прочие — как строки."""

    def sort_key(key: str) -> tuple[int, float | str]:
        if _is_numeric_string(key):
            return (0, float(key))
        return (1, key)

    return sorted(keys, key=sort_key)


def _transform(value: Any) -> Any:
    if isinstance(value, str):
        if _is_numeric_string(value):
            return _to_number(value)
        return value
    if isinstance(value, (list, tuple)):
        return [_transform(item) for item in value]
    if isinstance(value, dict):
        keys = [str(k) for k in value.keys()]
        if not keys:
            return []  # PHP: пустой объект после json_decode(assoc) — []
        if keys == [str(i) for i in range(len(keys))]:
            return [_transform(value[k]) for k in value.keys()]
        return {k: _transform(value[k]) for k in _php_ksort_keys(keys)}
    return value


def canonicalize(payload: dict[str, Any]) -> str:
    """Canonical JSON string of *payload* for strict-mode signing."""
    return json.dumps(_transform(payload), ensure_ascii=False, separators=(",", ":"))
