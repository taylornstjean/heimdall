# Copyright 2026 Taylor St Jean

from __future__ import annotations

from enum import StrEnum


class NEOCPCol(StrEnum):
    TEMP_DESIG  = "TempDesig"
    SCORE       = "Score"
    DISCOVERY   = "Discovery"
    RA          = "RA"
    DEC         = "Dec"
    V           = "V"
    UPDATED     = "Updated"
    NOTE        = "Note"
    N_OBS       = "NObs"
    ARC         = "Arc"
    H           = "H"
    NOT_SEEN    = "NotSeen"

    @classmethod
    def float_cols(cls) -> list[NEOCPCol]:
        return [cls.RA, cls.DEC, cls.V, cls.H, cls.ARC, cls.NOT_SEEN]

    @classmethod
    def int_cols(cls) -> list[NEOCPCol]:
        return [cls.SCORE, cls.N_OBS]
