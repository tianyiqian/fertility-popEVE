# fertility-popEVE

Population-aware evolutionary model for reproductive genomics — adapts the
[popEVE](https://github.com/debbiemarkslab/popEVE) framework (Marks Lab,
Harvard) to reproductive medicine.

**Paper reference**: Orenbuch et al. "Deep generative modeling of the human
proteome reveals over a hundred novel genes involved in rare genetic
disorders." medRxiv, 2023.

## Status

Current version: **v0.8.1**

The data pipeline (VEP → feature matrix) and Gaussian Process training are
functional.  The module list below distinguishes what is implemented from
what is planned.

## What Works

| Component | Status |
|-----------|--------|
| VCF processing pipeline | Done |
| VEP annotation | Done |
| Missense variant filtering | Done |
| Protein sequence preparation | Done |
| Protein ID mapping (Ensembl → RefSeq) | Done |
| popEVE feature extraction (VCF tabix query) | Done |
| Variant feature matrix construction | Done |
| Reproductive phenotype integration | Done |
| Proband gVCF mapping | Done |
| Gene burden analysis (GeneBurdenRD export) | Done |
| GP training data builder | Done |
| GP candidate space construction | Done |
| GP model training (per-protein, EVE+ESM1v ensemble) | Done |
| Memory watchdog daemon | Done |
| Pipeline orchestration & checkpointing | Done |

## In Progress / Planned

| Component | Status |
|-----------|--------|
| EVE model inference (local) | Planned — currently reads precomputed scores |
| Protein embedding layer | Planned |
| Full-cohort joint calling at scale | In progress |
| Fertility-specific model evaluation & benchmarking | In progress |
| Clinical phenotype association analysis | In progress |
| Web interface / API | Not started |

## Pipeline

The pipeline has 16 steps orchestrated via `config/pipeline.yaml`:

| Step | Script | Description |
|------|--------|-------------|
| 01 | `01_run_vep.py` | VEP annotation |
| 02 | `02_extract_features.py` | VCF feature extraction |
| 03 | `03_filter_missense.py` | Missense variant filtering |
| 04 | `04_prepare_protein.py` | Protein sequence preparation |
| 05 | `05_build_reference_mapping.py` | Reference ID mapping |
| 06 | `06_build_popeve_index.py` | popEVE index construction |
| 07 | `07_build_foundation_features.py` | EVE/ESM1v feature extraction |
| 08 | `08_build_feature_matrix.py` | Feature matrix assembly |
| 09 | `09_validate_feature_matrix.py` | Matrix validation |
| 10 | `10_export_analysis_labels.py` | Phenotype label export |
| 11 | `11_build_gp_training.py` | GP training data builder |
| 12 | `12_prepare_phenotype.py` | Phenotype data preparation |
| 13 | `13_build_vcf_mapping.py` | Proband gVCF mapping |
| 14 | `14_build_gp_candidate_space.py` | GP candidate space |
| 15 | `15_train_fertility_popeve.py` | GP model training |
| 16 | `16_prepare_full_cohort.py` | Full cohort preparation |

Memory watchdog (`scripts/00_watchdog.py`) monitors system memory during
training and terminates subprocesses when available RAM drops below the
configured danger threshold.

## Quick Start

```bash
# 1. Create conda environments
conda env create -f environment/fertility_popeve.yml
conda env create -f environment/fertility_gp.yml

# 2. Run full pipeline
python run_pipeline.py

# 3. GP training (separate env for torch/gpytorch)
conda run -n fertility_gp python scripts/15_train_fertility_popeve.py
```

## Configuration

Edit `config/config.yaml` to set paths and thresholds.  Key sections:

- `paths` — data directories, reference genome, BED files
- `gp_training` — epochs, admission criteria, checkpoint intervals
- `memory` — watchdog thresholds

## GP Training Alignment

The GP trainer is aligned with the official
[debbiemarkslab/popEVE](https://github.com/debbiemarkslab/popEVE) training
methodology:

- Per-protein GP calibration using Pólya-Gamma likelihood
- RBF kernel with Natural Variational Distribution
- 6,000 training epochs with checkpoints every 1,000
- Output directories: `states/`, `scores/`, `losses_and_lengthscales/`
- Ensemble scoring: EVE + ESM1v posterior means averaged
- Multi-GPU parallel training via subprocess pool

## Project Structure

```
fertility_popEVE/
├── fertility_popeve/         # Core library
│   ├── annotation/           # VEP annotation & feature extraction
│   ├── burden/               # Gene burden analysis & phenotype export
│   ├── features/             # Feature merge, training, popEVE queries
│   ├── gp/                   # Gaussian Process (model, trainer, builder, candidates)
│   ├── reference/            # Reference database
│   ├── utils/                # Config, logging, memory
│   ├── variant/              # Variant records, protein parsing, genotypes
│   └── providers/            # Data provider stubs
├── scripts/                  # Pipeline step scripts (00–16)
├── tests/                    # Unit & integration tests (57 tests)
├── config/                   # YAML configs (pipeline, model, cohort)
├── environment/              # Conda environment files
├── data/                     # Runtime data (gitignored)
├── models/                   # Model artifacts (gitignored)
├── outputs/                  # Pipeline outputs (gitignored)
└── run_pipeline.py           # Main pipeline runner
```

## Target Applications

Infertility · Recurrent pregnancy loss · Embryo developmental arrest ·
Oocyte maturation disorders

## License

MIT — see [upstream](https://github.com/debbiemarkslab/popEVE) for popEVE's
original license.
