#!/usr/bin/env bash
set -euo pipefail
LOG="/home/tian/fertility_popEVE/data/joint_test_real/merge_30.log"
exec > >(tee -a "$LOG") 2>&1

echo "[$(date)] Starting GLnexus merge for 30 samples"

# Use the already-validated include list
LIST="/home/tian/fertility_popEVE/data/joint_test_real/cohort_30.vcf.included_gvcfs.list"
OUT="/home/tian/fertility_popEVE/data/joint_test_real/cohort_30.vcf.gz"
WS="/home/tian/fertility_popEVE/data/joint_test_real/glnexus_workspace"
TMP="${OUT}.tmp"

rm -rf "$WS"

# Source clitools
eval "$(conda shell.bash hook)"
conda activate clitools

echo "[$(date)] Running GLnexus..."
glnexus_cli \
    --threads 8 \
    --config DeepVariantWGS \
    --dir "$WS" \
    --list "$LIST" \
    | bcftools view --threads 4 -Oz -o "$TMP" -

mv "$TMP" "$OUT"
bcftools index --threads 4 -t "$OUT"

echo "[$(date)] Done!"
ls -lh "$OUT" "$OUT.tbi"
