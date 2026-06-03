# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to
[Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- CI pipeline (`uv sync --locked` → ruff → format → mypy → pytest) on push and PR.
- MIT `LICENSE` + SPDX metadata; ruff + mypy + mutmut config; pinned interpreter.
- `GET /healthz` liveness/readiness endpoint.
- `AGENTS.md`, `ARCHITECTURE.md` (Mermaid), ADR 0001 (Monte-Carlo vs closed form), and
  vendored-asset provenance (`static/VENDORED.md` + third-party licenses).

### Changed
- Request DTOs reject unknown fields (`extra="forbid"`) and validate the `deadline` date.
- LLM requests are bounded (timeout + retries) and log on graceful fallback instead of
  swallowing the error.
- The JSON store raises clear errors on a corrupt file / unknown collection and serializes
  writes under a reentrant lock.

### Fixed
- Engine guards: `update_posterior(k>n)`, `urgency_factor(horizon=0)`, `validate_strategy([])`,
  and `min_volume_for_threshold` now fail loudly or report infeasibility instead of returning
  a silently-wrong result.

## [0.1.0] - 2026-06-03

### Added
- Monte-Carlo life-planning engine — `outcome = probability × volume`: Beta-Binomial funnels,
  conjugate Bayesian updating, a cross-goal priority queue, a digital-twin persona layer, a
  FastAPI app, and a static dashboard.
