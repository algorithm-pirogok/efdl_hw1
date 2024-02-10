from typing import Dict, Tuple

import torch
import torch.nn as nn


class DiffusionModel(nn.Module):
    def __init__(
        self,
        eps_model: nn.Module,
        betas: Tuple[float, float],
        num_timesteps: int,
    ):
        super().__init__()
        self.eps_model = eps_model

        for name, schedule in get_schedules(betas[0], betas[1], num_timesteps).items():
            self.register_buffer(name, schedule)

        self.num_timesteps = num_timesteps
        self.criterion = nn.MSELoss()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        timestep = torch.randint(1, self.num_timesteps + 1, (x.shape[0],)).to(x.device) # переносим все объекты на 1 девайс
        eps = torch.randn_like(x).to(x.device) # fix какая-то проверка на внимательность, заменил rand на randn

        x_t = (
            self.sqrt_alphas_cumprod[timestep, None, None, None].to(x.device) * x
            + self.sqrt_one_minus_alpha_prod[timestep, None, None, None].to(x.device) * eps # fix не тот коэффициент
        )

        return self.criterion(eps, self.eps_model(x_t, timestep / self.num_timesteps))

    def sample(self, num_samples: int, size, device) -> torch.Tensor:

        x_i = torch.randn(num_samples, *size).to(device) # fix не было привязки к девайсу

        # fix 3 так-то невключительно до 0 идет, поэтому нужно брать -1
        for i in range(self.num_timesteps, -1, -1):
            z = torch.randn(num_samples, *size).to(device) if i > 1 else 0 # fix не было привязки к девайсу
            eps = self.eps_model(x_i, torch.tensor(i / self.num_timesteps).repeat(num_samples, 1).to(device))
            x_i = self.inv_sqrt_alphas[i].to(device) * (x_i - eps * self.one_minus_alpha_over_prod[i]) + self.sqrt_betas[i].to(device) * z
        return x_i

def get_schedules(beta1: float, beta2: float, num_timesteps: int) -> Dict[str, torch.Tensor]:
    assert 0 < beta1 < beta2 < 1.0, "beta1 and beta2 must be in (0, 1)"
    # fix заметил, что нет оценки снизу и добавил < 0

    betas = (beta2 - beta1) * torch.arange(0, num_timesteps + 1, dtype=torch.float32) / num_timesteps + beta1
    sqrt_betas = torch.sqrt(betas)
    alphas = 1 - betas

    alphas_cumprod = torch.cumprod(alphas, dim=0)

    
    sqrt_alphas_cumprod = torch.sqrt(alphas_cumprod)
    inv_sqrt_alphas = 1 / torch.sqrt(alphas)

    sqrt_one_minus_alpha_prod = torch.sqrt(1 - alphas_cumprod)
    one_minus_alpha_over_prod = (1 - alphas) / sqrt_one_minus_alpha_prod

    return {
        "alphas": alphas,
        "inv_sqrt_alphas": inv_sqrt_alphas,
        "sqrt_betas": sqrt_betas,
        "alphas_cumprod": alphas_cumprod,
        "sqrt_alphas_cumprod": sqrt_alphas_cumprod,
        "sqrt_one_minus_alpha_prod": sqrt_one_minus_alpha_prod,
        "one_minus_alpha_over_prod": one_minus_alpha_over_prod,
    }
