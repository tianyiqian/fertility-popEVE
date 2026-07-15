# fertility-popEVE Project Status

Last Updated: 2026-07-15

## Current Version

v0.3

Latest Commit:

77ba003 add config driven training pipeline

---

## Project Goal

Adapt the Harvard popEVE framework for reproductive genetics, including:

- Infertility
- Recurrent pregnancy loss
- Embryo developmental arrest
- Oocyte maturation disorders

The long-term objective is to build a population-aware pathogenicity prediction framework for reproductive medicine.

---

## Completed Modules

- [x] Configuration-driven pipeline
- [x] VEP annotation
- [x] VariantRecord data model
- [x] Missense variant filtering
- [x] Protein mapping
- [x] Foundation feature extraction (popEVE)
- [x] Feature matrix generation
- [x] Genotype extraction
- [x] Training matrix generation
- [x] Unit tests

---

## Current Pipeline

VCF
↓
VEP
↓
VariantRecord
↓
Protein Mapping
↓
Foundation Features
↓
Feature Matrix
↓
Training Matrix

---

## Current Outputs

data/features/

- foundation_features.parquet
- feature_matrix.parquet
- training_matrix.parquet

---

## Next Milestone (v0.4)

GeneBurdenRD integration

Target outputs:

- gene_burden.parquet
- merged_training_matrix.parquet

---

## Future Roadmap

v0.4
- Gene burden features

v0.5
- Gaussian Process training

v0.6
- Fertility-specific model training

v1.0
- Complete fertility-popEVE pipeline

