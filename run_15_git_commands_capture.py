#!/usr/bin/env python3
import subprocess
import os
import sys

os.chdir('C:\\Users\\silverfang\\epiwatch')

commands = [
    'git --no-pager status',
    'git add .',
    'git --no-pager commit -m "feat: initial project scaffold with CI pipeline" --author "Copilot <223556219+Copilot@users.noreply.github.com>"',
    'git --no-pager branch data-pipeline',
    'git --no-pager branch modeling',
    'git --no-pager branch dashboard',
    'git --no-pager branch risk-map',
    'git --no-pager push origin data-pipeline',
    'git --no-pager push origin modeling',
    'git --no-pager push origin dashboard',
    'git --no-pager push origin risk-map',
    'git --no-pager checkout main',
    'git --no-pager checkout data-pipeline',
    'git --no-pager status --short',
    'git --no-pager rev-parse --abbrev-ref HEAD'
]

results = []

for i, cmd in enumerate(commands, 1):
    print(f'[{i}/15] Executing: {cmd}')
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        stdout = result.stdout
        stderr = result.stderr
        returncode = result.returncode
    except subprocess.TimeoutExpired:
        stdout = ''
        stderr = 'TIMEOUT'
        returncode = -1
    except Exception as e:
        stdout = ''
        stderr = str(e)
        returncode = -1
    
    results.append({
        'num': i,
        'command': cmd,
        'stdout': stdout,
        'stderr': stderr,
        'exit_code': returncode
    })
    print(f'Exit Code: {returncode}')

print('')
print('='*70)
print('COMMAND RESULTS')
print('='*70)
print('')

for r in results:
    print(f'--- COMMAND {r["num"]} ---')
    print(f'Command: {r["command"]}')
    print('STDOUT:')
    if r['stdout']:
        print(r['stdout'])
    else:
        print('(empty)')
    print('STDERR:')
    if r['stderr']:
        print(r['stderr'])
    else:
        print('(empty)')
    print(f'Exit Code: {r["exit_code"]}')
    print('')

print('='*70)
print('SUMMARY')
print('='*70)
print('')
print(f'Final Branch (Command 15): {results[14]["stdout"].strip()}')
print(f'Command 14 Output (status --short):')
print(results[13]['stdout'])
