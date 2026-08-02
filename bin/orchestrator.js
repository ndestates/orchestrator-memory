#!/usr/bin/env node
'use strict';

/**
 * npm global shim for the orchestrator Python CLI.
 *
 * Always delegates to ``python -m orchestrator_cli`` — never shells out to an
 * ``orchestrator`` binary on PATH (that would be this same shim after
 * ``npm install -g`` and can recurse infinitely).
 *
 * postinstall installs the Python wheel/editable package; this script only
 * launches it.
 */

const { spawnSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const args = process.argv.slice(2);
const repoRoot = path.resolve(__dirname, '..');
const isWin = process.platform === 'win32';

function exitStatus(result) {
  return result.status !== null && result.status !== undefined ? result.status : 1;
}

function pythonCandidates() {
  if (isWin) {
    return ['py', 'python', 'python3'];
  }
  return ['python3', 'python'];
}

function findPython() {
  for (const cmd of pythonCandidates()) {
    const versionArgs = cmd === 'py' ? ['-3', '--version'] : ['--version'];
    const check = spawnSync(cmd, versionArgs, { encoding: 'utf8', shell: isWin });
    if (check.status === 0) {
      return cmd;
    }
  }
  return null;
}

function pythonModuleArgs(py) {
  return py === 'py' ? ['-3', '-m', 'orchestrator_cli'] : ['-m', 'orchestrator_cli'];
}

function runFromCheckout(py) {
  const src = path.join(repoRoot, 'src');
  const scripts = path.join(repoRoot, 'scripts');
  const env = { ...process.env };
  const sep = path.delimiter;
  const existing = env.PYTHONPATH ? `${env.PYTHONPATH}${sep}` : '';
  env.PYTHONPATH = `${src}${sep}${scripts}${sep}${existing}`.replace(/;{2,}|:{2,}/g, sep);
  return spawnSync(py, [...pythonModuleArgs(py), ...args], {
    stdio: 'inherit',
    env,
    cwd: repoRoot,
    shell: false,
  });
}

function runInstalled(py) {
  return spawnSync(py, [...pythonModuleArgs(py), ...args], {
    stdio: 'inherit',
    shell: false,
  });
}

function main() {
  const py = findPython();
  if (!py) {
    console.error(
      '[orchestrator] Python 3.10+ is required.\n' +
        '  Run: npm run install:cli\n' +
        '  Or:  pip install orchestrator\n' +
        '  Or:  bash scripts/install.sh --cli  /  .\\scripts\\install.ps1 -Cli'
    );
    process.exit(1);
  }

  const pyproject = path.join(repoRoot, 'pyproject.toml');
  const result = fs.existsSync(pyproject) ? runFromCheckout(py) : runInstalled(py);
  process.exit(exitStatus(result));
}

main();