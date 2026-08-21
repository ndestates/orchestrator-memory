#!/usr/bin/env node
'use strict';

/**
 * npm / npx shim for the orchestrator Python CLI.
 *
 * Always delegates to ``python -m orchestrator_cli`` — never shells out to an
 * ``orchestrator`` binary on PATH (that would be this same shim after
 * ``npm install -g`` and can recurse infinitely).
 *
 * Does not auto-pip. Factory checkout uses PYTHONPATH. Published package
 * requires ``orchestrator_cli`` already installed (GitHub Release wheel).
 */

const { spawnSync } = require('child_process');
const path = require('path');
const runtime = require('../scripts/npm/runtime');

const args = process.argv.slice(2);
const repoRoot = path.resolve(__dirname, '..');

function exitStatus(result) {
  return result.status !== null && result.status !== undefined ? result.status : 1;
}

function runFromCheckout(py) {
  const src = path.join(repoRoot, 'src');
  const scripts = path.join(repoRoot, 'scripts');
  const env = { ...process.env };
  const sep = path.delimiter;
  const existing = env.PYTHONPATH ? `${env.PYTHONPATH}${sep}` : '';
  env.PYTHONPATH = `${src}${sep}${scripts}${sep}${existing}`.replace(/;{2,}|:{2,}/g, sep);
  return spawnSync(py, [...runtime.pythonModuleArgs(py), ...args], {
    stdio: 'inherit',
    env,
    cwd: repoRoot,
    shell: false,
  });
}

function runInstalled(py) {
  return spawnSync(py, [...runtime.pythonModuleArgs(py), ...args], {
    stdio: 'inherit',
    shell: false,
  });
}

function main() {
  const py = runtime.findPython();
  if (!py) {
    console.error(runtime.missingPythonMessage());
    process.exit(1);
  }

  if (runtime.hasCheckout(repoRoot)) {
    const result = runFromCheckout(py);
    process.exit(exitStatus(result));
  }

  if (!runtime.hasModule(py)) {
    console.error(runtime.missingModuleMessage(runtime.readVersion(repoRoot)));
    process.exit(1);
  }

  process.exit(exitStatus(runInstalled(py)));
}

main();
