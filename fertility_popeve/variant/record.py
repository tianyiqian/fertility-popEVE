from dataclasses import dataclass


@dataclass
class VariantRecord:
    sample: str
    chrom: str
    pos: int

    ref: str
    alt: str

    gene: str | None = None
    consequence: str | None = None

    af: float | None = None

    popeve: float | None = None
    burden: float | None = None
