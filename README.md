# fertility-popEVE

A population-aware evolutionary model for reproductive genomics.

fertility-popEVE adapts the popEVE framework to reproductive medicine by integrating population-aware evolutionary scores, protein foundation models, clinical phenotype labels, gene burden analysis and Gaussian Process calibration for infertility-related genomic analysis.

## Project Status

Current version: v0.6

fertility-popEVE has completed the core feature extraction pipeline, phenotype integration pipeline and real cohort sample mapping pipeline.

Completed modules:

- VCF processing pipeline ✅
- VEP annotation pipeline ✅
- Missense variant filtering ✅
- Protein sequence preparation ✅
- Protein ID mapping ✅
- popEVE feature extraction ✅
- EVE / ESM1v feature integration ✅
- Variant feature matrix construction ✅
- GP training data preparation ✅
- Reproductive phenotype integration ✅
- Sample ID and proband gVCF mapping ✅

Current development:

- Real cohort joint calling 🚧
- Large-scale variant annotation 🚧
- Fertility-specific model training 🚧


## Pipeline Overview
