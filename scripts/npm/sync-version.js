#!/usr/bin/env node
'use strict';

/**
 * Sync release mirrors from /VERSION (single source of truth):
 *   - package.json version
 *   - scripts/orchestrator-template-version (deployed stamp apps read)
 *
 * Run after every VERSION bump, before tag/release.
 */

const fs = require('fs');
const path = require('path');

const repoRoot = path.resolve(__dirname, '..', '..');
// Full identity, including pre-release labels (e.g. 1.9.0-pre.2). Users see this stamp.
const version = fs.readFileSync(path.join(repoRoot, 'VERSION'), 'utf8').trim().replace(/^v/, '');
if (!/^\d+\.\d+\.\d+(-[0-9A-Za-z.-]+)?$/.test(version)) {
  console.error(`Invalid VERSION: ${version}`);
  process.exit(1);
}

const pkgPath = path.join(repoRoot, 'package.json');
const pkg = JSON.parse(fs.readFileSync(pkgPath, 'utf8'));
pkg.version = version;
fs.writeFileSync(pkgPath, `${JSON.stringify(pkg, null, 2)}\n`);
console.log(`package.json version -> ${version}`);

const stampPath = path.join(repoRoot, 'scripts', 'orchestrator-template-version');
fs.writeFileSync(stampPath, `${version}\n`);
console.log(`scripts/orchestrator-template-version -> ${version}`);
