#!/usr/bin/env node
'use strict';

/**
 * Ensures the Python orchestrator CLI is installed after npm install.
 * - From a git checkout: pip install -e .
 * - From npm registry: pip install orchestrator==<VERSION>
 */

const { spawnSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const repoRoot = path.resolve(__dirname, '..', '..');
const isWin = process.platform === 'win32';
const force = process.argv.includes('--force');

function readVersion() {
  const versionFile = path.join(repoRoot, 'VERSION');
  if (fs.existsSync(versionFile)) {
    return fs.readFileSync(versionFile, 'utf8').trim();
  }
  const pkg = require(path.join(repoRoot, 'package.json'));
  return pkg.version;
}

function pipInvocation() {
  const attempts = isWin
    ? [{ cmd: 'py', args: ['-3', '-m', 'pip'] }, { cmd: 'python', args: ['-m', 'pip'] }]
    : [{ cmd: 'python3', args: ['-m', 'pip'] }, { cmd: 'python', args: ['-m', 'pip'] }];
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

function main() {
  if (process.env.ORCHESTRATOR_SKIP_PIP_INSTALL === '1') {
    console.log('[orchestrator] ORCHESTRATOR_SKIP_PIP_INSTALL=1 — skipping pip install');
    return;
  }

  const pip = pipInvocation();
  if (!pip) {
    console.warn(
      '[orchestrator] pip not found — Python CLI not installed.\n' +
        '  Install Python 3.10+ then run: npm run install:cli'
    );
    return;
  }

  if (!force) {
    const show = spawnSync(pip.cmd, [...pip.args, 'show', 'orchestrator'], {
      encoding: 'utf8',
      shell: isWin,
    });
    if (show.status === 0) {
      console.log('[orchestrator] Python package already installed — skipping (npm run install:cli -- --force to reinstall)');
      return;
    }
  }

  const version = readVersion();
  const pyproject = path.join(repoRoot, 'pyproject.toml');
  const spec = fs.existsSync(pyproject) ? '-e .' : `orchestrator==${version}`;

  console.log(`[orchestrator] Installing Python CLI (${spec}) ...`);
  const status = runPip(pip, ['install', spec]);
  if (status !== 0) {
    console.warn(`[orchestrator] pip install failed — install manually: pip install ${spec}`);
    return;
  }
  console.log('[orchestrator] Python CLI ready — run: orchestrator version');
}

main();