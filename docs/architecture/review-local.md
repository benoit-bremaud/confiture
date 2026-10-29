# Local review — confiture (branch diff main...feat/4-piper-tts)

- Date: 2026-10-28
- Commit: 661ad5b (gate re-run on this head on 2026-10-29; the next commit only updates this report)
- Scope: branch diff `main...HEAD`
- Checks run: design · docs · security · correctness · containers (tests: no executable code, brick 0 waiver)
- Verdict: ship as-is after the fixes below · Must 1 (all fixed) · Should 4 (all fixed) · Nice 3 (issue)

## Pre-merge gate (head SHA 661ad5b)

| Step | Result |
|---|---|
| 1 Tests | N/A: docs, config and compose only (brick 0 waiver until the first PR with code) |
| 2 Coverage | N/A (same waiver) |
| 3 SonarQube | ✅ PASSED |
| 4 Secrets | ✅ gitleaks clean (`--log-opts=--all`) · no tracked .env · diff read: no IP, MAC or name added |
| 5 QA pass | ✅ smoke on the running system: Piper healthy, uid 1000, CapEff 0, loopback only; owner heard Yuki answers on the Nest; question to playback 2.2 s warm |

Other checks: Trivy config `deploy` (HIGH, CRITICAL): 0 · actionlint clean · `docker compose config` valid.

- Gate: **GREEN — push authorised**; merge after CI and the owner's approval

## PR review (Codex)

- `deploy/pi5/README.md:10` `[correctness]` (Codex P2) · `scp -r` into an existing folder nests it, updates kept the old compose · **fixed** in 661ad5b

## 🔴 Must Have

- `deploy/pi5/compose.yaml` `[docker]` · no Dependabot entry, no Trivy config scan · **fixed** in c4a3f8d (`.github/dependabot.yml`, `.github/workflows/docker-security.yml`)

## 🟡 Should Have

- `deploy/pi5/compose.yaml` `[docker]` · `cap_drop: [ALL]`, `no-new-privileges` · **fixed**, redeployed, healthy
- `deploy/pi5/README.md` `[docs][docker]` · digest on update, post-deploy checks, `mkdir data` ownership · **fixed**
- `docs/architecture/decisions/0006-…md` `[docs][security]` · option order, residual LAN risk · **fixed**
- `docs/architecture/traceability-matrix.md:23,25` `[docs]` · REQ-12/16 still `planned` · **fixed** (iteration 1)

## 🔵 Nice to Have

- `config/homeassistant/yuki_say.yaml` · `mode: queued` with `max: 3`; header: UI paste format, not `scripts.yaml` as is
- `deploy/pi5/compose.yaml` · `mem_limit`, `read_only` + tmpfs; `.env.example` for `PIPER_*`
- `PROJECT_LOG.md` · full `owner/repo#N` references

## ⚪ Disagree / Intentional

_None._

## Per-dimension summary

- Design: no over-engineering; one compose service, one script, one firewall rule.
- Docs: consistent across confiture, home-assistant and bb-homelab (issue numbers, MCDA totals, placeholders).
- Tests: no executable code in the diff.
- Security: Piper loopback only and non-root; 8123 open to the Nest only; residual LAN risk documented.
- Correctness: template path and languages verified live (`fr` for the agent, `fr_FR` for Piper).
