import argparse
import json
import logging
import sys
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import torchvision.transforms as transforms
from scipy.interpolate import interp1d
from scipy.optimize import brentq
from sklearn.metrics import roc_auc_score, roc_curve
from torch.utils.data import DataLoader

# Add src to path and import our components
sys.path.append(str(Path(__file__).resolve().parent))
from dataset import PRNUDataset
from model import PRNUModel
from utils import calculate_sha256

def setup_logging(log_path: Path):
    """Sets up a logger to output to both console and a file."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] - %(message)s",
        handlers=[logging.FileHandler(log_path), logging.StreamHandler(sys.stdout)],
    )
    logging.info(f"Logging initialized. Log file at: {log_path}")

def calculate_eer(y_true, y_scores):
    """Calculates the Equal Error Rate (EER)."""
    fpr, tpr, _ = roc_curve(y_true, y_scores, pos_label=1)
    eer = brentq(lambda x: 1.0 - x - interp1d(fpr, tpr)(x), 0.0, 1.0)
    return eer * 100

def train_epoch(model, dataloader, optimizer, triplet_loss, bce_loss, device):
    """Trains the model for one epoch."""
    model.train()
    total_loss = 0.0
    for anchor, positive, negative in dataloader:
        anchor, positive, negative = (t.to(device) for t in [anchor, positive, negative])
        optimizer.zero_grad()
        pos_similarity, anchor_sig, pos_sig = model(anchor, positive)
        neg_similarity, _, neg_sig = model(anchor, negative)
        
        loss_triplet = triplet_loss(anchor_sig, pos_sig, neg_sig)
        loss_bce = (
            bce_loss(pos_similarity, torch.ones_like(pos_similarity)) +
            bce_loss(neg_similarity, torch.zeros_like(neg_similarity))
        ) / 2
        
        combined_loss = loss_triplet + loss_bce
        combined_loss.backward()
        optimizer.step()
        total_loss += combined_loss.item()
        
    return total_loss / len(dataloader)

def validate_epoch(model, dataloader, triplet_loss, bce_loss, device):
    """Validates the model for one epoch."""
    model.eval()
    total_loss = 0.0
    all_targets, all_scores = [], []
    with torch.no_grad():
        for anchor, positive, negative in dataloader:
            anchor, positive, negative = (t.to(device) for t in [anchor, positive, negative])
            pos_similarity, anchor_sig, pos_sig = model(anchor, positive)
            neg_similarity, _, neg_sig = model(anchor, negative)

            loss_triplet = triplet_loss(anchor_sig, pos_sig, neg_sig)
            loss_bce = (
                bce_loss(pos_similarity, torch.ones_like(pos_similarity)) +
                bce_loss(neg_similarity, torch.zeros_like(neg_similarity))
            ) / 2
            
            total_loss += (loss_triplet + loss_bce).item()
            
            all_scores.extend(pos_similarity.cpu().numpy().flatten())
            all_scores.extend(neg_similarity.cpu().numpy().flatten())
            all_targets.extend([1] * len(pos_similarity))
            all_targets.extend([0] * len(neg_similarity))

    avg_loss = total_loss / len(dataloader)
    roc_auc = roc_auc_score(all_targets, all_scores)
    eer = calculate_eer(all_targets, all_scores)
    return avg_loss, roc_auc, eer

def save_checkpoint(model, optimizer, epoch, metrics, filepath: Path):
    """Saves a model checkpoint dictionary."""
    torch.save({
        'epoch': epoch,
        'model_state_dict': model.state_dict(),
        'optimizer_state_dict': optimizer.state_dict(),
        'metrics': metrics
    }, filepath)
    logging.info(f"Checkpoint saved to {filepath}")

def main():
    """Main refactored training function with forensic manifest generation."""
    parser = argparse.ArgumentParser(description="Train PRNU forensic model with auditable manifest generation.")
    parser.add_argument("--train_json_path", type=str, required=True, help="Path to training triplets JSON.")
    parser.add_argument("--val_json_path", type=str, required=True, help="Path to validation triplets JSON.")
    parser.add_argument("--output_dir", type=str, default="models", help="Root directory to save training runs.")
    parser.add_argument("--epochs", type=int, default=50, help="Number of training epochs.")
    parser.add_argument("--batch_size", type=int, default=16, help="Batch size for training.")
    parser.add_argument("--learning_rate", type=float, default=1e-4, help="Initial learning rate.")
    args = parser.parse_args()

    # --- 1. Setup Run Environment and Manifest ---
    run_timestamp = time.strftime("%Y%m%d_%H%M%S")
    run_output_dir = Path(args.output_dir) / f"run_{run_timestamp}"
    run_output_dir.mkdir(parents=True, exist_ok=True)

    setup_logging(run_output_dir / "_log.txt")
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logging.info(f"Starting new training run: {run_timestamp}")
    logging.info(f"Output will be saved to: {run_output_dir}")
    logging.info(f"Using device: {device}")

    # --- 2. Define and Log All Parameters ---
    train_params = {
        "command_line_args": vars(args),
        "run_timestamp": run_timestamp,
        "pytorch_version": torch.__version__,
        "device": str(device),
        "loss_functions": {
            "triplet_margin_loss": {"margin": 1.0},
            "binary_cross_entropy_loss": {}
        },
        "optimizer": {
            "type": "AdamW",
            "weight_decay": 1e-5
        },
        "scheduler": {
            "type": "CosineAnnealingLR",
            "T_max": args.epochs
        },
        "transforms": {
            "resize": [224, 224],
            "normalization_mean": [0.485, 0.456, 0.406],
            "normalization_std": [0.229, 0.224, 0.225]
        }
    }

    manifest = {"training_parameters": train_params, "inputs": [], "outputs": []}

    # --- 3. Verify and Hash Inputs ---
    logging.info("Verifying and hashing input data...")
    train_json_path = Path(args.train_json_path)
    val_json_path = Path(args.val_json_path)
    manifest['inputs'].append({"path": str(train_json_path), "sha256": calculate_sha256(train_json_path)})
    manifest['inputs'].append({"path": str(val_json_path), "sha256": calculate_sha256(val_json_path)})

    # --- 4. Initialize Components ---
    transform = transforms.Compose([
        transforms.Resize(train_params['transforms']['resize']),
        transforms.ToTensor(),
        transforms.Normalize(mean=train_params['transforms']['normalization_mean'], 
                           std=train_params['transforms']['normalization_std'])
    ])
    
    train_dataset = PRNUDataset(str(train_json_path), transform=transform)
    val_dataset = PRNUDataset(str(val_json_path), transform=transform)
    train_loader = DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True, num_workers=4, pin_memory=True)
    val_loader = DataLoader(val_dataset, batch_size=args.batch_size, shuffle=False, num_workers=4, pin_memory=True)

    model = PRNUModel().to(device)
    triplet_loss = nn.TripletMarginLoss(margin=train_params['loss_functions']['triplet_margin_loss']['margin'])
    bce_loss = nn.BCELoss()
    optimizer = optim.AdamW(model.parameters(), lr=args.learning_rate, weight_decay=train_params['optimizer']['weight_decay'])
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs)

    # --- 5. Training Loop ---
    best_roc_auc = 0.0
    training_history = []
    logging.info("Starting training loop...")
    for epoch in range(args.epochs):
        logging.info(f"\n--- Epoch {epoch + 1}/{args.epochs} ---")
        train_loss = train_epoch(model, train_loader, optimizer, triplet_loss, bce_loss, device)
        val_loss, roc_auc, eer = validate_epoch(model, val_loader, triplet_loss, bce_loss, device)
        scheduler.step()

        metrics = {'train_loss': train_loss, 'val_loss': val_loss, 'roc_auc': roc_auc, 'eer': eer}
        training_history.append({'epoch': epoch + 1, **metrics})
        logging.info(f"Validation Metrics: ROC-AUC={roc_auc:.4f}, EER={eer:.2f}%, Loss={val_loss:.4f}")

        if roc_auc > best_roc_auc:
            best_roc_auc = roc_auc
            best_model_path = run_output_dir / "best_model.pth"
            save_checkpoint(model, optimizer, epoch + 1, metrics, best_model_path)

    # --- 6. Finalize and Hash Outputs ---
    logging.info("\nTraining complete. Finalizing run artifacts...")
    
    history_path = run_output_dir / "training_history.json"
    with open(history_path, 'w') as f:
        json.dump(training_history, f, indent=4)
        
    manifest['outputs'].append({"path": str(history_path), "sha256": calculate_sha256(history_path)})
    
    # Check if a best model was saved and add it to the manifest
    if 'best_model_path' in locals() and best_model_path.exists():
        manifest['outputs'].append({"path": str(best_model_path), "sha256": calculate_sha256(best_model_path)})
    else:
        logging.warning("No best model was saved during the run.")

    # --- 7. Save the Final Manifest ---
    manifest_path = run_output_dir / "_manifest.json"
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=4)
        
    logging.info(f"Run manifest saved to {manifest_path}")
    logging.info(f"--- Run {run_timestamp} Finished ---")

if __name__ == "__main__":
    main()

