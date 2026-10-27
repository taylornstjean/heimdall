# Copyright 2026 Taylor St Jean

from datetime import datetime
from dataclasses import dataclass
from typing import Any, ClassVar

from .col import NEOCPCol


@dataclass(frozen=True)
class NEOCPAdd:
    kind: ClassVar[str] = "added"
    desig: str
    time: datetime

@dataclass(frozen=True)
class NEOCPRemove:
    kind: ClassVar[str] = "removed"
    desig: str
    time: datetime

@dataclass(frozen=True)
class NEOCPUpdate:
    kind: ClassVar[str] = "updated"
    desig: str
    changes: dict[NEOCPCol, tuple[Any, Any]]
    time: datetime

NEOCPDiff = NEOCPAdd | NEOCPRemove | NEOCPUpdate
