import subprocess

VCF = "models/popeve_data/grch38_popEVE_ukbb_20250715.vcf.gz"


def annotate(chrom, pos, ref, alt):

    region = f"{chrom}:{pos}-{pos}"

    result = subprocess.run(
        [
            "tabix",
            VCF,
            region,
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        return {"found": False}

    for line in result.stdout.splitlines():

        fields = line.split("\t")

        if len(fields) < 8:
            continue

        if fields[3] != ref:
            continue

        if fields[4] != alt:
            continue

        info = {}

        for item in fields[7].split(";"):

            if "=" not in item:
                continue

            k, v = item.split("=", 1)

            info[k] = v

        info["found"] = True

        return info

    return {"found": False}
