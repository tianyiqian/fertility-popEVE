# AGENTS.md — fertility-popEVE

## Environments (critical)

Two separate conda environments:

| Env | YAML | Uses |
|-----|------|------|
| `popeve` | `environment/fertility_popeve.yml` | Pipeline steps 01–14, 16, most tests |
| `fertility_gp` | `environment/fertility_gp.yml` | GP training (step 15) and GP-related tests |

Step 15 (`15_train_fertility_popeve.py`) imports `torch`/`gpytorch` — **must run in `fertility_gp` env**.

## Running tests

```bash
# Main pipeline tests (popeve env)
conda run -n popeve pytest tests/ -v

# Single test file
conda run -n popeve pytest tests/test_config.py -v

# GP-related tests (fertility_gp env)
conda run -n fertility_gp pytest tests/test_gp_model.py tests/test_gp_trainer.py tests/test_gp_builder.py tests/test_candidate_space.py -v
```

`pythonpath = .` is set in `pytest.ini`.

Tests that require gitignored data (`test_genotype.py`, `test_real_variant.py`, `test_training.py`) **skip gracefully with `pytest.skip`** when data is missing — no manual `--ignore` flags needed on a fresh clone.

## Running the pipeline

```bash
# Full pipeline (reads config/pipeline.yaml for step order)
python run_pipeline.py

# GP training separately (REQUIRES fertility_gp env)
conda run -n fertility_gp python scripts/15_train_fertility_popeve.py

# Individual step (runs as module from project root)
conda run -n popeve python -m scripts.01_run_vep
```

Pipeline steps are defined in `config/pipeline.yaml` as module paths (e.g. `scripts.01_run_vep`). `run_pipeline.py` launches a memory watchdog daemon that monitors `/proc/meminfo` and kills heaviest child processes when available RAM drops below `danger_threshold_gb`.

## Architecture

```
fertility_popeve/          # Core library (no packaging — uses sys.path hacks)
├── annotation/            # VEP runner, feature extractor
├── burden/                # GeneBurdenRD export, phenotype validation/export
├── features/              # Feature merge, training matrix, popEVE queries
├── gp/                    # GP model, trainer, builder, candidate space
├── reference/             # Reference database
├── utils/                 # Config loader, logger, memory utils, validation
├── variant/               # VariantRecord, protein HGVSp parser, genotypes
├── embedding/             # Stub (planned)
├── eve/                   # Stub (planned — reads precomputed scores today)
├── pipeline/              # Stub
└── providers/             # Stub
scripts/                   # Pipeline step scripts (00–16)
```

Scripts use the pattern `sys.path.insert(0, str(PROJECT_ROOT))` then `# noqa: E402` after module-level imports — do not refactor this into a package install without updating all scripts.

## GP training specifics

Aligned with [debbiemarkslab/popEVE](https://github.com/debbiemarkslab/popEVE):
- RBF kernel, Pólya-Gamma likelihood, Natural Variational Distribution
- 6,000 epochs, checkpoints every 1,000
- Fixed seed 42
- Per-protein training; ensemble averages EVE + ESM1v posterior means
- Output layout: `{gp_dir}/states/`, `scores/`, `losses_and_lengthscales/`

**Admission criteria** (in `config/config.yaml` under `gp_training`):
- `min_candidates: 100` — minimum missense variants per protein
- `min_observed_variants: 10` — minimum cohort-observed mutations per protein
Proteins below these thresholds are skipped. Small test datasets will naturally produce zero trained proteins — this is expected.

## Configuration

The committed config is `config/config.example.yaml` (with `${ENV_VAR:default}` placeholders).
`config/config.yaml` is **gitignored** — the first `load_config()` call copies the example as a starting template.

Override any path via env var, e.g.:
```bash
export FPEVE_ANNOTATION=/my/data/annotation
export FPEVE_GP=/my/data/gp
```

Key sections:
- `paths` — data directories (override with env vars for portability)
- `gp_training` — epochs, admission criteria, learning rates
- `memory` — watchdog thresholds (safe/danger GB, interval, per-subprocess limit)

Variant configs: `config_30.yaml`, `config_full.yaml` — copy one to `config/config.yaml` to switch cohort sizes.

## Linting & formatting

```bash
# Check
conda run -n popeve ruff check fertility_popeve/ scripts/ tests/
# Auto-fix
conda run -n popeve ruff check --fix fertility_popeve/ scripts/ tests/
# Format
conda run -n popeve ruff format fertility_popeve/ scripts/ tests/
```

Config is in `pyproject.toml` (`[tool.ruff]`). `E402` (module-level import after `sys.path.insert`) is ignored project-wide.

## CI

GitHub Actions (`.github/workflows/test.yml`) runs data-independent tests in both `popeve` and `gp` environments on push to `main`.

## Key gotchas

- **No packaging**: no `setup.py`. All imports resolve via `sys.path.insert`. Do not refactor into `pip install`.
- **Step 15 needs `fertility_gp` env**, not `popeve`.
- **Gitignored data**: `data/`, `models/`, `outputs/` and `tests/test_phenotype.csv` are not in the repo.
