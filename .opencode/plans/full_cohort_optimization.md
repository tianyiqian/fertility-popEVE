# 全量队列执行 + 高性能优化计划

## 硬件
- CPU: 2× AMD EPYC 9755 (128C) = 256核
- RAM: 2.2 TB
- GPU: 6× RTX 5090 (每卡 32GB VRAM)
- NVMe: 7TB (/home)

---

## Phase 0: 系统准备 ✅ 已完成
- [x] jemalloc installed in clitools env
- [x] NVMe scratch dir: ~/tmp/glnexus_scratch

---

## Phase 1: 多GPU并行GP训练模块

### 修改 `fertility_popeve/gp/trainer.py`

在文件顶部新增 import:
```python
import subprocess
import sys
import itertools
from concurrent.futures import ThreadPoolExecutor, as_completed
```

### 新增函数 1: `_train_gp_subprocess`
```python
def _train_gp_subprocess(gpu_id, csv_path, output_dir, epochs, holdout_frac, seed):
    """Train a single GP model in a subprocess pinned to one GPU."""
    script = (
        f"import sys; sys.path.insert(0, '.'); "
        f"from fertility_popeve.gp.trainer import train_protein_gp; "
        f"train_protein_gp(r'{csv_path}', r'{output_dir}', "
        f"epochs={epochs}, holdout_frac={holdout_frac}, seed={seed})"
    )
    env = {**__import__('os').environ, "CUDA_VISIBLE_DEVICES": str(gpu_id)}
    subprocess.run([sys.executable, "-c", script], env=env, check=True,
                   capture_output=True, text=True)
```

### 新增函数 2: `compute_ensemble_scores`
```python
def compute_ensemble_scores(protein_id, model_names, output_dir):
    """Ensemble trained GP scores by averaging posterior means."""
    output_dir = Path(output_dir)
    ensemble_means = []
    ensemble_lowers = []
    ensemble_uppers = []

    for model_name in model_names:
        scores_path = output_dir / f"{protein_id}_{model_name}_scores.csv"
        if not scores_path.exists():
            continue
        scores = pd.read_csv(scores_path)
        ensemble_means.append(scores["gp_mean_probability"].values)
        ensemble_lowers.append(scores["gp_lower"].values)
        ensemble_uppers.append(scores["gp_upper"].values)

    if not ensemble_means:
        return

    ref = pd.read_csv(output_dir / f"{protein_id}_{model_names[0]}_scores.csv")
    ensemble_df = ref[["mutant", "observed", "model_score"]].copy()
    ensemble_df["gp_mean_probability"] = np.mean(ensemble_means, axis=0)
    ensemble_df["gp_lower"] = np.min(ensemble_lowers, axis=0)
    ensemble_df["gp_upper"] = np.max(ensemble_uppers, axis=0)
    ensemble_df["n_models"] = len(model_names)
    ensemble_df.to_csv(output_dir / f"{protein_id}_ensemble_scores.csv", index=False)
    print(f"  [ENSEMBLE] {protein_id}: {len(model_names)} models, {len(ensemble_df)} variants")
```

### 新增函数 3: `train_eligible_proteins_multi_gpu`
```python
def train_eligible_proteins_multi_gpu(
    readiness_file,
    output_dir,
    epochs=6000,
    holdout_frac=0.2,
    gpu_ids=None,
    max_proteins=None,
):
    """Train GP models in parallel across multiple GPUs.

    Each protein's EVE + ESM1V models are trained on different GPUs,
    then ensembled after all individual GPs complete.
    """
    if gpu_ids is None:
        gpu_ids = list(range(torch.cuda.device_count()))
    elif isinstance(gpu_ids, int):
        gpu_ids = list(range(gpu_ids))

    readiness = pd.read_csv(readiness_file)
    eligible = readiness[readiness.eligible_for_training].sort_values("protein_id")
    if max_proteins is not None:
        eligible = eligible.head(max_proteins * len(gpu_ids))

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Build task list: one task per (protein_id, evo_model) pair
    tasks = []
    for row in eligible.itertuples(index=False):
        tasks.append({
            "protein_id": row.protein_id,
            "file_path": row.file_path,
            "evo_model": row.evo_model,
        })

    if not tasks:
        print("[INFO] No eligible proteins to train.")
        return []

    gpu_cycle = itertools.cycle(gpu_ids)
    trained_proteins = set()

    def _run_task(task):
        gpu_id = next(gpu_cycle)
        csv_path = Path(task["file_path"])
        out_dir = output_dir / "models"
        out_dir.mkdir(parents=True, exist_ok=True)
        _train_gp_subprocess(gpu_id, csv_path, out_dir, epochs, holdout_frac, seed=42)
        return task

    with ThreadPoolExecutor(max_workers=len(gpu_ids)) as pool:
        futures = [pool.submit(_run_task, t) for t in tasks]
        for f in as_completed(futures):
            result = f.result()
            trained_proteins.add(result["protein_id"])
            print(f"  [DONE] {result['protein_id']}_{result['evo_model']}")

    # Ensemble each protein after all models are trained
    models_dir = output_dir / "models"
    for protein_id in sorted(trained_proteins):
        subset = eligible[eligible.protein_id == protein_id]
        model_names = subset["evo_model"].tolist()
        compute_ensemble_scores(protein_id, model_names, models_dir)

    print(f"[INFO] Trained {len(trained_proteins)} proteins across {len(gpu_ids)} GPUs")
    return list(trained_proteins)
```

