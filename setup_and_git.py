#!/usr/bin/env python3
import os
import subprocess
import json
import sys

os.chdir('C:\\Users\\silverfang\\epiwatch')

# Step 1: Ensure directories exist
dirs = ['backend', 'frontend', 'data', 'notebooks', '.github/workflows']
for d in dirs:
    os.makedirs(d, exist_ok=True)

# Step 2: Ensure empty files exist
files = [
    'backend/__init__.py',
    'backend/data_pipeline.py',
    'backend/model.py',
    'backend/api.py',
    'backend/requirements.txt',
    'data/.gitkeep',
    'notebooks/.gitkeep'
]
for f in files:
    os.makedirs(os.path.dirname(f), exist_ok=True)
    open(f, 'a').close()

results = {}

# Command a: git status
result = subprocess.run(['git', '--no-pager', 'status'], capture_output=True, text=True)
results['a'] = result.stdout + result.stderr

# Command b: git add
result = subprocess.run(['git', 'add', '.'], capture_output=True, text=True)
results['b'] = result.stdout + result.stderr

# Command c: git commit
result = subprocess.run([
    'git', '--no-pager', 'commit', '-m', 'feat: initial project scaffold with CI pipeline',
    '--author', 'Copilot <223556219+Copilot@users.noreply.github.com>'
], capture_output=True, text=True)
results['c'] = result.stdout + result.stderr

# Command d: git branch data-pipeline
result = subprocess.run(['git', '--no-pager', 'branch', 'data-pipeline'], capture_output=True, text=True)
results['d'] = result.stdout + result.stderr

# Command e: git branch modeling
result = subprocess.run(['git', '--no-pager', 'branch', 'modeling'], capture_output=True, text=True)
results['e'] = result.stdout + result.stderr

# Command f: git branch dashboard
result = subprocess.run(['git', '--no-pager', 'branch', 'dashboard'], capture_output=True, text=True)
results['f'] = result.stdout + result.stderr

# Command g: git branch risk-map
result = subprocess.run(['git', '--no-pager', 'branch', 'risk-map'], capture_output=True, text=True)
results['g'] = result.stdout + result.stderr

# Command h: git push origin data-pipeline
result = subprocess.run(['git', '--no-pager', 'push', 'origin', 'data-pipeline'], capture_output=True, text=True)
results['h'] = result.stdout + result.stderr

# Command i: git push origin modeling
result = subprocess.run(['git', '--no-pager', 'push', 'origin', 'modeling'], capture_output=True, text=True)
results['i'] = result.stdout + result.stderr

# Command j: git push origin dashboard
result = subprocess.run(['git', '--no-pager', 'push', 'origin', 'dashboard'], capture_output=True, text=True)
results['j'] = result.stdout + result.stderr

# Command k: git push origin risk-map
result = subprocess.run(['git', '--no-pager', 'push', 'origin', 'risk-map'], capture_output=True, text=True)
results['k'] = result.stdout + result.stderr

# Command l: git checkout main
result = subprocess.run(['git', '--no-pager', 'checkout', 'main'], capture_output=True, text=True)
results['l'] = result.stdout + result.stderr

# Command m: git checkout data-pipeline
result = subprocess.run(['git', '--no-pager', 'checkout', 'data-pipeline'], capture_output=True, text=True)
results['m'] = result.stdout + result.stderr

# Command n: git status --short
result = subprocess.run(['git', '--no-pager', 'status', '--short'], capture_output=True, text=True)
results['n'] = result.stdout + result.stderr

# Command o: git rev-parse --abbrev-ref HEAD
result = subprocess.run(['git', '--no-pager', 'rev-parse', '--abbrev-ref', 'HEAD'], capture_output=True, text=True)
results['o'] = result.stdout + result.stderr

# Get final status
final_branch = results['o'].strip()
result = subprocess.run(['git', '--no-pager', 'status', '--short'], capture_output=True, text=True)
final_status_short = result.stdout + result.stderr

# Output machine-readable report
report = {
    'a': results['a'],
    'b': results['b'],
    'c': results['c'],
    'd': results['d'],
    'e': results['e'],
    'f': results['f'],
    'g': results['g'],
    'h': results['h'],
    'i': results['i'],
    'j': results['j'],
    'k': results['k'],
    'l': results['l'],
    'm': results['m'],
    'n': results['n'],
    'o': results['o'],
    'final_branch': final_branch,
    'final_status_short': final_status_short
}

print(json.dumps(report, indent=2))
