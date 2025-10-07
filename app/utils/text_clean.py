from __future__ import annotations

import re


_whitespace_re = re.compile(r"\s+")


def normalize_text(s: str) -> str:
    """Basic normalization: trim and collapse whitespace."""
    return _whitespace_re.sub(" ", s).strip()