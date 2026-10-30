# Local review — confiture (fix/26-satellite-deaf-after-reply)

Pre-push review of issue #26, satellite on the host network; the Should findings were fixed on the branch.

- Date: 2026-10-30
- Commit: 14fa503 (review run), fixes in the next commit
- Scope: branch diff main...HEAD (`deploy/pi5/compose.yaml`, `deploy/pi5/README.md`, `04-sequence-ask-by-voice.md`, `PROJECT_LOG.md`)
- Checks run: containers (`docker-auditor`) · security · correctness (compose and docs only: design, docs and tests audits proportionally skipped, no code changed)
- Verdict: ship · Must 0 · Should 3 (fixed) · Nice 2

## Pre-merge gate (head SHA of the fix commit)
| Step | Result |
|---|---|
| 1 Tests | ✅ nest-relay 18 passed (unchanged code); `docker compose config -q` valid |
| 2 Coverage | n/a: no code changed |
| 3 SonarQube | ⚠️ not run: compose and Markdown only |
| 4 Secrets | ✅ gitleaks clean (origin/main..HEAD) · only `.env.example` tracked · diff read: loopback addresses only |
| 5 QA pass | ✅ spoken test on the Pi 5 by the owner: two chained questions, wake word back 6 s after the reply, nest-relay spoke both; `ss` 6053/6055 on 127.0.0.1 |
- Gate: **GREEN** (SonarQube n/a, staging waiver)

## 🔴 Must Have
_None._

## 🟡 Should Have
- `deploy/pi5/compose.yaml:90` `[security]` · host networking: any local process reaches the unauthenticated 6055 · fixed: comment states it
- `deploy/pi5/compose.yaml:90` `[security]` · fails open if an image bump ignores `HOST`/`PERIPHERAL_HOST` · fixed: `ss -ltn` check after every bump in compose comment and README
- `deploy/pi5/compose.yaml:94` `[docs]` · `MAC_ADDRESS` is an identifier only · fixed: comment reworded

## 🔵 Nice to Have
- `PROJECT_LOG.md` `[docs]` · record why the ufw rule was rejected · done in the #26 entry
- `deploy/pi5/README.md` `[docs]` · no bridge wording left · checked

## ⚪ Disagree / Intentional
_None._

## Per-dimension summary
- Containers: hardening kept, loopback binds verified on the Pi · Security: no new exposure · Correctness: compose valid, spoken test green
