# GitHub Codespaces ♥️ Jupyter Notebooks



# PRNU Forensic Analysis - Phase 1 Complete

## 🎯 Overview
A deep learning solution for camera device fingerprinting using Photo Response Non-Uniformity (PRNU) analysis. This system can determine with high accuracy whether two images were captured by the same camera device.

## ✅ Phase 1 Status: COMPLETE
All core components have been successfully implemented and tested:

- **Data Pipeline**: Triplet generation for training
- **Neural Network**: ResNet50-based PRNU model  
- **Training System**: Complete pipeline with validation
- **Inference Tool**: Production-ready comparison script
- **Documentation**: Comprehensive logging and guides

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Prepare Data
Place your device image folders in `data/raw/`:
```
data/raw/
├── device_01/
├── device_02/
└── device_03/
```

### 3. Generate Training Data
```bash
python scripts/generate_triplets.py --data_dir data/raw --output_dir data/processed
```

### 4. Train Model
```bash
python src/train.py --train_json_path data/processed/train_triplets.json --val_json_path data/processed/val_triplets.json
```

### 5. Compare Images
```bash
python src/inference.py --model_path models/best_model.pth --image1_path img1.jpg --image2_path img2.jpg
```

## 📊 Performance Targets
- **ROC-AUC**: > 0.95
- **EER**: < 5%

## 📁 Project Structure
See `PHASE1_SUMMARY.md` for complete file structure and component details.

## 🔬 Scientific Validation
This implementation follows rigorous ML engineering practices with proper train/validation methodology, standard evaluation metrics, and reproducible experiments.

---
**Status**: Phase 1 Complete ✅ | **Next**: Production Deployment
