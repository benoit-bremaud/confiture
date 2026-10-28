# Local review — confiture (branch diff main...HEAD)

Pre-push review of the first push of the repository (public), run in `--push` mode.

- Date: 2026-10-28
- Commit: 3c9410b
- Scope: branch diff `main...HEAD` (`docs/1-publish-phase-1-conception`, issue #1)
- Checks run: docs · security · correctness (design, tests and containers not applicable: no
  application code, no Dockerfile)
- Verdict: ship (push) · Must 1 resolved · Should 9 resolved · Nice 4 open

## Pre-merge gate (head SHA 3c9410b)

| Step | Result |
|---|---|
| 1 Tests | ⚠️ not applicable: no code, no test suite yet |
| 2 Coverage | ⚠️ not applicable (tests, docs counter) |
| 3 SonarQube | ✅ PASSED (local `localhost:9000`, project `confiture`): 0 bugs, 0 vulnerabilities, 0 code smells, 0 hotspots |
| 4 Secrets | ✅ gitleaks clean on full history (default + personal-data rules) · `.env.example` only · ✅ diff read after the second history scrub: nothing sensitive (0 matches left) |
| 5 QA pass | skipped (`--push` mode, no running product in the diff) |

- Gate: **GREEN for push**. Steps 1–2: owner waiver 2026-10-28 (MCDA 450/500), valid until
  the first PR that adds executable code; from then on tests and coverage are
  mandatory. Step 3 runs on every local CI run (owner rule 2026-10-28, agents-skills#159). Meanwhile `shellcheck scripts/*.sh` runs locally: one SC2016 info at
  `scripts/configure-sd.sh:46`, a false positive (the single quotes sit inside double quotes).

## Resolution (2026-10-28)

- Must: second history scrub with placeholders; full-history grep and gitleaks: 0 left.
- Should: gitleaks regexes widened (dash MACs, 172.16/12), workflow hardened (job permissions,
  no artifact upload, project config); README, glossary, ID ranges, use cases and
  traceability matrix updated; `num_predict` deviation and the prompt-is-not-a-boundary note
  documented in the Modelfile.
- Nice: left open for a later brick.

## 🔴 Must Have

- `PROJECT_LOG.md:113-114,115-116,153,157,171,195,245-246` `[security][docs]` · Residual
  personal and network data in a public repo: LAN map by last octet, `.216`/`.174` octets,
  projector model string, work PC hostname and employer name ("VEV PC"), "my daughter's Mac",
  the work network range `10.6.x.x`; also the child's gender in
  `docs/architecture/specs/voice-assistant-needs.md:83-84,94` · Second history scrub with
  placeholders (`<pi5-ip>`, "work PC", "a family laptop", "an outside network", "their").

## 🟡 Should Have

- `.gitleaks.toml:8,13` `[security]` · MAC rule misses the dash format, private-IP rule misses
  the 172.16/12 range · Widen both regexes.
- `.github/workflows/secret-scan.yml:12-14` `[security]` · `pull-requests: write` at workflow
  level; a found leak may be uploaded as a public artifact · Move permissions to the job, set
  `GITLEAKS_ENABLE_UPLOAD_ARTIFACT: false`, `GITLEAKS_CONFIG: .gitleaks.toml`.
- `README.md:13-17` `[docs]` · Architecture still "draft", brain host "to decide" · Point to
  ADR-0004/0005 and REQ-15/16.
- `docs/architecture/traceability-matrix.md:16-20` `[docs]` · Only REQ-4 traced; REQ-1..20,
  NFR-1, ADRs and the UC1 sequence missing · Add rows.
- `docs/architecture/glossary.md:6,16` `[docs]` · "Brain … optional LLM", "Satellite =
  microphone and speaker" contradict ADR-0004 and REQ-12/15/16 · Redefine.
- `docs/architecture/README.md:11-12`, `specs/voice-assistant-needs.md:5` `[docs]` · Stale ID
  ranges (NFR-1..4, REQ-1..8) · Update to NFR-1..5, REQ-1..20.
- `docs/architecture/specs/voice-assistant-use-cases.md:12,45` `[docs]` · Q7 said open (it is
  ADR-0003); barge-in extension not marked iteration 2 (REQ-17) · Update.
- `config/ollama/yuki.Modelfile:11-12` `[correctness]` · `num_predict 160` ≈ 20 s exceeds
  NFR-5 (15 s) · Lower to about 120 or document the deviation.
- `config/ollama/yuki.Modelfile` `[security]` · Child safety rests on the prompt only; a child
  can say "ignore your rules" · State that the prompt is not a security boundary; ADR-0002
  per-satellite policy stays the control.

## 🔵 Nice to Have

- `scripts/configure-sd.sh:22,42-43,6` `[security]` · `ssh_pwauth: true` stays on; Wi-Fi PSK
  left unescaped on the boot partition; default path contains the local user name.
- `PROJECT_LOG.md` (hostnames `hp-probook`, `nest-mini-sejour`, `owner-phone`, `pitest`,
  `espectre-01`) `[security]` · Map devices, not people · Optional placeholders.
- `docs/architecture/specs/voice-assistant-needs.md:100-120` `[docs]` · Q4 decided (Yuki) but
  not struck through; facts bullet badly wrapped.
- `docs/architecture/decisions/0004-*.md:38` `[docs]` · Sensitivity totals not labelled by option.

## ⚪ Disagree / Intentional

- `docs/architecture/specs/voice-assistant-needs.md:62` `[security]` · "(about 7)" kept:
  owner decision K2 (MCDA 450, 2026-10-28) — the approximate age drives the speech-to-text
  choice.
- `config/ollama/yuki.Modelfile:14,35` `[security]` · "un papa et ses enfants": generic family
  structure needed by the persona; no name, no age. Owner to confirm.
- Commit author email: already public on the owner's other public repositories.

## Per-dimension summary

- Design: not applicable (no code) · Docs: stale README, glossary and matrix after the ADRs ·
  Tests: not applicable · Security: no secret; residual personal data (Must) and gitleaks rule
  gaps · Correctness: `num_predict` vs NFR-5.
