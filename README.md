# fertility-popEVE

A population-aware evolutionary model for reproductive genomics.

fertility-popEVE adapts the popEVE framework to reproductive medicine by integrating population-aware evolutionary scores, protein foundation models, clinical phenotype labels, gene burden analysis and Gaussian Process calibration for infertility-related genomic analysis.

## Project Status

Current version: v0.7

fertility-popEVE has completed the full feature extraction pipeline, phenotype integration, gene burden analysis, GP training pipeline, and real cohort preparation.

Completed modules:

- VCF processing pipeline ✅
- VEP annotation pipeline ✅
- Missense variant filtering ✅
- Protein sequence preparation ✅
- Protein ID mapping ✅
- popEVE feature extraction ✅
- EVE / ESM1v feature integration ✅
- Variant feature matrix construction ✅
- Reproductive phenotype integration ✅
- Sample ID and proband gVCF mapping ✅
- Gene burden analysis ✅
- Exomiser master export ✅
- GP training data builder ✅
- GP candidate space construction ✅
- GP model training ✅
- Memory watchdog daemon ✅
- Full-cohort preparation pipeline ✅
- Pipeline orchestration & checkpointing ✅

Current development:

- Large-scale real cohort joint calling 🚧
- Fertility-specific model evaluation & tuning 🚧
- Clinical phenotype analysis 🚧

## Pipeline Overview

The pipeline is orchestrated via `run_pipeline.py` with step definitions in `config/pipeline.yaml`. Steps:

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

Memory watchdog (`scripts/00_watchdog.py`) automatically monitors and kills heavy subprocesses when available memory drops below 200 GB.

## Project Structure

```
fertility_popEVE/
├── fertility_popeve/         # Core library
│   ├── annotation/           # VEP annotation & feature extraction
│   ├── burden/               # Gene burden analysis & phenotype export
│   ├── embedding/            # Embedding layer
│   ├── eve/                  # EVE model interface
│   ├── features/             # Feature merge, training, popEVE
│   ├── gp/                   # Gaussian Process (builder, model, trainer)
│   ├── pipeline/             # Pipeline orchestration
│   ├── providers/            # popEVE data provider
│   ├── reference/            # Reference DB, ID mapping, cache
│   ├── utils/                # Config, logging, memory, checkpoint, shell
│   └── validation/           # Validation utilities
├── scripts/                  # Pipeline step scripts (00-16)
├── tests/                    # Unit & integration tests
├── config/                   # YAML configs (pipeline, model, cohort)
├── environment/              # Conda environment files
├── data/                     # Runtime data (gitignored)
├── models/                   # Model artifacts (gitignored)
├── outputs/                  # Pipeline outputs (gitignored)
└── run_pipeline.py           # Main pipeline runner
```
