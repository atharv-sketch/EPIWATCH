#!/usr/bin/env python3
import os
import sys

base_dir = r"C:\Users\silverfang\epiwatch"

# Create directories
dirs = [
    "backend",
    "frontend", 
    "data",
    "notebooks"
]

for d in dirs:
    path = os.path.join(base_dir, d)
    os.makedirs(path, exist_ok=True)
    print(f"Created: {path}")

# Create files
files = [
    "backend/__init__.py",
    "backend/data_pipeline.py",
    "backend/model.py",
    "backend/api.py",
    "backend/requirements.txt",
    "data/.gitkeep",
    "notebooks/.gitkeep"
]

for f in files:
    path = os.path.join(base_dir, f)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, 'a').close()
    print(f"Created: {path}")

print("\nDirectory structure created successfully!")
