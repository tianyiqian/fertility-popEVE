from __future__ import annotations

import gzip
import re
from pathlib import Path

import pandas as pd


MUTANT_PATTERN = re.compile(r"^([A-Z*])(\d+)([A-Z*])$")
SCORE_COLUMNS = {"EVE", "ESM1v"}


def _normalise_chromosome(value) -> str:
    return str(value).removeprefix("chr")


def _variant_key(chrom, pos, ref, alt) -> tuple[str, int, str, str]:
    return (_normalise_chromosome(chrom), int(pos), str(ref), str(alt))


def _parse_info(raw_info: str) -> dict[str, str]:
    return {
        key: value
        for item in raw_info.split(";")
        if "=" in item
        for key, value in [item.split("=", 1)]
    }


def _load_observed_keys(observed_file: Path) -> tuple[set[tuple[str, int, str, str]], set[str]]:
    observed = pd.read_parquet(observed_file)
    required = {"chrom", "pos", "ref", "alt", "protein_id"}
    missing = required.difference(observed.columns)
    if missing:
        raise ValueError(f"Observed-variant file is missing columns: {sorted(missing)}")

    keys = {
        _variant_key(row.chrom, row.pos, row.ref, row.alt)
        for row in observed[["chrom", "pos", "ref", "alt"]].itertuples(index=False)
    }
    proteins = set(observed["protein_id"].dropna().astype(str))
    return keys, proteins


def build_gp_candidate_space(
    popeve_vcf,
    protein_mapping_file,
    observed_file,
    output_file,
    score_columns=None,
):
    """Build a cohort-labelled, protein-level candidate space for popEVE GP training.

    Extracts all available evo-model scores (EVE, ESM1v, etc.) from the popEVE VCF
    so that separate GPs can be trained per model and ensembled.
    """
    if score_columns is None:
        score_columns = list(SCORE_COLUMNS)
    score_columns = [c for c in score_columns if c in SCORE_COLUMNS]
    if not score_columns:
        raise ValueError("At least one score column (EVE, ESM1v) must be specified.")

    popeve_vcf = Path(popeve_vcf)
    protein_mapping_file = Path(protein_mapping_file)
    observed_file = Path(observed_file)
    output_file = Path(output_file)

    observed_keys, observed_proteins = _load_observed_keys(observed_file)
    mapping = pd.read_parquet(protein_mapping_file)
    required_mapping = {"protein_id", "refseq_id", "status"}
    missing_mapping = required_mapping.difference(mapping.columns)
    if missing_mapping:
        raise ValueError(f"Protein mapping is missing columns: {sorted(missing_mapping)}")

    mapping = mapping[
        mapping["status"].eq("ok") & mapping["protein_id"].isin(observed_proteins)
    ].drop_duplicates("refseq_id")
    refseq_to_protein = dict(zip(mapping["refseq_id"], mapping["protein_id"]))
    if not refseq_to_protein:
        raise ValueError("No observed proteins have an approved RefSeq mapping.")

    records = []
    opener = gzip.open if popeve_vcf.suffix == ".gz" else open
    with opener(popeve_vcf, "rt") as handle:
        for line in handle:
            if line.startswith("#"):
                continue
            fields = line.rstrip("\n").split("\t")
            if len(fields) < 8:
                continue
            chrom, pos, _, ref, alt, _, _, raw_info = fields[:8]
            info = _parse_info(raw_info)
            refseq_id = info.get("protein")
            mutant = info.get("mutant")
            if refseq_id not in refseq_to_protein or not mutant:
                continue
            missing = [c for c in score_columns if c not in info]
            if missing:
                continue
            match = MUTANT_PATTERN.match(mutant)
            if not match:
                continue
            try:
                scores = {col: float(info[col]) for col in score_columns}
            except ValueError:
                continue
            ref_aa, position, alt_aa = match.groups()
            record = {
                "protein_id": refseq_to_protein[refseq_id],
                "refseq_id": refseq_id,
                "mutant": mutant,
                "position": int(position),
                "ref_aa": ref_aa,
                "alt_aa": alt_aa,
                "cohort_observed": _variant_key(chrom, pos, ref, alt) in observed_keys,
            }
            record.update({f"{col.lower()}_score": scores[col] for col in score_columns})
            records.append(record)

    if not records:
        raise ValueError("No scored popEVE candidates matched the observed cohort proteins.")

    candidates = pd.DataFrame(records)
    group_cols = ["protein_id", "refseq_id", "mutant", "position", "ref_aa", "alt_aa"]
    score_cols = [f"{c.lower()}_score" for c in score_columns]
    agg_kwargs = {col: (col, "first") for col in score_cols}
    agg_kwargs["cohort_observed"] = ("cohort_observed", "max")
    agg_kwargs["genomic_encoding_count"] = ("mutant", "size")
    candidates = (
        candidates.groupby(group_cols, as_index=False)
        .agg(**agg_kwargs)
        .sort_values(["protein_id", "position", "mutant"])
        .reset_index(drop=True)
    )
    candidates["cohort_observed"] = candidates["cohort_observed"].astype(int)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    candidates.to_parquet(output_file, index=False)
    return candidates
