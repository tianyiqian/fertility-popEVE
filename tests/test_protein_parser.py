import pytest
from fertility_popeve.variant.protein_parser import parse_hgvsp


@pytest.mark.parametrize(
    "hgvsp,expected_protein,expected_pos,expected_ref,expected_alt",
    [
        ("ENSP00000495403.1:p.Val78Ala", "ENSP00000495403", 78, "V", "A"),
        ("ENSP00000340610.6:p.Ser12Phe", "ENSP00000340610", 12, "S", "F"),
        ("ENSP00000331704.5:p.Pro232Leu", "ENSP00000331704", 232, "P", "L"),
    ],
)
def test_parse_hgvsp(hgvsp, expected_protein, expected_pos, expected_ref, expected_alt):
    result = parse_hgvsp(hgvsp)
    assert result["protein_id"] == expected_protein
    assert result["position"] == expected_pos
    assert result["ref_aa"] == expected_ref
    assert result["alt_aa"] == expected_alt


def test_parse_hgvsp_returns_dict():
    result = parse_hgvsp("ENSP00000495403.1:p.Val78Ala")
    assert isinstance(result, dict)
    assert set(result.keys()) == {"protein_id", "position", "ref_aa", "alt_aa"}


def test_parse_hgvsp_returns_none_for_empty():
    assert parse_hgvsp("") is None
    assert parse_hgvsp(None) is None


def test_parse_hgvsp_three_to_one_letter():
    result = parse_hgvsp("ENSP00000495403.1:p.Val78Ala")
    assert result["ref_aa"] == "V"
    assert result["alt_aa"] == "A"
