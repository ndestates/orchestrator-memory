# Technology Stack

> Fill with verifiable evidence only (manifest files, Docker/DDEV config, actual imports, test config). Load `.claude/project-manifest.yaml` first for hints; use `references/stack-detection.md` if ambiguous.

## Core Sections (Required)

### 1) Runtime Summary

| Area | Value | Evidence |
|------|-------|----------|
| Primary language | [language] | [manifest / source paths] |
| Runtime + version | [version] | [.nvmrc, go.mod, pyproject.toml, Docker FROM, ddev config] |
| Package manager | [npm/pip/composer/go mod/etc] | [lockfiles] |
| Module/build system | [description] | [build files] |

### 2) Production Frameworks and Dependencies

List only high-impact production dependencies.

| Dependency | Version | Role in system | Evidence |
|------------|---------|----------------|----------|
| [name] | [ver] | [role] | [file] |

### 3) Development Toolchain

| Tool | Purpose | Evidence |
|------|---------|----------|
| [linter/formatter/test runner] | [purpose] | [config file] |

### 4) Infrastructure and Runtime

| Component | Details | Evidence |
|-----------|---------|----------|
| Local runtime | [DDEV/docker-compose/local] | [config] |
| CI/CD | [platform] | [.github/workflows, etc.] |
| Containers | [if any] | [Dockerfile, compose] |

### 5) Environment and Secrets

- Required env vars: [list pattern only — never real values]
- Secret loading: [.env, config services, credential managers]
- Evidence: [files]

## Optional Deep-Dive

Add when repo complexity justifies (e.g. multi-service mesh, detailed API surface, polyglot modules).

## Evidence

- [list concrete paths used to populate this doc]