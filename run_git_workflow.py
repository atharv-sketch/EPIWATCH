#!/usr/bin/env python3
import subprocess
import os
import sys

os.chdir('C:\\Users\\silverfang\\epiwatch')

commands = [
    'git --no-pager status -sb',
    'git add .',
    'git commit -m "feat: initial project scaffold with CI pipeline" -m "Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"',
    'git checkout -b data-pipeline || git checkout data-pipeline',
    'git push -u origin data-pipeline',
    'git checkout main || git checkout master',
    'git checkout -b modeling || git checkout modeling',
    'git push -u origin modeling',
    'git checkout main || git checkout master',
    'git checkout -b dashboard || git checkout dashboard',
    'git push -u origin dashboard',
    'git checkout main || git checkout master',
    'git checkout -b risk-map || git checkout risk-map',
    'git push -u origin risk-map',
    'git checkout main || git checkout master',
    'git checkout data-pipeline',
    'git --no-pager branch --show-current',
    'git --no-pager status -sb'
]

for i, cmd in enumerate(commands, 1):
    print(f'\n{"="*50}')
    print(f'COMMAND {i}: {cmd}')
    print(f'{"="*50}')
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        output = result.stdout if result.stdout else result.stderr
        print(output if output else '[No output]')
        if result.returncode != 0 and i == 3:  # Special case for commit
            print(f'[Exit Code: {result.returncode} - Commit may have failed due to no changes]')
    except subprocess.TimeoutExpired:
        print('[Command timeout]')
    except Exception as e:
        print(f'[Error: {e}]')

print(f'\n{"="*50}')
print('All commands completed')
print(f'{"="*50}')
