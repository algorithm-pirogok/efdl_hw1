import hydra
from hydra.utils import instantiate
import torch
import os
import wandb
from modeling.training import generate_samples, train_epoch

@hydra.main(config_path=".", config_name="main_config")
def main(clf):
    
    if not os.path.exists('samples'):
        os.mkdir('samples')

    
    clf['device'] = "cuda" if torch.cuda.is_available() else "cpu"
    ddpm = instantiate(clf['DiffusionModel']).to(clf['device'])

    train_transforms = instantiate(clf['Augmentations'])
    dataset = instantiate(clf['CIFAR10'], transform=train_transforms)

    dataloader = instantiate(clf['DataLoader'], dataset)
    optim = instantiate(clf['optimizer'], ddpm.parameters())
    
    # wandb.login()
    # wandb.init(project='hw_1', name=clf.name, config=clf)

    
    for i in range(clf['num_epochs']):
        train_epoch(ddpm, dataloader, optim, clf['device'])
        generate_samples(ddpm, clf['device'], f"samples/{i:02d}.png")


if __name__ == "__main__":
    main()
