import itertools
import random
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import gpytorch
import numpy as np
import pandas as pd
import torch

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


def _percentiles_from_samples(samples, percentiles=(0.05, 0.5, 0.95)):
    """Compute percentiles from a tensor of posterior samples.

    Mirrors ``utils/helpers.py::percentiles_from_samples`` from the
    official `debbiemarkslab/popEVE`_ implementation.

    Parameters
    ----------
    samples : torch.Tensor
        Posterior function samples of shape ``(n_samples, n_variants)``.
    percentiles : tuple of float
        Percentiles to return.
    """
    num_samples = samples.size(0)
    sorted_samples = samples.sort(dim=0)[0]
    return [sorted_samples[int(num_samples * p)] for p in percentiles]


def train_protein_gp(
    training_file,
    output_dir,
    epochs=6000,
    inducing_points=20,
    seed=42,
    training_frac=1.0,
    lr_ngd=0.1,
    lr_adam=0.05,
    lengthscale_init=0.2,
    checkpoint_every=1000,
    checkpoint_dir=None,
    losses_dir=None,
    scores_dir=None,
    states_dir=None,
    convergence_patience=0,
    convergence_threshold=1e-4,
):
    """Fit one popEVE GP, producing scores, checkpoints, and training history.

    Aligned with the training methodology from:

        Orenbuch et al. "Deep generative modeling of the human proteome
        reveals over a hundred novel genes involved in rare genetic
        disorders."  medRxiv, 2023.

    Official implementation: https://github.com/debbiemarkslab/popEVE

    Parameters
    ----------
    training_file : str or Path
        CSV with columns ``model_score, observed`` (and optionally ``mutant``).
    output_dir : str or Path
        Base directory for outputs.  If the specialised directories below are
        *not* given, ``{stem}.pt``, ``{stem}_history.csv`` and
        ``{stem}_scores.csv`` are all written here.
    epochs : int
        Maximum training epochs.  Default 6 000 matches the official code.
    inducing_points : int
        Number of inducing points for the variational GP.
    seed : int
        Random seed (fixed to 42 in the official code).
    training_frac : float
        Fraction of data used for training.  Set to 1.0 (official default)
        to train on all data; set to e.g. 0.8 for a 20 % holdout split.
    lr_ngd : float
        Learning rate for the NGD (variational) optimizer.
    lr_adam : float
        Learning rate for the Adam (hyperparameter) optimizer.
    lengthscale_init : float
        Initial value for the RBF kernel lengthscale.
    checkpoint_every : int
        Save a model checkpoint every N epochs (official default: 1 000).
        Set to 0 to disable.
    checkpoint_dir : str or Path, optional
        Where to write periodic checkpoint ``.pth`` files.  Falls back to
        ``output_dir / "states"`` when ``states_dir`` is also unset.
    losses_dir : str or Path, optional
        Where to write the loss/lengthscale history CSV.  Falls back to
        ``output_dir / "losses_and_lengthscales"`` when unset.
    scores_dir : str or Path, optional
        Where to write the per-variant scores CSV.  Falls back to
        ``output_dir / "scores"`` when unset.
    states_dir : str or Path, optional
        Where to write the final model state ``.pt`` file.  Falls back to
        ``output_dir / "states"`` when unset.
    convergence_patience : int
        If > 0, enable early stopping after this many epochs without
        improvement.  0 (default) disables early stopping to match the
        official behaviour of training for the full ``epochs``.
    convergence_threshold : float
        Minimum loss decrease to reset the patience counter.

    Returns
    -------
    history : list of dict
        Per-epoch ``{epoch, loss, val_loss, lengthscale}`` records.
    """
    training_file = Path(training_file)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    stem = training_file.stem

    def _resolve(path, default_name):
        return Path(path) if path is not None else output_dir / default_name

    ckpt_dir = _resolve(checkpoint_dir, "states")
    losses_d = _resolve(losses_dir, "losses_and_lengthscales")
    scores_d = _resolve(scores_dir, "scores")
    states_d = _resolve(states_dir, "states")
    for d in (ckpt_dir, losses_d, scores_d, states_d):
        d.mkdir(parents=True, exist_ok=True)

    frame = pd.read_csv(training_file)
    if frame.observed.nunique() != 2:
        raise ValueError(f"{training_file} requires both observed classes (0 and 1).")

    _set_seed(seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    scores = frame.model_score.to_numpy(dtype=np.float32)
    normalised, score_min, score_max = _normalise_scores(scores)

    train_x = torch.tensor(normalised[:, None], device=device)
    train_y = torch.tensor(frame.observed.to_numpy(dtype=np.float32), device=device)

    all_x_np = normalised
    val_x, val_y = None, None
    if training_frac < 1.0:
        n_val = max(1, int(len(train_x) * (1 - training_frac)))
        perm = torch.randperm(len(train_x), device=device)
        val_idx = perm[:n_val]
        train_idx = perm[n_val:]
        val_x, val_y = train_x[val_idx], train_y[val_idx]
        train_x, train_y = train_x[train_idx], train_y[train_idx]
        all_x_np = normalised

    M = min(inducing_points, len(train_x))
    inducing = torch.linspace(0, 1, M, dtype=train_x.dtype, device=device).unsqueeze(-1)
    model, likelihood = PopEVEGP(inducing).to(device), PGLikelihood().to(device)
    model.covar_module.base_kernel.initialize(lengthscale=lengthscale_init)

    variational = gpytorch.optim.NGD(
        model.variational_parameters(), num_data=len(train_y), lr=lr_ngd
    )
    hyperparameters = torch.optim.Adam(
        [{"params": model.hyperparameters()}, {"params": likelihood.parameters()}],
        lr=lr_adam,
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
                val_loss = float(-objective(model(val_x), val_y).detach().cpu())
            model.train()
            likelihood.train()

        history.append({
            "epoch": epoch + 1,
            "loss": loss_val,
            "val_loss": val_loss,
            "lengthscale": lengthscale_val,
        })

        if checkpoint_every and (epoch + 1) % checkpoint_every == 0:
            torch.save(
                {"model": model.state_dict(), "likelihood": likelihood.state_dict()},
                ckpt_dir / f"{stem}_model_{epoch + 1}.pth",
            )

        if convergence_patience > 0:
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

    if convergence_patience > 0 and best_state is not None:
        model.load_state_dict(best_state["model"])
        likelihood.load_state_dict(best_state["likelihood"])
        score_min, score_max = best_state["score_min"], best_state["score_max"]

    final_state = {
        "model": model.state_dict(),
        "likelihood": likelihood.state_dict(),
        "score_min": score_min,
        "score_max": score_max,
    }
    torch.save(final_state, states_d / f"{stem}_model_final.pth")

    model.eval()
    likelihood.eval()
    all_x = torch.tensor(all_x_np[:, None], device=device)
    with torch.no_grad(), gpytorch.settings.fast_pred_var():
        posterior = model(all_x)
        n_samples = 1000
        samples = posterior.sample(torch.Size([n_samples]))
        gp_lower, gp_median, gp_upper = _percentiles_from_samples(samples)

    frame_out = frame.copy()
    frame_out["X"] = all_x_np
    frame_out["GP_mean"] = posterior.mean.detach().cpu().numpy()
    frame_out["GP_lower"] = gp_lower.cpu().numpy()
    frame_out["GP_upper"] = gp_upper.cpu().numpy()
    frame_out["GP_mean_all_samples"] = samples.mean(0).cpu().numpy()
    frame_out["mean_prob"] = posterior.mean.sigmoid().detach().cpu().numpy()

    frame_out.to_csv(scores_d / f"{stem}_scores.csv", index=False)

    losses_df = pd.DataFrame(history)
    losses_df.to_csv(losses_d / f"{stem}_loss_lengthscale.csv", index=False)

    return history


def train_protein_ensemble(
    training_dir,
    model_names,
    protein_id,
    output_dir,
    epochs=6000,
    training_frac=1.0,
    **kwargs,
):
    """Train separate GPs for each evo model and ensemble by averaging.

    The popEVE ensemble score is the mean of the GP posterior means across
    all constituent evo models (see Orenbuch et al. §3.3, Eq. B.19).

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
            training_frac=training_frac,
            **kwargs,
        )
        histories[model_name] = hist
        stem = f"{protein_id}_{model_name}"
        scores_path = output_dir / "scores" / f"{stem}_scores.csv"
        scores = pd.read_csv(scores_path)
        ensemble_means.append(scores["mean_prob"].values)
        ensemble_lowers.append(scores["GP_lower"].values)
        ensemble_uppers.append(scores["GP_upper"].values)

    if not ensemble_means:
        raise ValueError(f"No models trained for {protein_id}")

    ensemble_means = np.mean(ensemble_means, axis=0)
    ensemble_lowers = np.min(ensemble_lowers, axis=0)
    ensemble_uppers = np.max(ensemble_uppers, axis=0)

    stem_first = f"{protein_id}_{model_names[0]}"
    ref_scores = pd.read_csv(output_dir / "scores" / f"{stem_first}_scores.csv")
    ensemble_df = ref_scores[["mutant", "observed", "model_score"]].copy()
    ensemble_df["gp_mean_probability"] = ensemble_means
    ensemble_df["gp_lower"] = ensemble_lowers
    ensemble_df["gp_upper"] = ensemble_uppers
    ensemble_df["n_models"] = len(model_names)

    (output_dir / "scores").mkdir(parents=True, exist_ok=True)
    ensemble_df.to_csv(
        output_dir / "scores" / f"{protein_id}_ensemble_scores.csv", index=False
    )
    print(f"  [ENSEMBLE] {protein_id}: {len(model_names)} models, {len(ensemble_df)} variants")
    return histories


def train_eligible_proteins(
    readiness_file,
    output_dir,
    epochs=6000,
    max_proteins=None,
    training_frac=1.0,
    ensemble_mode=False,
    model_names=None,
    **kwargs,
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
        available_models = (
            subset["evo_model"].tolist() if "evo_model" in subset.columns else None
        )

        if ensemble_mode and model_names:
            used_models = [m for m in model_names if m in available_models]
            if not used_models:
                continue
            train_protein_ensemble(
                Path(readiness_file).parent,
                used_models,
                protein_id,
                output_dir,
                epochs=epochs,
                training_frac=training_frac,
                **kwargs,
            )
        else:
            for row in subset.itertuples(index=False):
                train_protein_gp(
                    row.file_path,
                    output_dir,
                    epochs=epochs,
                    training_frac=training_frac,
                    **kwargs,
                )
        trained.append(protein_id)

    return trained


def _train_gp_subprocess(
    gpu_id, csv_path, output_dir, epochs, training_frac, seed, checkpoint_every=1000,
    mem_limit_gb=None, convergence_patience=0,
):
    """Run ``train_protein_gp`` in a subprocess pinned to one GPU."""
    csv_path = Path(csv_path).resolve()
    output_dir = Path(output_dir).resolve()

    project_root = str(Path(__file__).resolve().parents[2])

    mem_preamble = ""
    if mem_limit_gb:
        limit_bytes = int(mem_limit_gb * 1024 ** 3)
        mem_preamble = (
            f"import resource; "
            f"resource.setrlimit(resource.RLIMIT_AS, ({limit_bytes}, {limit_bytes})); "
        )
    script = (
        f"import sys; sys.path.insert(0, {project_root!r}); "
        f"{mem_preamble}"
        f"from fertility_popeve.gp.trainer import train_protein_gp; "
        f"train_protein_gp("
        f"{str(csv_path)!r}, {str(output_dir)!r}, "
        f"epochs={epochs}, training_frac={training_frac}, "
        f"seed={seed}, checkpoint_every={checkpoint_every}, "
        f"convergence_patience={convergence_patience})"
    )
    env = {**__import__("os").environ, "CUDA_VISIBLE_DEVICES": str(gpu_id)}
    result = subprocess.run(
        [sys.executable, "-c", script],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
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
        means.append(s["mean_prob"].values)
        lowers.append(s["GP_lower"].values)
        uppers.append(s["GP_upper"].values)

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
    training_frac=1.0,
    gpu_ids=None,
    max_proteins=None,
    seed=42,
    mem_limit_gb=None,
    checkpoint_every=1000,
    convergence_patience=0,
):
    """Train GP models in parallel across multiple GPUs.

    Each protein's EVE + ESM1V models are dispatched to different GPUs,
    then ensembled after all individual training jobs complete.

    Mirrors the iteration loop in the official ``train_popEVE_models.sh``
    but with multi-GPU parallelism.

    Parameters
    ----------
    readiness_file : str or Path
        Path to ``training_readiness.csv``.
    output_dir : str or Path
        Base output directory.  Sub-directories ``states/``, ``scores/``,
        ``losses_and_lengthscales/`` are created inside.
    epochs : int
    training_frac : float
        Fraction of data for training (1.0 = all data, official default).
    gpu_ids : list of int, optional
    max_proteins : int, optional
    seed : int
    mem_limit_gb : float or None
        Per-subprocess memory limit in GB (via RLIMIT_AS).
    checkpoint_every : int
        Save intermediate checkpoints every N epochs.
    convergence_patience : int
        If > 0, enable early stopping.
    """
    if gpu_ids is None:
        gpu_ids = list(range(torch.cuda.device_count())) or [0]
    elif isinstance(gpu_ids, int):
        gpu_ids = list(range(gpu_ids))

    readiness = pd.read_csv(readiness_file)
    eligible = readiness[readiness.eligible_for_training].sort_values("protein_id")
    if max_proteins is not None:
        eligible = eligible.head(max_proteins)

    output_dir = Path(output_dir)
    for sub in ("states", "scores", "losses_and_lengthscales"):
        (output_dir / sub).mkdir(parents=True, exist_ok=True)

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
        _train_gp_subprocess(
            gpu, task["file_path"], output_dir, epochs, training_frac, seed,
            checkpoint_every=checkpoint_every, mem_limit_gb=mem_limit_gb,
            convergence_patience=convergence_patience,
        )
        return task

    with ThreadPoolExecutor(max_workers=len(gpu_ids)) as pool:
        futures = [pool.submit(_run, t) for t in tasks]
        for f in as_completed(futures):
            r = f.result()
            trained_set.add(r["protein_id"])
            print(f"  [DONE] {r['protein_id']}_{r['evo_model']}")

    for pid in sorted(trained_set):
        subset = eligible[eligible.protein_id == pid]
        compute_ensemble_scores(pid, subset["evo_model"].tolist(), output_dir / "scores")

    print(f"[INFO] Trained {len(trained_set)} proteins across {len(gpu_ids)} GPUs")
    return list(trained_set)
