# fertility-popEVE Project Status

Last Updated: 2026-07-15

---

# Current Version

v0.5

Latest Commit:

f5b2a62 organize generated output ignores

---

# Project Goal

Adapt the Harvard popEVE framework for reproductive genetics.

Target applications:

- Infertility
- Recurrent pregnancy loss
- Embryo developmental arrest
- Oocyte maturation disorders

Long-term goal:

Build a population-aware pathogenicity prediction framework for reproductive medicine.

---

# Current Architecture

The project contains three major data layers.

## Variant-level data

Source:

Joint multi-sample VCF

Representation:

sample × variant

Current output:

data/features/training_matrix.parquet

Purpose:

- popEVE feature modeling
- GP training
- downstream machine learning


## Patient-level data

Source:

data/phenotype/phenotype.csv

Representation:

one row per patient/sample

Purpose:

- clinical phenotype definition
- GeneBurdenRD case-control labels
- future clinical modeling


## Gene-level burden analysis

Input:

- Exomiser-compatible master TSV
- phenotype labels

Purpose:

- gene burden testing
- association analysis

---

# Completed Modules

- [x] Configuration-driven pipeline
- [x] VEP annotation
- [x] VariantRecord data model
- [x] Missense variant filtering
- [x] Protein mapping
- [x] Foundation feature extraction (popEVE)
- [x] Feature matrix generation
- [x] Genotype extraction
- [x] Training matrix generation
- [x] GeneBurdenRD master TSV export
- [x] GeneBurdenRD phenotype label export
- [x] Phenotype validation
- [x] Unit tests

---

# Current Pipeline

## Variant pipeline

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


## GeneBurdenRD phenotype pipeline

phenotype.csv
↓
Phenotype Exporter
↓
analysisLabelList.tsv
EA.tsv
NF.tsv
GV.tsv
MI.tsv


## Gene burden pipeline

Training matrix
↓
Exomiser master TSV
↓
GeneBurdenRD analysis

---

# Current Outputs

## Feature outputs

data/features/

- foundation_features.parquet
- feature_matrix.parquet
- training_matrix.parquet


## GeneBurdenRD outputs

Generated files:

data/geneBurdenRD/

- analysisLabelList.tsv
- EA.tsv
- NF.tsv
- GV.tsv
- MI.tsv

---

# Development Principles

1. Variant-level and patient-level data remain separated.

2. phenotype.csv is the canonical patient metadata source.

3. Do not reconstruct patient phenotype from training_matrix.parquet.

4. Business logic belongs under:

fertility_popeve/

5. CLI scripts remain thin wrappers.

6. When information is uncertain:

- verify data/code first
- distinguish confirmed facts from inference
- avoid assumptions

---

# Next Milestone

## v0.6

Gaussian Process retraining.

Goals:

- adapt popEVE GP framework
- define fertility-specific labels
- construct GP training dataset

---

# Future Roadmap

v0.6
- Gaussian Process training

v0.7
- Fertility-specific model training

v1.0
- Complete fertility-popEVE pipeline
