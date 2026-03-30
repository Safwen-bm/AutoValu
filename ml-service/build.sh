#!/bin/bash
echo "Running fix_data.py..."
python fix_data.py
echo "Running train_model.py..."
python train_model.py
echo "Build complete."
