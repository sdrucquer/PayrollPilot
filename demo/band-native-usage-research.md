# Native Band usage: read-only support check

Checked October 20, 2026, before the lead’s 2:15 PM Pacific timebox. Installed CLI: **Band 0.4.16**. Official Desktop page currently describes **0.4.15**; this version difference limits assumptions. No runtime changes, plugin installs, native-session bindings, refresh/reprice operations, usage writes, provider calls or manufactured telemetry performed.

## Finding for the current product agents

**No verified supported path was found to populate native Band Desktop per-agent sessions/tokens/estimated cost from the current generic-host, direct-OpenRouter product agents.** This is a timeboxed finding, not proof that no such API can exist. R19 stays REQUIRED GAP.

Actual read-only query results and C corroboration are in [native-usage-status.txt](evidence/band/native-usage-status.txt): only one unattributed usage bucket, no attributed product-agent row, and empty native sessions for pp-audit, pp-resolution and pp-payroll. Empty attribution is not zero usage. App OpenRouter events remain separate evidence.

## What is documented / what is not

| Mechanism | Verified source | Supported conclusion | Limit for PayrollPilot |
|---|---|---|---|
| Native coding-session usage | Installed `band usage --help`, `usage sessions --help`, `usage session --help` | Usage is local coding-agent/ccusage-backed catalog estimates; per-session attribution uses live bindings then the session ledger. One-session lookup takes a coding session UUID. | Direct Python OpenRouter calls are not themselves an actual Claude Code/Codex coding-harness transcript/session. No product attribution in the checked view. |
| Actual coding-harness binding | Installed `band onboard --help`, `band attach --help` | Explicit provider/session id/transcript-path fields exist; `--auto-session` resolves from daemon presence and needs active coding-agent hooks. | Binding an arbitrary batch id, fabricated transcript or unrelated coding session would misattribute work. No binding was performed. This route requires a real participating harness session, not just renaming the generic peer. |
| Native rescan / repricing | Installed `band usage refresh --help`, `usage reprice --help` | Refresh rescans local logs; reprice recomputes accepted estimates. | Neither help describes ingestion of arbitrary OpenRouter usage. Neither operation was run. |
| Desktop coding agents | [Official Desktop guide](https://docs.band.ai/band-desktop), [coding-agent setup](https://docs.band.ai/integrations/sdks/tutorials/coding-agents) | Desktop supports owned or attached coding runtimes; the guide describes actual Codex/Claude Code agents, rooms, work and existing tool logins. | Setting up or migrating runtimes would be a separate change; it was not executed in this read-only investigation. The older hacker guide and newer Desktop page differ on runtime ownership; installed CLI help is used for local command facts. |
| SDK turn usage events | [Official SDK reference, adapter features](https://docs.band.ai/integrations/sdks/reference#adapter-features) | `Emit.USAGE` reports turn token-usage events; supported adapters include LangGraph, PydanticAI, Agno, Anthropic, Claude SDK and others. The feature’s `emit` settings govern the room timeline. | This is a documented event-reporting path, **not verified proof** that the events populate Desktop’s canonical sessions/token/cost totals. No adapter swap/installation/event emission performed. |
| Custom adapter / REST events | [Custom adapter guide](https://docs.band.ai/integrations/sdks/tutorials/creating-framework-integrations), [event API](https://docs.band.ai/api/agent-api/agent-api-events/create-agent-chat-event) | Execution events can report tools/results/errors/tasks; the SDK guide describes adapter integration. | The reviewed pages do not establish a native per-agent session/cost ingestion contract for our current generic direct-OpenRouter loop. A room event or screenshot of app metrics is not automatically native cost-view proof. |

The supported native path identified is **real coding-harness session attribution**, observed through the CLI and corresponding Desktop view. It is not currently verified for these generic product agents. SDK `Emit.USAGE` is a candidate to ask Band about, not a tested fix or a claim that the mandatory visibility gap is closed.

## Exact sponsor question for the owner to ask

> We run Band Desktop/CLI 0.4.16 with three real Python product agents registered as `--host generic`, calling OpenRouter directly. Native `band usage agents` has only an unattributed bucket, and native session queries for those agents return empty session/agent arrays; generic provider-session bindings are null. Is there a supported SDK/API path that records their **actual** model token usage and estimated USD cost into Band Desktop’s native **per-agent sessions/tokens/cost view**? If yes, please give the required event/schema, real session binding, pricing source, version and exact Desktop view. Does SDK `Emit.USAGE` populate that canonical view, or only room timeline events? If generic agents are unsupported, does this hackathon criterion require actual supported coding-harness agents, or is a clearly labeled SDK usage timeline accepted? We will not substitute unrelated sessions or fabricate transcripts/costs.

This is draft text for the owner/lead; Lane E has not sent it externally. A sponsor answer must be recorded and verified before upgrading R19. No synthetic figures or machine-wide unattributed totals may be labeled per-product-agent cost.

## Exact read-only commands and research results

```bash
band --version
band --help
band onboard --help
band attach --help
band sessions --help
band agent --help
band usage --help
band usage agents --help
band usage sessions --help
band usage session --help
band usage refresh --help
band usage reprice --help
```

All exit 0. This inspected flags; it did not run onboarding, attachment, refresh or repricing. The three date-filtered session reads and aggregate usage read are recorded in the sanitized status artifact.

Official sources read through Firecrawl: `/jam` redirected to `/band-desktop`; `/llms.txt` documentation index; `/integrations/sdks/reference`; `/integrations/sdks/tutorials/coding-agents`; `/integrations/custom-integration`; custom-adapter and event API pages linked above; [official hacker guide](https://www.band.ai/hacker-guide). Two official-site searches returned no results; a developer-index search returned unrelated results, which were not used as Band evidence. Scrapes succeeded; the custom-integration page had no useful usage passage. No claim of exhaustive API/source inspection.
