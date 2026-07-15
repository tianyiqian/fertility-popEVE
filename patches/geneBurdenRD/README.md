# geneBurdenRD Compatibility Patches

This directory stores compatibility patches applied to the upstream
geneBurdenRD project.

## prepare.patch

Purpose:

- Replace `library(tidyverse)` with minimal dependencies:
  - readr
  - dplyr
  - data.table

Reason:

The upstream script depends on the tidyverse meta-package, which fails
to install on our HPC environment because of ICU/xml2 runtime
dependencies.

The prepare script only requires readr, dplyr and data.table.

Additional changes:

- Remove verbose debugging output
- Replace with concise INFO messages

This patch has been validated using fertility-popEVE generated master TSV.
