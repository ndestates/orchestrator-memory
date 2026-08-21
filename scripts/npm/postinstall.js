#!/usr/bin/env node
'use strict';

/**
 * npm postinstall — print the user path. Does **not** auto-pip.
 *
 * Explicit maintainer escape: ``npm run install:cli`` (``--force``) still
 * runs ``pip install -e .`` in a factory checkout only.
 */

const { spawnSync } = require('child_process');
const runtime = require('./runtime');

const repoRoot = runtime.repoRootFromHere();
const isWin = runtime.isWin();
const force = process.argv.includes('--force');

function pipInvocation() {
  const attempts = isWin
    ? [
        { cmd: 'py', args: ['-3', '-m', 'pip'] },
        { cmd: 'python', args: ['-m', 'pip'] },
      ]
    : [
        { cmd: 'python3', args: ['-m', 'pip'] },
        { cmd: 'python', args: ['-m', 'pip'] },
      ];
  for (const { cmd, args } of attempts) {
    const check = spawnSync(cmd, [...args, '--version'], { encoding: 'utf8', shell: isWin });
    if (check.status === 0) {
      return { cmd, args };
    }
  }
  return null;
}

function runPip(pip, subArgs) {
  const extra = ['--upgrade'];
  if (process.env.ORCHESTRATOR_PIP_USER === '1') {
    extra.push('--user');
  }
  const result = spawnSync(pip.cmd, [...pip.args, ...subArgs, ...extra], {
    stdio: 'inherit',
    shell: isWin,
    cwd: repoRoot,
  });
  return result.status !== null && result.status !== undefined ? result.status : 1;
}

function printUserHint(version) {
  console.log('[orchestrator] npm/npx shim ready — no auto-pip.');
  console.log('  Daily:  npx @ndestates/orchestrator <command>');
  console.log('  Files:  npx @ndestates/orchestrator init|upgrade   (explicit only)');
  console.log(`  If python -m orchestrator_cli fails:\n    ${runtime.pipWheelLine(version)}`);
}

function main() {
  const version = runtime.readVersion(repoRoot);

  if (force && runtime.hasCheckout(repoRoot)) {
    const pip = pipInvocation();
    if (!pip) {
      console.warn(runtime.missingPythonMessage());
      printUserHint(version);
      return;
    }
    console.log('[orchestrator] install:cli --force: pip install -e . (factory checkout)');
    const status = runPip(pip, ['install', '-e', '.']);
    if (status !== 0) {
      console.warn('[orchestrator] pip install -e . failed — use the wheel line instead.');
      printUserHint(version);
      return;
    }
    console.log('[orchestrator] editable Python CLI ready — orchestrator version');
    return;
  }

  printUserHint(version);
}

main();
