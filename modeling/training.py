import torch
from torch.optim.optimizer import Optimizer
from torch.utils.data import DataLoader
from torchvision.utils import make_grid, save_image
from tqdm import tqdm
import wandb

from modeling.diffusion import DiffusionModel


def train_step(model: DiffusionModel, inputs: torch.Tensor, optimizer: Optimizer, device: str):
    optimizer.zero_grad()
    inputs = inputs.to(device)
    loss = model(inputs)
    loss.backward()
    optimizer.step()
    return loss


def train_epoch(model: DiffusionModel, dataloader: DataLoader, optimizer: Optimizer, device: str, epoch: int = None, logging_policy: int = None):
    model.train()
    pbar = tqdm(dataloader)
    loss_ema = None
    for step, (x, _) in enumerate(pbar):
        train_loss = train_step(model, x, optimizer, device)
        loss_ema = train_loss if loss_ema is None else 0.9 * loss_ema + 0.1 * train_loss
        pbar.set_description(f"loss: {loss_ema:.4f}")
        if logging_policy is not None and step % logging_policy == 0: # fix Добавили wandb
            wandb.log({"loss": loss_ema, "learning_rate": optimizer.param_groups[0]['lr']}, step=step + epoch * len(dataloader))
    return x

def generate_samples(model: DiffusionModel, device: str, path: str, noise: torch.Tensor = None, is_save: bool = True):
    model.eval()
    with torch.no_grad():
        samples = model.sample(8, (3, 32, 32), device=device, noise=noise)
        grid = make_grid(samples, nrow=4)
        if is_save:
            save_image(grid, path)
    return samples
