"""Command line tool to push locally save model checkpoints to huggingface

use:
python checkpoint_to_huggingface.py "path/to/model/checkpoints" \
    --local-path="~/tmp/this_model" \
    --no-push-to-hub
"""
import glob
import os
import tempfile
from typing import Optional

import hydra
import torch
import typer
import wandb
from pyaml_env import parse_config
from pvnet.models.multimodal.unimodal_teacher import Model as UMTModel


def push_to_huggingface(
    checkpoint_dir_path: str,
    val_best: bool = True,
    wandb_id: Optional[str] = None,
    local_path: Optional[str] = None,
    push_to_hub: bool = True,
):
    """Push a local model to pvnet_v2 huggingface model repo

    checkpoint_dir_path (str): Path of the chekpoint directory
    val_best (bool): Use best model according to val loss, else last saved model
    wandb_id (str): The wandb ID code
    local_path (str): Where to save the local copy of the model
    push_to_hub (bool): Whether to push the model to the hub or just create local version.
    """

    assert push_to_hub or local_path is not None

    os.path.dirname(os.path.abspath(__file__))

    # Check if checkpoint dir name is wandb run ID
    if wandb_id is None:
        all_wandb_ids = [run.id for run in wandb.Api().runs(path="openclimatefix/pvnet2.1")]
        dirname = checkpoint_dir_path.split("/")[-1]
        if dirname in all_wandb_ids:
            wandb_id = dirname

    # Load the model
    model_config = parse_config(f"{checkpoint_dir_path}/model_config.yaml")

    model = hydra.utils.instantiate(model_config)

    if val_best:
        # Only one epoch (best) saved per model
        files = glob.glob(f"{checkpoint_dir_path}/epoch*.ckpt")
        assert len(files) == 1
        checkpoint = torch.load(files[0], map_location="cpu")
    else:
        checkpoint = torch.load(f"{checkpoint_dir_path}/last.ckpt", map_location="cpu")

    model.load_state_dict(state_dict=checkpoint["state_dict"])
    
    if isinstance(model, UMTModel):
        model, model_config = model.convert_to_multimodal_model(model_config)

    # Check for data config
    data_config = f"{checkpoint_dir_path}/data_config.yaml"
    assert os.path.isfile(data_config)

    # Push to hub
    if local_path is None:
        temp_dir = tempfile.TemporaryDirectory()
        model_output_dir = temp_dir.name
    else:
        model_output_dir = local_path

    model.save_pretrained(
        model_output_dir,
        config=model_config,
        data_config=data_config,
        wandb_model_code=wandb_id,
        push_to_hub=push_to_hub,
        repo_id="openclimatefix/pvnet_v2" if push_to_hub else None,
    )

    if local_path is None:
        temp_dir.cleanup()


if __name__ == "__main__":
    typer.run(push_to_huggingface)
