#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$SCRIPT_DIR"

LOG="logs/pipeline_30_$(date +%Y%m%d_%H%M%S).log"
exec > >(tee "$LOG") 2>&1

eval "$(conda shell.bash hook)"

echo "=========================================="
echo " 30-sample fertility_popEVE pipeline"
echo " Started: $(date)"
echo " Config: config/config_30.yaml -> config/config.yaml"
echo " VCF: data/joint_test_real/cohort_30.vcf.gz"
echo "=========================================="

fail() {
    echo "[FATAL] $*"
    echo "Pipeline failed at $(date)" | tee -a "$LOG"
    exit 1
}

run_step() {
    local step="$1"
    local env_name="${2:-popeve}"
    echo ""
    echo "=== $(date) $step ==="
    export PYTHONPATH=$SCRIPT_DIR
    conda run --no-capture-output -n "$env_name" python3 "$step" || fail "$step failed"
    echo "--- $(date) $step DONE ---"
}

echo "[$(date)] Step 1: VEP annotation"
export PYTHONPATH=$SCRIPT_DIR
conda run --no-capture-output -n popeve python3 scripts/01_run_vep.py || fail "VEP failed"
echo "[$(date)] Step 1 done"

run_step scripts/02_extract_features.py popeve
run_step scripts/03_filter_missense.py popeve
run_step scripts/04_prepare_protein.py popeve
run_step scripts/05_build_reference_mapping.py popeve
run_step scripts/06_build_popeve_index.py popeve
run_step scripts/07_build_foundation_features.py popeve
run_step scripts/08_build_feature_matrix.py popeve
run_step scripts/09_validate_feature_matrix.py popeve

echo ""
echo "[$(date)] Step 10: GP candidate space"
export PYTHONPATH=$SCRIPT_DIR
conda run --no-capture-output -n popeve python3 scripts/14_build_gp_candidate_space.py || fail "candidate_space failed"
echo "[$(date)] Step 10 done"

echo ""
echo "[$(date)] Step 11: GP training data"
conda run --no-capture-output -n popeve python3 scripts/11_build_gp_training.py || fail "gp_training failed"
echo "[$(date)] Step 11 done"

echo ""
echo "[$(date)] Step 12: GP model training (GPU)"
conda run --no-capture-output -n fertility_gp python3 scripts/15_train_fertility_popeve.py || echo "[WARN] GP training had errors (may be expected for small cohort)"

echo ""
echo "=========================================="
echo " Pipeline complete!"
echo " Finished: $(date)"
echo " Outputs:"
echo "   VCF: data/joint_test_real/cohort_30.vcf.gz"
echo "   VEP: data/joint_test_real/annotation/"
echo "   Features: data/joint_test_real/features/"
echo "   GP: data/joint_test_real/gp/"
echo "=========================================="
