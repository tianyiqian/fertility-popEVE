import gpytorch
import torch


class PGLikelihood(gpytorch.likelihoods._OneDimensionalLikelihood):
    """Variational Pólya-Gamma likelihood for binary GP classification."""

    def expected_log_prob(self, target, input):
        mean, variance = input.mean, input.variance
        second_moment = variance + mean.pow(2)
        signed_target = target.to(mean.dtype).mul(2).sub(1)
        c = second_moment.detach().sqrt().clamp_min(1e-8)
        half_omega = 0.25 * torch.tanh(0.5 * c) / c
        return (0.5 * signed_target * mean - half_omega * second_moment).sum(dim=-1)

    def forward(self, function_samples):
        return torch.distributions.Bernoulli(logits=function_samples)

    def marginal(self, function_dist):
        probabilities = self.quadrature(lambda samples: self.forward(samples).probs, function_dist)
        return torch.distributions.Bernoulli(probs=probabilities)


class PopEVEGP(gpytorch.models.ApproximateGP):
    def __init__(self, inducing_points):
        variational_distribution = gpytorch.variational.NaturalVariationalDistribution(
            inducing_points.size(0)
        )
        strategy = gpytorch.variational.VariationalStrategy(
            self, inducing_points, variational_distribution, learn_inducing_locations=True
        )
        super().__init__(strategy)
        self.mean_module = gpytorch.means.ZeroMean()
        self.covar_module = gpytorch.kernels.ScaleKernel(gpytorch.kernels.RBFKernel())

    def forward(self, x):
        return gpytorch.distributions.MultivariateNormal(
            self.mean_module(x), self.covar_module(x)
        )
