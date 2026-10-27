# Copyright 2026 Taylor St Jean

from typing import Any, Self
from datetime import datetime, timezone, UTC
from dataclasses import dataclass

import polars as pl

from .col import NEOCPCol

# neocp.json keys that map directly onto a column
_JSON_RENAME = {
    "Temp_Desig": NEOCPCol.TEMP_DESIG,
    "Score": NEOCPCol.SCORE,
    "R.A.": NEOCPCol.RA,
    "Decl.": NEOCPCol.DEC,
    "V": NEOCPCol.V,
    "Updated": NEOCPCol.UPDATED,
    "Note": NEOCPCol.NOTE,
    "NObs": NEOCPCol.N_OBS,
    "Arc": NEOCPCol.ARC,
    "H": NEOCPCol.H,
    "Not_Seen_dys": NEOCPCol.NOT_SEEN,
}

_DAY_MS = 86_400_000


@dataclass
class NEOCPSnapshot:
    table: pl.DataFrame
    timestamp: float

    def __repr__(self) -> str:
        return repr(self.table)

    @classmethod
    def from_json(cls, data: list[dict[str, Any]]) -> Self:
        # scan every entry for keys, otherwise a note that first appears past
        # the first 100 entries might get dropped
        df = pl.DataFrame(data, infer_schema_length=None)

        # discovery comes split into year, month and fractional day
        day = pl.col("Discovery_day").cast(pl.Float64)
        whole_day = day.floor()
        df = df.with_columns(
            (
                pl.datetime(pl.col("Discovery_year"), pl.col("Discovery_month"), whole_day.cast(pl.Int64))
                + pl.duration(milliseconds=((day - whole_day) * _DAY_MS).round().cast(pl.Int64))
            ).alias(NEOCPCol.DISCOVERY)
        )

        # note is only included on entries that have one, so it may be missing entirely
        # add it back in as an empty col if so
        if "Note" not in df.columns:
            df = df.with_columns(pl.lit(None, dtype=pl.String).alias(NEOCPCol.NOTE))

        # rename to our columns, drop the split discovery fields, and put columns in enum order
        df = df.rename(_JSON_RENAME).select(list(NEOCPCol))

        # normalize updated column to a datetime
        now = datetime.now(timezone.utc).replace(tzinfo=None)

        # this should handle removing the Added/Updated,
        # and grouping the variable formatted months and the fractional days
        # claude made this fancy extraction
        p = pl.col(NEOCPCol.UPDATED).str.extract_groups(
            r"(?P<mon>[A-Za-z]{3})[a-z]*\.? (?P<day>\d+)(?P<frac>\.\d+)?"
        )

        # we assume year is current year
        date = pl.concat_str(
            pl.lit(str(now.year)), p.struct.field("mon"), p.struct.field("day"), separator=" "
        ).str.to_date("%Y %b %d")

        # add in day fraction to date
        frac_ms = (p.struct.field("frac").cast(pl.Float64) * _DAY_MS).round().cast(pl.Int64)
        updated = date.cast(pl.Datetime) + pl.duration(milliseconds=frac_ms)

        # if a date would land at a time that has not occurred yet, assume one year back
        # this is to handle year rollovers (for example, loading data in early january)
        df = df.with_columns(
            pl.when(updated > now).then(updated.dt.offset_by("-1y")).otherwise(updated).alias(NEOCPCol.UPDATED)
        )

        # json numbers can come through as int or float, so cast explicitly
        df = df.with_columns(
            pl.col(NEOCPCol.float_cols()).cast(pl.Float64),
            pl.col(NEOCPCol.int_cols()).cast(pl.Int64),
        )

        # V = 99.9 is a placeholder for no magnitude
        # also convert empty note to null
        df = df.with_columns(
            pl.col("V").replace(99.9, None),
            pl.col("Note").replace("", None)
        )

        return cls(df, timestamp=datetime.now(UTC).timestamp())