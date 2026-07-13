with open("data/annotation/joint_chr22.vep.vcf") as f:
    for line in f:
        if line.startswith("##INFO=<ID=CSQ"):
            print(line.strip())
            break
