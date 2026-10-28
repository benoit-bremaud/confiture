# confiture — project rules

Rules specific to this repository; the global rules in `~/.claude/CLAUDE.md` still apply.

## No sensitive data in the repository (owner rule 2026-10-28)

The repository is public during development (it becomes private around V2 or V3).

- Never commit secrets, API keys, tokens or passwords — not in code, config, docs or commit messages.
- Never commit personal or home-network data: MAC addresses, IP addresses, Tailscale addresses,
  user names, family first names, exact ages. Write placeholders instead (`<probook-ip>`,
  `<mac>`, `<user>`, "the young child").
- Real values live in a local `.env` (gitignored, template in `.env.example`), in GitHub
  secrets, or in `*.local.md` notes (gitignored, e.g. `inventory.local.md`).
- Before every commit, check the staged diff for MACs, IPs, names and keys; `gitleaks` must pass.

## Code design

- Clean architecture: the domain never imports infrastructure (Home Assistant, Ollama, MQTT,
  hardware); infrastructure is injected through abstractions.
- SOLID, above all dependency inversion: depend on interfaces, wire concrete adapters at the edge.
- Keep the layering proportional to the real complexity (KISS, YAGNI).
