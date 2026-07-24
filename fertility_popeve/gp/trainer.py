from pathlib import Path
import random
import subprocess
import sys
import itertools
from concurrent.futures import ThreadPoolExecutor, as_completed

import numpy as np
import pandas as pd
import torch
import gpytorch

from fertility_popeve.gp.model import PGLikelihood, PopEVEGP


def _set_seed(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


def _normalise_scores(scores_np, eps=1e-8):
    lower = float(scores_np.min())
    upper = float(scores_np.max())
    if upper - lower < eps:
        raise ValueError("Constant model score — cannot normalise.")
    normalised = (scores_np - lower) / (upper - lower)
    return normalised, lower, upper


def train_protein_gp(
    training_file,
    output_dir,
    epochs=6000,
    inducing_points=20,
    seed=42,
    holdout_frac=0.2,
    lr_ngd=0.1,
    lr_adam=0.05,
    lengthscale_init=0.2,
    convergence_patience=500,
    convergence_threshold=1e-4,
):
    """Fit one popEVE GP and write model state, training history and scores.

    Parameters
    ----------
    training_file : str or Path
        CSV with columns ``model_score, observed``.
    output_dir : str or Path
        Where to write ``{stem}.pt``, ``{stem}_history.csv``, ``{stem}_scores.csv``.
    holdout_frac : float
        Fraction of data held out for evaluation (0 = train on all).  The original
        popEVE paper uses 0.2.
    """
    training_file, output_dir = Path(training_file), Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    frame = pd.read_csv(training_file)
    if frame.observed.nunique() != 2:
        raise ValueError(f"{training_file} requires both observed classes.")

    _set_seed(seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    scores = frame.model_score.to_numpy(dtype=np.float32)
    normalised, score_min, score_max = _normalise_scores(scores)

    train_x = torch.tensor(normalised[:, None], device=device)
    train_y = torch.tensor(frame.observed.to_numpy(dtype=np.float32), device=device)

    train_indices = torch.arange(len(train_x), device=device)
    val_indices = None
    val_x, val_y = None, None

    if holdout_frac > 0:
        n_val = max(1, int(len(train_x) * holdout_frac))
        val_indices = torch.randperm(len(train_x), device=device)[:n_val]
        train_indices = torch.tensor(
            [i for i in range(len(train_x)) if i not in val_indices], device=device
        )
        val_x, val_y = train_x[val_indices], train_y[val_indices]
        train_x, train_y = train_x[train_indices], train_y[train_indices]

    inducing = torch.linspace(0, 1, min(inducing_points, len(train_x)), device=device).unsqueeze(-1)
    model, likelihood = PopEVEGP(inducing).to(device), PGLikelihood().to(device)
    model.covar_module.base_kernel.initialize(lengthscale=lengthscale_init)

    variational = gpytorch.optim.NGD(model.variational_parameters(), num_data=len(train_y), lr=lr_ngd)
    hyperparameters = torch.optim.Adam(
        [{"params": model.hyperparameters()}, {"params": likelihood.parameters()}], lr=lr_adam
    )
    objective = gpytorch.mlls.VariationalELBO(likelihood, model, num_data=len(train_y))

    history = []
    best_loss = float("inf")
    best_state = None
    stall_count = 0

    model.train()
    likelihood.train()
    for epoch in range(epochs):
        variational.zero_grad()
        hyperparameters.zero_grad()
        loss = -objective(model(train_x), train_y)
        loss.backward()
        variational.step()
        hyperparameters.step()
        loss_val = float(loss.detach().cpu())
        lengthscale_val = float(model.covar_module.base_kernel.lengthscale.detach().cpu())

        val_loss = None
        if val_x is not None:
            model.eval()
            likelihood.eval()
            with torch.no_grad():
                val_loss = -objective(model(val_x), val_y)
                val_loss = float(val_loss.detach().cpu())
            model.train()
            likelihood.train()

        history.append({
            "epoch": epoch + 1,
            "loss": loss_val,
            "val_loss": val_loss,
            "lengthscale": lengthscale_val,
        })

        if loss_val < best_loss - convergence_threshold:
            best_loss = loss_val
            best_state = {
                "model": model.state_dict(),
                "likelihood": likelihood.state_dict(),
                "score_min": score_min,
                "score_max": score_max,
            }
            stall_count = 0
        else:
            stall_count += 1

        if stall_count >= convergence_patience:
            break

    if best_state is None:
        best_state = {
            "model": model.state_dict(),
            "likelihood": likelihood.state_dict(),
            "score_min": score_min,
            "score_max": score_max,
        }

    model.eval()
    likelihood.eval()
    all_x = torch.tensor(normalised[:, None], device=device)
    with torch.no_grad(), gpytorch.settings.fast_pred_var():
        posterior = model(all_x)
        samples = posterior.sample(torch.Size([1000]))
        frame["gp_mean_probability"] = likelihood(posterior).probs.cpu().numpy()
        frame["gp_lower"] = samples.quantile(0.05, dim=0).sigmoid().cpu().numpy()
        frame["gp_upper"] = samples.quantile(0.95, dim=0).sigmoid().cpu().numpy()

    stem = training_file.stem
    torch.save(best_state, output_dir / f"{stem}.pt")
    pd.DataFrame(history).to_csv(output_dir / f"{stem}_history.csv", index=False)
    frame.to_csv(output_dir / f"{stem}_scores.csv", index=False)
    return history


def train_protein_ensemble(
    training_dir,
    model_names,
    protein_id,
    output_dir,
    epochs=6000,
    holdout_frac=0.2,
    **kwargs,
):
    """Train separate GPs for each evo model and ensemble by averaging.

    The popEVE ensemble score is the mean of the GP posterior means across
    all constituent evo models (see dissertation §3.3, Eq. B.19).

    Parameters
    ----------
    training_dir : str or Path
        Directory with ``{protein_id}_{model_name}.csv`` files.
    model_names : list of str
        Evo model names, e.g. ``["EVE", "ESM1v"]``.
    protein_id : str
    output_dir : str or Path
    """
    training_dir = Path(training_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    ensemble_means = []
    ensemble_lowers = []
    ensemble_uppers = []
    histories = {}

    for model_name in model_names:
        csv_path = training_dir / f"{protein_id}_{model_name}.csv"
        if not csv_path.exists():
            print(f"  [SKIP] {csv_path} not found")
            continue
        hist = train_protein_gp(
            csv_path,
            output_dir,
            epochs=epochs,
            holdout_frac=holdout_frac,
            **kwargs,
        )
        histories[model_name] = hist
        scores = pd.read_csv(output_dir / f"{protein_id}_{model_name}_scores.csv")
        ensemble_means.append(scores["gp_mean_probability"].values)
        ensemble_lowers.append(scores["gp_lower"].values)
        ensemble_uppers.append(scores["gp_upper"].values)

    if not ensemble_means:
        raise ValueError(f"No models trained for {protein_id}")

    ensemble_means = np.mean(ensemble_means, axis=0)
    ensemble_lowers = np.min(ensemble_lowers, axis=0)
    ensemble_uppers = np.max(ensemble_uppers, axis=0)

    ref_scores = pd.read_csv(output_dir / f"{protein_id}_{model_names[0]}_scores.csv")
    ensemble_df = ref_scores[["mutant", "observed", "model_score"]].copy()
    ensemble_df["gp_mean_probability"] = ensemble_means
    ensemble_df["gp_lower"] = ensemble_lowers
    ensemble_df["gp_upper"] = ensemble_uppers
    ensemble_df["n_models"] = len(model_names)

    ensemble_df.to_csv(output_dir / f"{protein_id}_ensemble_scores.csv", index=False)
    print(f"  [ENSEMBLE] {protein_id}: {len(model_names)} models, {len(ensemble_df)} variants")
    return histories


def train_eligible_proteins(
    readiness_file,
    output_dir,
    epochs=6000,
    max_proteins=None,
    holdout_frac=0.2,
    ensemble_mode=False,
    model_names=None,
):
    """Train GP models for all eligible proteins.

    If ``ensemble_mode=True``, trains separate GPs for each ``model_name``
    per protein and writes an ensemble score file.
    """
    readiness = pd.read_csv(readiness_file)
    eligible = readiness[readiness.eligible_for_training].sort_values("protein_id")
    if max_proteins is not None:
        eligible = eligible.head(max_proteins)

    trained = []
    for protein_id in eligible["protein_id"].unique():
        subset = eligible[eligible.protein_id == protein_id]
        available_models = subset["evo_model"].tolist() if "evo_model" in subset.columns else None

        if ensemble_mode and model_names:
            used_models = [m for m in model_names if m in available_models]
            train_protein_ensemble(
                Path(readiness_file).parent,
                used_models,
                protein_id,
                output_dir,
                epochs=epochs,
                holdout_frac=holdout_frac,
            )
        else:
            for row in subset.itertuples(index=False):
                train_protein_gp(
                    row.file_path,
                    output_dir,
                    epochs=epochs,
                    holdout_frac=holdout_frac,
                )
        trained.append(protein_id)

    return trained


def _train_gp_subprocess(gpu_id, csv_path, output_dir, epochs, holdout_frac, seed, mem_limit_gb=None):
    """Run ``train_protein_gp`` in a subprocess pinned to one GPU."""
    csv_path = Path(csv_path).resolve()
    output_dir = Path(output_dir).resolve()
    mem_preamble = ""
    if mem_limit_gb:
        mem_preamble = (
            f"import resource; "
            f"resource.setrlimit(resource.RLIMIT_AS, "
            f"({int(mem_limit_gb * 1024**3)}, {int(mem_limit_gb * 1024**3)})); "
        )
    script = (
        f"import sys; sys.path.insert(0, '{csv_path.parent.parent.parent}'); "
        f"{mem_preamble}"
        f"from fertility_popeve.gp.trainer import train_protein_gp; "
        f"train_protein_gp("
        f"r'{csv_path}', r'{output_dir}', "
        f"epochs={epochs}, holdout_frac={holdout_frac}, seed={seed})"
    )
    env = {**__import__("os").environ, "CUDA_VISIBLE_DEVICES": str(gpu_id)}
    result = subprocess.run(
        [sys.executable, "-c", script], env=env,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode != 0:
        print(f"  [ERROR] GPU{gpu_id} {csv_path.name}: {result.stderr[:500]}")
        raise RuntimeError(f"GPU{gpu_id} training failed for {csv_path.name}")
    for line in result.stdout.strip().split("\n"):
        if line.strip():
            print(f"  [GPU{gpu_id}] {line}")


def compute_ensemble_scores(protein_id, model_names, output_dir):
    """Ensemble trained GP scores by averaging posterior means across models."""
    output_dir = Path(output_dir)
    means, lowers, uppers = [], [], []

    for m in model_names:
        sp = output_dir / f"{protein_id}_{m}_scores.csv"
        if not sp.exists():
            continue
        s = pd.read_csv(sp)
        means.append(s["gp_mean_probability"].values)
        lowers.append(s["gp_lower"].values)
        uppers.append(s["gp_upper"].values)

    if not means:
        return

    ref = pd.read_csv(output_dir / f"{protein_id}_{model_names[0]}_scores.csv")
    out = ref[["mutant", "observed", "model_score"]].copy()
    out["gp_mean_probability"] = np.mean(means, axis=0)
    out["gp_lower"] = np.min(lowers, axis=0)
    out["gp_upper"] = np.max(uppers, axis=0)
    out["n_models"] = len(model_names)
    out.to_csv(output_dir / f"{protein_id}_ensemble_scores.csv", index=False)
    print(f"  [ENSEMBLE] {protein_id}: {len(model_names)} models, {len(out)} variants")


def train_eligible_proteins_multi_gpu(
    readiness_file,
    output_dir,
    epochs=6000,
    holdout_frac=0.2,
    gpu_ids=None,
    max_proteins=None,
    seed=42,
    mem_limit_gb=None,
):
    """Train GP models in parallel across multiple GPUs.

    Each protein's EVE + ESM1V models are dispatched to different GPUs,
    then ensembled after all individual training jobs complete.

    Parameters
    ----------
    mem_limit_gb : float or None
        Per-subprocess memory limit in GB (via RLIMIT_AS).
    """
    if gpu_ids is None:
        gpu_ids = list(range(torch.cuda.device_count())) or [0]
    elif isinstance(gpu_ids, int):
        gpu_ids = list(range(gpu_ids))

    readiness = pd.read_csv(readiness_file)
    eligible = readiness[readiness.eligible_for_training].sort_values("protein_id")
    if max_proteins is not None:
        eligible = eligible.head(max_proteins)

    output_dir = Path(output_dir) / "models"
    output_dir.mkdir(parents=True, exist_ok=True)

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
    trained_set = set()

    def _run(task):
        gpu = next(gpu_cycle)
        _train_gp_subprocess(gpu, task["file_path"], output_dir, epochs, holdout_frac, seed, mem_limit_gb)
        return task

    with ThreadPoolExecutor(max_workers=len(gpu_ids)) as pool:
        futures = [pool.submit(_run, t) for t in tasks]
        for f in as_completed(futures):
            r = f.result()
            trained_set.add(r["protein_id"])
            print(f"  [DONE] {r['protein_id']}_{r['evo_model']}")

    for pid in sorted(trained_set):
        subset = eligible[eligible.protein_id == pid]
        compute_ensemble_scores(pid, subset["evo_model"].tolist(), output_dir)

    print(f"[INFO] Trained {len(trained_set)} proteins across {len(gpu_ids)} GPUs")
    return list(trained_set)
