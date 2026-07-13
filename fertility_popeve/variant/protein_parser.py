import re


AA3_TO_1 = {
    "Ala": "A", "Arg": "R", "Asn": "N", "Asp": "D",
    "Cys": "C", "Gln": "Q", "Glu": "E", "Gly": "G",
    "His": "H", "Ile": "I", "Leu": "L", "Lys": "K",
    "Met": "M", "Phe": "F", "Pro": "P", "Ser": "S",
    "Thr": "T", "Trp": "W", "Tyr": "Y", "Val": "V",
    "Ter": "*"
}


def parse_hgvsp(hgvsp):
    if not hgvsp:
        return None

    protein_id, protein_change = hgvsp.split(":")
    protein_id = protein_id.split(".")[0]

    m = re.match(r"p\.([A-Za-z]{3})(\d+)([A-Za-z]{3}|Ter)", protein_change)

    if m is None:
        return None

    ref3, pos, alt3 = m.groups()

    return {
        "protein_id": protein_id,
        "position": int(pos),
        "ref_aa": AA3_TO_1[ref3],
        "alt_aa": AA3_TO_1[alt3],
    }