---

## Phase 2: 更新训练脚本

### 修改 `scripts/15_train_fertility_popeve.py`
- 检测可用 GPU 数量
- 调用 `train_eligible_proteins_multi_gpu` 而非 `train_eligible_proteins`
- 如果 GPU=0 则回退到 CPU 串行模式

```python
#!/usr/bin/env python3
from pathlib import Path
import sys
import torch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from fertility_popeve.gp.trainer import train_eligible_proteins_multi_gpu
from fertility_popeve.utils.config import load_config


def main():
    config = load_config()
    gp_dir = Path(config["paths"]["gp"])

    n_gpu = torch.cuda.device_count()
    print(f"[INFO] Detected {n_gpu} GPUs")

    trained = train_eligible_proteins_multi_gpu(
        gp_dir / "training" / "training_readiness.csv",
        gp_dir,
        epochs=config.get("gp_training", {}).get("epochs", 6000),
        holdout_frac=config.get("gp_training", {}).get("holdout_frac", 0.2),
        gpu_ids=list(range(n_gpu)) if n_gpu > 0 else None,
    )
    print(f"[INFO] Trained {len(trained)} proteins")


if __name__ == "__main__":
    main()
```

---

## Phase 3: 全量队列联合 calling

### 步骤 3.1: 生成 gVCF 路径清单
```bash
# 从 proband_gvcf_mapping_exact.csv 提取 vcf 路径
conda run -n popeve python3 -c "
import pandas as pd
df = pd.read_csv('data/cohort/proband_gvcf_mapping_exact.csv')
df['vcf'].to_csv('data/cohort/full_cohort_gvcfs.list', index=False, header=False)
print(f'gVCFs to merge: {len(df)}')
"
```

### 步骤 3.2: 运行 GLnexus 联合 calling（优化参数）
```bash
conda run -n clitools \
  LD_PRELOAD=libjemalloc.so \
  numactl --cpunodebind=0 --membind=0 \
  glnexus_cli \
    --threads 64 \
    --mem-gbytes 256 \
    --config DeepVariantWGS \
    --dir /home/tian/tmp/glnexus_scratch \
    --list data/cohort/full_cohort_gvcfs.list \
  | bcftools view --threads 16 -Oz -o data/joint_vcf/cohort_joint.vcf.gz -

bcftools index --threads 16 data/joint_vcf/cohort_joint.vcf.gz
```

### 预期输出
- `data/joint_vcf/cohort_joint.vcf.gz` (全外显子组, 2523 samples)
- `data/joint_vcf/cohort_joint.vcf.gz.tbi`

---

## Phase 4: 全量 pipeline 运行

### 步骤 4.1: 更新 `config/config.yaml`
```yaml
training:
  vcf: data/joint_vcf/cohort_joint.vcf.gz
  # ... 其余不变
```

### 步骤 4.2: 运行 VEP 注释（高并行）
```bash
# VEP 需要较多时间，推荐使用 --fork 96
conda run -n popeve python3 scripts/01_run_vep.py
```

### 步骤 4.3: 串联运行剩余 pipeline 步骤
```bash
for script in \
  scripts/02_extract_features.py \
  scripts/03_filter_missense.py \
  scripts/04_prepare_protein.py \
  scripts/07_build_foundation_features.py \
  scripts/08_build_feature_matrix.py \
  scripts/09_validate_feature_matrix.py; do
  conda run -n popeve python3 "$script"
done
```

### 步骤 4.4: GP 候选空间 + 训练数据
```bash
conda run -n popeve python3 scripts/14_build_gp_candidate_space.py
conda run -n popeve python3 scripts/11_build_gp_training.py
```

### 步骤 4.5: GPU 加速 GP 训练
```bash
conda run -n fertility_gp python3 scripts/15_train_fertility_popeve.py
```

---

## Phase 5: GitHub Release 更新

更新以下文件：
- `README.md` — 项目简介、架构图、使用方法
- `PROJECT_STATUS.md` — 更新到 v0.6
- 创建 GitHub Release tag v0.6

---

## 预期运行时间

| 阶段 | 串行估计 | 优化后估计 |
|------|---------|-----------|
| GLnexus joint calling | 3-8h | 1-3h (64线程+NVMe) |
| VEP annotation | 24-48h | 8-16h (fork 96) |
| Feature pipeline | 2-4h | 1-2h |
| **GP 训练** (≈2000蛋白) | **~170h** | **~28h** (6 GPU并行) |
