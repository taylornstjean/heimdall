# Copyright 2026 Taylor St Jean

import time
from collections.abc import Sequence
from typing import Any
from threading import Lock
from datetime import datetime, UTC

import polars as pl
import requests

from heimdall_neo import __version__

from .col import NEOCPCol
from .table import NEOCPSnapshot
from .update import NEOCPDiff, NEOCPAdd, NEOCPRemove, NEOCPUpdate

NEOCP_URL = "https://www.minorplanetcenter.net/Extended_Files/neocp.json"
USER_AGENT = f"heimdall-neo/{__version__} (tstjean@umd.edu)"
TIMEOUT = 30
REFRESH_SECONDS = 60
TRACK_COLUMNS = (NEOCPCol.SCORE, NEOCPCol.NOTE, NEOCPCol.N_OBS, NEOCPCol.ARC)

_KEY = NEOCPCol.TEMP_DESIG

ColChanges = dict[NEOCPCol, tuple[Any, Any]]


def _keys_only_in(a: pl.DataFrame, b: pl.DataFrame) -> pl.Series:
    """Temp designations in `a` but not in `b`."""
    return a.join(b, on=_KEY, how="anti")[_KEY]


def _rowwise_diff(
    old: pl.DataFrame, new: pl.DataFrame, cols: Sequence[NEOCPCol]
) -> dict[str, ColChanges]:
    """For each NEO in both tables, get diffs for tracked columns"""
    joined = (
        old.select(_KEY, *cols)
        .join(new.select(_KEY, *cols), on=_KEY, how="inner", suffix="_new")
        .with_columns([pl.col(c).ne_missing(pl.col(f"{c}_new")).alias(f"{c}_chg") for c in cols])
        .filter(pl.any_horizontal([f"{c}_chg" for c in cols]))
    )
    return {
        row[_KEY]: {c: (row[c], row[f"{c}_new"]) for c in cols if row[f"{c}_chg"]}
        for row in joined.iter_rows(named=True)
    }


def _diff(
    old: pl.DataFrame, new: pl.DataFrame, cols: Sequence[NEOCPCol]
) -> list[NEOCPDiff]:
    now = datetime.now(UTC)
    return [
        *(NEOCPAdd(d, time=now) for d in _keys_only_in(new, old)),
        *(NEOCPRemove(d, time=now) for d in _keys_only_in(old, new)),
        *(NEOCPUpdate(d, c, time=now) for d, c in _rowwise_diff(old, new, cols).items()),
    ]


class NEOCPService:
    def __init__(self) -> None:
        self._neocp: NEOCPSnapshot | None = None
        self._diffs: list[NEOCPDiff] = []
        self._lock = Lock()

    @staticmethod
    def _fetch_remote() -> list[dict[str, Any]]:
        r = requests.get(NEOCP_URL, timeout=TIMEOUT, headers={"User-Agent": USER_AGENT})
        r.raise_for_status()
        return r.json()

    def _refresh(self) -> NEOCPSnapshot:
        with self._lock:
            if self._neocp is not None and time.time() - self._neocp.timestamp < REFRESH_SECONDS:
                return self._neocp

            snapshot = NEOCPSnapshot.from_json(self._fetch_remote())
            if self._neocp is not None:
                self._diffs = _diff(self._neocp.table, snapshot.table, TRACK_COLUMNS) + self._diffs

            self._neocp = snapshot
        return snapshot

    def get(self) -> tuple[NEOCPSnapshot, list[NEOCPDiff]]:
        return self._refresh(), self._diffs