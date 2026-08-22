const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const projectDir = r'C:\Users\silverfang\epiwatch';
process.chdir(projectDir);

console.log('=== Creating directories ===');
const dirs = ['backend', 'frontend', 'data', 'notebooks', '.github\\workflows'];
dirs.forEach(d => {
  if (!fs.existsSync(d)) {
    fs.mkdirSync(d, { recursive: true });
  }
});
console.log('✓ Directories created');

console.log('\n=== Creating files ===');
const files = [
  'backend\\__init__.py',
  'backend\\data_pipeline.py',
  'backend\\model.py',
  'backend\\api.py',
  'backend\\requirements.txt',
  'data\\.gitkeep',
  'notebooks\\.gitkeep',
];

files.forEach(f => {
  const dir = path.dirname(f);
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
  if (!fs.existsSync(f)) {
    fs.writeFileSync(f, '');
  }
});
console.log('✓ Files created');

console.log('\n=== Git Operations ===');

const commands = [
  ['git --no-pager status', '[1] git --no-pager status'],
  ['git add .', '[2] git add .'],
  ['git --no-pager commit -m "feat: initial project scaffold with CI pipeline" --author "Copilot <223556219+Copilot@users.noreply.github.com>"', '[3] git commit'],
  ['git --no-pager branch data-pipeline', '[4a] Creating data-pipeline branch'],
  ['git --no-pager push origin data-pipeline', '[4b] Pushing data-pipeline'],
  ['git --no-pager branch modeling', '[5a] Creating modeling branch'],
  ['git --no-pager push origin modeling', '[5b] Pushing modeling'],
  ['git --no-pager branch dashboard', '[6a] Creating dashboard branch'],
  ['git --no-pager push origin dashboard', '[6b] Pushing dashboard'],
  ['git --no-pager branch risk-map', '[7a] Creating risk-map branch'],
  ['git --no-pager push origin risk-map', '[7b] Pushing risk-map'],
  ['git --no-pager checkout main', '[8] Checkout main'],
  ['git --no-pager checkout data-pipeline', '[9] Checkout data-pipeline'],
  ['git --no-pager status', '[10] Final status'],
];

commands.forEach(([cmd, desc]) => {
  console.log(`\n${desc}`);
  try {
    const output = execSync(cmd, { encoding: 'utf-8' });
    console.log(output);
  } catch (error) {
    console.error('Error:', error.message);
    console.error(error.stdout || error.stderr);
  }
});

console.log('\n=== Setup Complete ===');
