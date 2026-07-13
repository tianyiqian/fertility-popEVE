#!/usr/bin/env python3
"""
Build ENSP -> RefSeq protein mapping.

Input:
    data/protein/protein_table.parquet

Output:
    data/reference/mapping/protein_mapping.parquet
"""

import time
from pathlib import Path

import pandas as pd
import requests

from fertility_popeve.utils.config import load_config


HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
}


def query_refseq(protein_id: str, retry: int = 3):
    """
    Query RefSeq peptide ID from Ensembl xrefs.
    """

    url = f"https://rest.ensembl.org/xrefs/id/{protein_id}"

    for attempt in range(retry):

        try:
            response = requests.get(
                url,
                headers=HEADERS,
                timeout=30,
            )

            if response.status_code != 200:
                time.sleep(1)
                continue

            for item in response.json():

                if item.get("dbname") == "RefSeq_peptide":
                    return item.get("display_id")

            return None

        except requests.RequestException:

            time.sleep(1)

    return None


def main():

    cfg = load_config()

    protein_table = (
        Path(cfg["paths"]["protein"])
        / "protein_table.parquet"
    )

    output_table = Path(
        cfg["files"]["protein_mapping"]
    )

    output_table.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    print("=" * 60)
    print("Loading protein table")
    print("=" * 60)

    df = pd.read_parquet(protein_table)

    proteins = (
        df["protein_id"]
        .dropna()
        .drop_duplicates()
        .tolist()
    )

    print(f"Total proteins: {len(proteins)}")

    records = []

    success = 0

    for idx, protein in enumerate(proteins, start=1):

        print(f"[{idx:3d}/{len(proteins)}] {protein}")

        refseq = query_refseq(protein)

        status = "ok" if refseq else "failed"

        if refseq:
            success += 1

        records.append(
            {
                "protein_id": protein,
                "refseq_id": refseq,
                "status": status,
            }
        )

        time.sleep(0.2)

    mapping = pd.DataFrame(records)

    mapping.to_parquet(
        output_table,
        index=False,
    )

    print()
    print("=" * 60)
    print("Finished")
    print("=" * 60)
    print(f"Success : {success}")
    print(f"Failed  : {len(proteins)-success}")
    print(f"Saved   : {output_table}")


if __name__ == "__main__":
    main()
