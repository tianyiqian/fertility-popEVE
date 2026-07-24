import pytest
import torch
import gpytorch
from fertility_popeve.gp.model import PGLikelihood, PopEVEGP


class TestPGLikelihood:
    def test_likelihood_is_binary(self):
        likelihood = PGLikelihood()
        samples = torch.randn(10)
        dist = likelihood(samples)
        assert isinstance(dist, torch.distributions.Bernoulli)

    def test_forward_outputs_probs_in_01(self):
        likelihood = PGLikelihood()
        samples = torch.linspace(-5, 5, 20)
        probs = likelihood(samples).probs
        assert (probs >= 0).all()
        assert (probs <= 1).all()

    def test_expected_log_prob_scalar_output(self):
        likelihood = PGLikelihood()
        mean = torch.randn(5)
        variance = torch.rand(5) * 0.5 + 0.1
        target = torch.randint(0, 2, (5,)).float()

        class _Fake:
            pass

        inp = _Fake()
        inp.mean = mean
        inp.variance = variance
        result = likelihood.expected_log_prob(target, inp)
        assert result.ndim == 0

    def test_marginal_returns_bernoulli(self):
        likelihood = PGLikelihood()
        inducing = torch.linspace(0, 1, 5).unsqueeze(-1)
        model = PopEVEGP(inducing)
        model.eval()
        with torch.no_grad():
            f_dist = model(torch.linspace(0.1, 0.9, 10).unsqueeze(-1))
        marginal = likelihood.marginal(f_dist)
        assert isinstance(marginal, torch.distributions.Bernoulli)


class TestPopEVEGP:
    def test_model_creation(self):
        inducing = torch.linspace(0, 1, 20).unsqueeze(-1)
        model = PopEVEGP(inducing)
        assert isinstance(model, gpytorch.models.ApproximateGP)

    def test_forward_returns_multivariate_normal(self):
        inducing = torch.linspace(0, 1, 20).unsqueeze(-1)
        model = PopEVEGP(inducing)
        model.eval()
        with torch.no_grad():
            result = model(torch.rand(10, 1))
        assert isinstance(result, gpytorch.distributions.MultivariateNormal)

    def test_kernel_is_rbf(self):
        inducing = torch.linspace(0, 1, 20).unsqueeze(-1)
        model = PopEVEGP(inducing)
        assert isinstance(model.covar_module, gpytorch.kernels.ScaleKernel)
        assert isinstance(model.covar_module.base_kernel, gpytorch.kernels.RBFKernel)

    def test_default_lengthscale(self):
        inducing = torch.linspace(0, 1, 20).unsqueeze(-1)
        model = PopEVEGP(inducing)
        lengthscale = model.covar_module.base_kernel.lengthscale.item()
        assert lengthscale > 0

    def test_variational_strategy_learns_inducing(self):
        inducing = torch.linspace(0, 1, 10).unsqueeze(-1)
        model = PopEVEGP(inducing)
        assert model.variational_strategy.inducing_points.requires_grad
