# Local review — confiture (chore/19-pi5-disk-housekeeping)

Pre-push review of issue #19, Pi 5 disk housekeeping; every Should finding was fixed on the branch in the commit after the review.

- Date: 2026-10-30
- Commit: eed13a1 (review run), fixes in the next commit
- Scope: branch diff main...HEAD (6 files: `deploy/pi5/docker-housekeeping.{sh,service,timer}`, `deploy/pi5/disk-space-alert.yaml`, `deploy/pi5/README.md`, `PROJECT_LOG.md`)
- Checks run: design · docs · security · correctness (tests: no test file in scope, the diff holds no code under test; containers: compose untouched, `docker-auditor` skipped)
- Verdict: ship after the Should fixes · Must 0 · Should 5 · Nice 4

## Pre-merge gate (head SHA of the fix commit)

| Step | Result |
|---|---|
| 1 Tests | ✅ 101 unit (pytest, `pi3cam/`) · shellcheck clean on the new script · `systemd-analyze verify` clean on both units (the only message is the script path, not installed locally) · `systemd-analyze calendar` resolves the timer to Sunday 04:00 |
| 2 Coverage | tests 93 % lines overall, 100 % on `domain.py` / `adapters.py` (`main.py` excluded as wiring; floor 80) · docs ~95 % of the new surface per `doc-auditor`, 100 % after the fixes (floor 90) |
| 3 SonarQube | ✅ PASSED (new coverage 99.1 %, 0 new violations, 0 % duplication) |
| 4 Secrets | ✅ gitleaks clean (`--log-opts=--all`) · no tracked .env (only `.env.example`) · diff read: no IP, MAC, host, user or family name, only `<user>`, `<pi5-host>`, `<notify_service>` placeholders |
| 5 QA pass | ✅ smoke on the Pi 5 (2026-10-30, owner's `sudo`): timer enabled, next run Sunday 2026-11-01 04:00; manual run finished, journal `freed 0 MiB on /` (the card had been pruned by hand that morning); `docker system df`: 13 images all in use, 0 B reclaimable, 2 unused volumes left untouched (4 MB); disk 80 % · ⚠️ the Home Assistant automation is pasted by the owner in the UI (placeholder notify service), tested with "Run actions" |
- Gate: **GREEN — merge authorised** once the automation is saved in Home Assistant

## 🔴 Must Have
_None._

## 🟡 Should Have
- `deploy/pi5/disk-space-alert.yaml:22` `[design|security]` · both levels share `notification_id`, so a late "warning" (10 min `for:`) overwrites an earlier "critical" · `notification_id: "pi5_disk_space_{{ trigger.id }}"`
- `deploy/pi5/disk-space-alert.yaml:10,16,25,30` `[design]` · the sensor entity id is written four times and the messages re-read the state instead of reporting the value that fired · `{{ trigger.to_state.state }}` in both messages, entity id left in the two triggers only
- `deploy/pi5/disk-space-alert.yaml:2` `[docs]` · the comment "named after the mount point" does not match the entity id used · say the id is the usual default for `/` and where to adjust it
- `deploy/pi5/README.md:55` `[docs]` · "the only thing it could remove" is overstated: no rollback image is kept either · reword, state the re-pull consequence
- `deploy/pi5/docker-housekeeping.service:1` `[docs]` · no WHY: runs as root on purpose (Docker socket), launched by the timer · two-line header comment

## 🔵 Nice to Have
- `deploy/pi5/disk-space-alert.yaml:27` `[security]` · `notify.<notify_service>` is refused by Home Assistant if pasted unchanged · ship the block commented out (applied: cheap, keeps the file pasteable)
- `deploy/pi5/docker-housekeeping.service:7` `[security]` · a oneshot has no start timeout, a hung Docker daemon keeps the job open · `TimeoutStartSec=30min` (applied)
- `deploy/pi5/docker-housekeeping.sh` `[correctness]` · committed as 100644 although `install -m 0755` fixes it on the Pi · `git update-index --chmod=+x` (applied)
- `deploy/pi5/disk-space-alert.yaml:8` `[security]` · `numeric_state` fires on crossing only: a disk already above 85 % at HA start raises nothing · accepted for now; the weekly prune and the 95 % step cover it (not applied)

## ⚪ Disagree / Intentional
- `deploy/pi5/docker-housekeeping.sh` `[design]` · the wrapper could be two `ExecStart=` lines · kept: the `df` difference logs what really changed on disk, Docker's "reclaimed" figure is off with shared layers
- `deploy/pi5/docker-housekeeping.sh:9` `[design]` · `docker builder prune` with no known build on the Pi 5 · kept: free, and bb-homelab may build
- `README.md:47` + timer `[design]` · manual prune in the update procedure and a weekly timer · recorded MCDA decision (PROJECT_LOG 2026-10-30, 480/500)
- `docker-housekeeping.service` `[security]` · no sandboxing directives · anything holding the Docker socket is root-equivalent, they would add nothing

## Per-dimension summary
- Design: proportionate, no new layer or container; two YAML fixes in the automation · Docs: ~95 %, three wording/WHY fixes · Tests: nothing testable in the diff, existing suite green · Security: no sensitive data, prune never touches volumes or stopped containers' images · Correctness: script and units verified under dash and `systemd-analyze`
