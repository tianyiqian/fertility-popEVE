# fertility-popEVE Project Status

Last Updated: 2026-07-24

Current Version: v0.8.1

---

## What Works (implemented and tested)

- VCF processing pipeline
- VEP annotation
- Missense variant filtering
- Protein sequence preparation
- Protein ID mapping (Ensembl REST API → RefSeq)
- popEVE feature extraction (tabix queries against Marks Lab precomputed VCF)
- Variant feature matrix construction
- Phenotype integration and GeneBurdenRD label export
- Proband gVCF mapping
- GP training data builder (with readiness assessment)
- GP candidate space construction
- Per-protein GP training (EVE + ESM1v ensemble, multi-GPU)
- Memory watchdog daemon
- Pipeline orchestration via run_pipeline.py

## In Progress

- Full-cohort joint calling at scale (2,572 probands)
- Fertility-specific model evaluation & benchmarking
- Clinical phenotype association analysis

## Not Yet Implemented

- Local EVE VAE / ESM-1v transformer inference (consumes precomputed scores)
- Protein embedding layer
- Web portal / score browser
- Containerization (Docker)
- HPC scheduler integration (SLURM)

## Test Coverage

57 tests passing (popeve env + fertility_gp env).  Module-level test counts:

| Module | Tests |
|--------|-------|
| GP model (PGLikelihood, PopEVEGP) | 9 |
| GP trainer (training, checkpoints, scoring) | 7 |
| GP builder (data prep, readiness) | 4 |
| GP candidate space | 1 |
| Phenotype exporter | 5 |
| Training matrix | 2 |
| Config loader | 4 |
| Protein parser | 4 |
| Variant record, genotype, merge, runner | 4 |
| Feature matrix validation | 1 |
| Real variant validation | 1 |
