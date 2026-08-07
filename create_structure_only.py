#!/usr/bin/env python3
import os
import sys

os.chdir(r"C:\Users\silverfang\epiwatch")

# 1) Create directories
print("=== Creating directories ===")
dirs = ["backend", "frontend", "data", "notebooks"]
for d in dirs:
    os.makedirs(d, exist_ok=True)
    print(f"✓ {d}")

# Also check if .github\workflows exists
os.makedirs(".github\\workflows", exist_ok=True)
print("✓ .github\\workflows")

# 2) Create files
print("\n=== Creating files ===")
files = [
    "backend\\__init__.py",
    "backend\\data_pipeline.py",
    "backend\\model.py",
    "backend\\api.py",
    "backend\\requirements.txt",
    "data\\.gitkeep",
    "notebooks\\.gitkeep",
]
for f in files:
    os.makedirs(os.path.dirname(f), exist_ok=True)
    open(f, 'a').close()
    print(f"✓ {f}")

print("\n=== Setup Complete ===")

# List the created structure
print("\n=== Directory structure ===")
for root, dirs, files in os.walk("."):
    level = root.replace(".", "").count(os.sep)
    indent = " " * 2 * level
    print(f"{indent}{os.path.basename(root)}/")
    subindent = " " * 2 * (level + 1)
    for file in files:
        if not file.startswith("."):
            print(f"{subindent}{file}")
