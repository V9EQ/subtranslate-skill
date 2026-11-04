# Skill authoring audit

## Primary guidance reviewed

Research used Exa search and page retrieval, plus the installed Pi 1.5.0
`docs/skills.md`. Links are upstream references, not evidence of measured quality.

| Official source | Relevant advice | Applied here |
| --- | --- | --- |
| [OpenAI Codex skills](https://developers.openai.com/codex/skills) | Focus on one job; concise routing description; imperative steps with explicit inputs/outputs; scripts for deterministic work | One portable skill, concrete CLI commands, Python owns IDs/structure/assembly |
| [Claude Code skills](https://code.claude.com/docs/en/skills) | Body loads only when invoked; keep detailed references separate; distinguish portable from host-specific fields | No Claude-only dynamic injection, subagent mode, or special tool permissions |
| [Anthropic authoring practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices) | Concision, shallow progressive disclosure, examples, early validation, evaluation-driven iteration; test intended models | Short main workflow, exact JSON example, batch checks, recovery reference, separate semantic evaluation |
| [Pi skills](https://github.com/badlogic/pi-mono/blob/main/packages/coding-agent/docs/skills.md) | Name/description for discovery; explicit steps; paths relative to skill directory; portable directory format | Resolve one absolute skill path, keep job data outside installation; no host extension needed |

The often-mentioned **500 lines is a ceiling guideline, not a target**. Moving
text into references helps only if the agent does not have to reload all of it
for every batch. Keep the happy path in SKILL.md and recovery details conditional.

## Concrete examples worth studying

- [Pi brave-search SKILL.md](https://github.com/badlogic/pi-skills/blob/main/brave-search/SKILL.md):
  short command examples, explicit options, visible output contract. Borrow the
  command-first style, not its host/path substitutions or installation assumptions.
- [Anthropic PDF skill](https://github.com/anthropics/skills/blob/main/skills/pdf/SKILL.md):
  quick start plus direct links to task-specific references. It covers a wider
  domain than subtitles, so its length is not a target for this skill.
- [OpenAI skill creator](https://github.com/openai/skills/blob/main/skills/.system/skill-creator/SKILL.md):
  staged loading and separating deterministic scripts from model instructions.
- [Subtitle Edit advanced engines](https://subtitleedit.github.io/subtitleedit/features/auto-translate-advanced.html):
  batches, glossary, previous translated context, and halving invalid batches.
  Its documented defaults (10 lines per batch, 12 previous lines) differ from
  ours; neither is a demonstrated optimum for this agent workflow.
- [LLM-Subtrans](https://github.com/machinewrapped/llm-subtrans):
  a full subtitle application, useful for studying scene/context and saved-work
  workflows, not a small drop-in agent skill. Provider code and transcription
  support would unnecessarily enlarge this package.

These are design precedents, not comparative translation-quality rankings.
No third-party implementation was copied.

## Changes in this iteration

1. **Make batching executable rather than aspirational.** `batch` emits only a
   selected window plus explicitly separated neighboring context. `check`
   validates exact ranges immediately. `merge` checks all parts in order, refusing
   stale source hashes, missing/duplicate/extra IDs, invalid payload, and overlaps.
   It never asks the model to regenerate the entire translated JSON for assembly.
2. **Reduce mandatory prompt work.** SKILL.md went from 1,052 to 689 whitespace-
   separated words (about 35% fewer). This is a word-count measurement, **not a
   tokenizer measurement or end-to-end token saving**. Replaced full-movie preload
   with incremental evidence-backed terminology, kept full semantic coverage,
   added explicit review-only behavior, bounded context/checkpoints, and recovery.
3. **Make claims testable.** Added batch/CLI regression tests, a read-only
   terminology evaluation with deliberate drift, Russian routing checks, and
   long-job/resume evaluation procedures. Agent evaluations remain unexecuted.

## Token cost versus quality

The Python helper itself makes **zero model calls**. Costs come from text the
host sends to the model, generated translations, repeated history, retries,
reviews, and tool responses. Therefore:

- Never have the model reproduce timings or combine already accepted translations.
- Read only the current window and relevant saved state, not growing whole-file JSON.
- Keep 3 accepted source/target pairs plus 3 following source cues by default.
  Use the full glossary as the authority; carry relevant entries when it is large.
- Default to 30 cues; try 10–15 for small models or dense dialogue. Count is only a
  heuristic: neither characters nor cues are model-independent token estimates.
- Review each pair before accepting it. Final checks focus on boundaries and all
  terminology occurrences instead of regenerating or back-translating the film.
- Compact/restart the host session from a checkpoint when necessary. Smaller files
  do not automatically remove earlier messages from the host's conversation.

Incremental translation trades away a mandatory global preview. Distant callbacks,
late identity revelations, and ambiguous speakers can still need targeted forward
reading and revision of earlier cues. This is an explicit trade-off, not a claim
that local context always suffices. Unsupported certainty belongs in the report,
not in dialogue.

**No prompt makes every weak model reliable.** Structural tests can protect the
file, but a small model may still mistranslate perfectly valid JSON. Test the
actual host/model/language pair. Compare input/output/cache token usage, retries,
completion rate, terminology errors, and human semantic ratings against both the
previous revision and a no-skill baseline. See the evaluation runbook.

## Remaining limits

- Checkpoints are agent-maintained. Source hashes are enforced, but target locale,
  glossary revision, and review completion are not machine-verified cache keys.
- No automatic token estimator, provider API client, scene detector, translation
  cache, or claim of automatic optimal batching was added.
- Tests cover deterministic structure, not end-to-end model quality or all hosts.
- A reusable glossary needs evidence and revision discipline; global replacement
  or substring compliance cannot establish semantic correctness.
