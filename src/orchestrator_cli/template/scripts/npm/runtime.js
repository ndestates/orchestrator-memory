#!/usr/bin/env node
'use strict';

/**
 * Shared npm/npx runtime checks for the Python CLI shim.
 * No auto-pip. Fail loud if python3 or orchestrator_cli is missing.
 */

const { spawnSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const RELEASE_ORG_REPO = 'ndestates/orchestrator-memory';

function isWin() {
  return process.platform === 'win32';
}

function repoRootFromHere() {
  return path.resolve(__dirname, '..', '..');
}

function readVersion(root) {
  const versionFile = path.join(root, 'VERSION');
  if (fs.existsSync(versionFile)) {
    return fs.readFileSync(versionFile, 'utf8').trim();
  }
  try {
    return require(path.join(root, 'package.json')).version;
  } catch (_err) {
    return '';
  }
}

function wheelUrl(version) {
  const ver = String(version || '').trim();
  return (
    `https://github.com/${RELEASE_ORG_REPO}/releases/download/v${ver}/` +
    `orchestrator-${ver}-py3-none-any.whl`
  );
}

function pipWheelLine(version) {
  return `python3 -m pip install --upgrade "${wheelUrl(version)}"`;
}

function pythonCandidates() {
  if (isWin()) {
    return ['py', 'python', 'python3'];
  }
  return ['python3', 'python'];
}

function findPython() {
  for (const cmd of pythonCandidates()) {
    const versionArgs = cmd === 'py' ? ['-3', '--version'] : ['--version'];
    const check = spawnSync(cmd, versionArgs, {
      encoding: 'utf8',
      shell: isWin(),
    });
    if (check.status === 0) {
      return cmd;
    }
  }
  return null;
}

function pythonDashCArgs(py, code) {
  return py === 'py' ? ['-3', '-c', code] : ['-c', code];
}

function pythonModuleArgs(py) {
  return py === 'py' ? ['-3', '-m', 'orchestrator_cli'] : ['-m', 'orchestrator_cli'];
}

function hasCheckout(root) {
  return (
    fs.existsSync(path.join(root, 'pyproject.toml')) &&
    fs.existsSync(path.join(root, 'src', 'orchestrator_cli'))
  );
}

function hasModule(py) {
  if (!py) {
    return false;
  }
  const check = spawnSync(py, pythonDashCArgs(py, 'import orchestrator_cli'), {
    encoding: 'utf8',
    shell: false,
  });
  return check.status === 0;
}

function missingPythonMessage() {
  return (
    '[orchestrator] Python 3.10+ is required (no auto-install).\n' +
    '  Install Python 3.10+, then retry: npx @ndestates/orchestrator …'
  );
}

function missingModuleMessage(version) {
  const ver = version || 'VERSION';
  return (
    '[orchestrator] Python package `orchestrator` is not installed (no auto-pip).\n' +
    `  ${pipWheelLine(ver)}\n` +
    '  Advanced / maintainer: uv tool install from the same wheel.\n' +
    '  Existing PATH installs of `orchestrator` are unchanged.'
  );
}

module.exports = {
  RELEASE_ORG_REPO,
  findPython,
  hasCheckout,
  hasModule,
  isWin,
  missingModuleMessage,
  missingPythonMessage,
  pipWheelLine,
  pythonModuleArgs,
  readVersion,
  repoRootFromHere,
  wheelUrl,
};
