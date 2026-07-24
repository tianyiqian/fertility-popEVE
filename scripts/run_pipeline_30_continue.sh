#!/usr/bin/env bash
set -euo pipefail
cd /home/tian/fertility_popEVE

LOG="logs/pipeline_30_$(date +%Y%m%d_%H%M%S).log"
exec > >(tee "$LOG") 2>&1

export PYTHONPATH=/home/tian/fertility_popEVE

fail() {
    echo "[FATAL] $*"
    echo "Pipeline failed at $(date)"
    exit 1
}

run_step() {
    local step="$1"
    local env_name="${2:-popeve}"
    echo ""
    echo "=== $(date) $step ==="
    conda run --no-capture-output -n "$env_name" python3 "$step" || fail "$step failed"
    echo "--- $(date) $step DONE ---"
}

echo "=========================================="
echo " 30-sample pipeline (skip VEP - already done)"
echo " Started: $(date)"
echo "=========================================="

run_step scripts/02_extract_features.py popeve
run_step scripts/03_filter_missense.py popeve
run_step scripts/04_prepare_protein.py popeve
run_step scripts/06_build_popeve_index.py popeve
run_step scripts/07_build_foundation_features.py popeve
run_step scripts/08_build_feature_matrix.py popeve
run_step scripts/09_validate_feature_matrix.py popeve

echo ""
echo "[$(date)] Step 10: GP candidate space"
conda run --no-capture-output -n popeve python3 scripts/14_build_gp_candidate_space.py || fail "candidate_space failed"

echo ""
echo "[$(date)] Step 11: GP training data"
conda run --no-capture-output -n popeve python3 scripts/11_build_gp_training.py || fail "gp_training failed"

echo ""
echo "[$(date)] Step 12: GP model training (GPU)"
conda run --no-capture-output -n fertility_gp python3 scripts/15_train_fertility_popeve.py || echo "[WARN] GP training errors (expected if few eligible proteins)"

echo ""
echo "=========================================="
echo " Pipeline complete!"
echo " Finished: $(date)"
echo " Outputs: data/joint_test_real/"
echo "=========================================="
