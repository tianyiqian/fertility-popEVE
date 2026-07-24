import gzip

import pandas as pd

from fertility_popeve.gp.candidate_space import build_gp_candidate_space


def test_builds_deduplicated_cohort_candidate_space(tmp_path):
    observed = tmp_path / "observed.parquet"
    pd.DataFrame(
        {
            "chrom": ["chr1"], "pos": [101], "ref": ["A"], "alt": ["C"],
            "protein_id": ["ENSP1"],
        }
    ).to_parquet(observed)

    mapping = tmp_path / "mapping.parquet"
    pd.DataFrame(
        {"protein_id": ["ENSP1"], "refseq_id": ["NP_1.1"], "status": ["ok"]}
    ).to_parquet(mapping)

    source = tmp_path / "scores.vcf.gz"
    with gzip.open(source, "wt") as handle:
        handle.write("#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\n")
        handle.write("1\t101\t.\tA\tC\t.\t.\tprotein=NP_1.1;mutant=A10V;EVE=1.5;ESM1v=-0.5\n")
        handle.write("1\t102\t.\tG\tT\t.\t.\tprotein=NP_1.1;mutant=A10V;EVE=1.5;ESM1v=-0.5\n")
        handle.write("1\t103\t.\tC\tA\t.\t.\tprotein=NP_1.1;mutant=G11D;EVE=2.5;ESM1v=0.8\n")
        handle.write("1\t104\t.\tC\tA\t.\t.\tprotein=NP_2.1;mutant=G11D;EVE=2.5;ESM1v=0.8\n")

    result = build_gp_candidate_space(source, mapping, observed, tmp_path / "candidates.parquet")

    assert list(result["mutant"]) == ["A10V", "G11D"]
    assert list(result["cohort_observed"]) == [1, 0]
    assert list(result["genomic_encoding_count"]) == [2, 1]
    assert "eve_score" in result.columns
    assert "esm1v_score" in result.columns
    assert list(result["eve_score"]) == [1.5, 2.5]
    assert list(result["esm1v_score"]) == [-0.5, 0.8]
