# Design research

## Scope and evidence

This document records the initial design. The follow-up
[authoring audit](skill-authoring-audit.md) supersedes its proposal status for
bounded batches, partial validation, deterministic merge, incremental terminology,
and review-only behavior. Checkpoints remain agent-maintained, not a validated
locale/glossary-aware resume engine. The evaluation suite now has four tasks;
controlled model trials are still pending.

This design synthesizes the four requested authoring guides and primary project documentation found/read with Exa. Project observations below describe documented workflows, not a line-by-line code audit or measured comparison of their translation quality. No third-party implementation or prompt was copied. There is no claim of a unique new translation algorithm.

## Skill authoring guidance → concrete decisions

| Source | Relevant practice | Application here |
| --- | --- | --- |
| [Agent Skills: best practices](https://agentskills.io/skill-creation/best-practices) | Narrow scope, expert-specific gotchas, defaults instead of menus, control proportional to fragility, progressive disclosure | One subtitle-localization workflow; stable terminology and unsupported-format rules in the core; detailed review/terminology references loaded at explicit gates |
| [Anthropic: skill authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices) | Specific third-person description, concise main instructions, deterministic utilities, verifiable intermediate outputs, validation loops | Portable name/description; JSON text intermediate; source fingerprint and helper IDs; render only after structural validation |
| [OpenAI: build skills](https://developers.openai.com/plugins/build/skills) | State inputs, outputs, inference boundaries and stop conditions; use scripts for deterministic operations; test activation and non-activation | Ask for target/file, prohibit unsupported identity inference, stop on malformed inputs, separate translate/review from transcription/retiming; no unnecessary MCP dependency |
| [Agent Skills: evaluating skills](https://agentskills.io/skill-creation/evaluating-skills) | Realistic tasks, fresh-context baseline comparisons, objective assertions, human review and trace-based iteration | Three task evals plus routing checks; deterministic tests for structure; semantic rubric for names, ambiguity and additions; explicit plan for with/without-skill comparison |

The main distinction is **variable language vs immutable structure**. An LLM may choose idiomatic phrasing, but should not be responsible for recreating timestamp syntax. A glossary is a decision ledger, not a global replacement dictionary.

## Similar projects and translation mechanics

### Subtitle Edit

Sources: [advanced local engines](https://subtitleedit.github.io/subtitleedit/features/auto-translate-advanced.html), [auto translate](https://subtitleedit.github.io/subtitleedit/features/auto-translate.html).

Its advanced local-engine documentation describes batches with synopsis, glossary, previous translated lines, and configurable line-break preservation. Invalid replies are retried and batches can be halved. This addresses the lack of continuity in independent line-by-line translation.

**Adapted principle:** bounded contextual batches with a glossary. **Deliberate difference:** read-only forward source context plus preceding accepted pairs; timing syntax stays outside the translation intermediate. No GUI, provider integration, or engine-specific prompt copied. The default batch size is a heuristic, not a measured optimum.

### LLM-Subtrans (formerly GPT-Subtrans)

Sources: [repository](https://github.com/machinewrapped/llm-subtrans), [mechanics/wiki](https://github.com/machinewrapped/llm-subtrans/wiki), [GUI workflow](https://github.com/machinewrapped/llm-subtrans/wiki/GUI).

The documented workflow groups subtitles into scene batches, maps model replies back to source lines, validates basic parity/format errors, and requests corrected replies. Condensed prior context and editable scene/batch summaries support continuity; project state supports resuming. Its GUI docs explicitly note the context trade-off when translating scenes in parallel. The wiki also acknowledges that missing visual context can cause speaker/referent mistakes.

**Adapted principle:** sequential batches, stable correspondence, targeted correction. **Deliberate difference:** an evidence-backed entity ledger and nearby accepted pairs rather than an expanding generated plot summary. No automatic assumption that line parity establishes semantic fidelity. No provider client or persistent project engine reproduced.

### ai-subtitle-translator

Source: [repository and workflow description](https://github.com/surbiks/ai-subtitle-translator).

The README documents structured parsing, adaptive chunks, read-only previous context, glossary injection, per-line IDs, corrective retries, optional critique/refinement, caching, checkpointing, and formatting reconstruction. It also documents target-language-specific normalization and source-term/target-term compliance checks.

**Adapted principle:** structured text results, read-only context and glossary priority. **Deliberate differences:** no global language-specific normalizer, no blind source-string cache, no approximate positioning of inline tags, no mandatory exact nominative-name substring match. A proper name can inflect without changing identity. Every protected token must stay ordered on its original payload line; if that is too restrictive for a requested edit, stop and scope a separate workflow.

## Why these safeguards matter

- **A prompt saying “preserve timestamps” is not a guarantee.** Rendering copies all non-payload source bytes and independently compares the resulting skeleton.
- **A synopsis can introduce facts.** Prefer source evidence and short context; unsupported gender, speaker identity, relationships and expanded names remain unresolved.
- **A glossary can be misapplied.** Homonyms and aliases require context; grammatical forms must not be misclassified as naming drift.
- **A fluent translation can be wrong.** Structural checks cannot detect invented motives, lost negation, or omitted meaning. Full pairwise semantic review remains necessary.
- **Auto-fixing can violate the task.** Retiming, cue merging, transcription repair, length compression and file conversion are out of scope by default.
- **Silently retaining failed source lines hides incompleteness.** Keep checkpoints, but do not publish a final translation if required cues remain blocked.

## Improvement priorities after documentation review

The authoring guides standardize the **skill contract**, not a mandatory repository
README layout. The revised README follows the local FFmpeg skill's user-facing
structure; detailed evidence and evaluation procedures stay in supporting docs.
The opening “English-language” label was removed because it describes the
instruction language, not a restriction on source or target languages.

The following table is the **historical proposal backlog**, not the current feature
list. See the follow-up audit above for implemented items; no measured model-quality
gains are claimed:

| Priority | Observed gap | Proposed change and acceptance check |
| --- | --- | --- |
| 1 | Three task specs exist, but there are no paired model runs | Follow [the evaluation runbook](../subtitle-translation/evals/README.md), save traces and assertion evidence, and compare with/without-skill results before expanding the prompt. Report semantic, structural, and routing results separately. |
| 1 | The description offers terminology review, but the numbered procedure assumes a new translation | Add an explicit review-only branch: inspect supplied translations/glossary, report cue-specific drift, and do not render or rewrite files unless asked. Add a review-only task that asserts no file mutation. |
| 1 | Small fixtures do not exercise long jobs or conflicting project decisions | Add long-file/context truncation, glossary conflict, glossary revision, resume, mixed-language, and user-instruction conflict cases. Include Russian activation prompts and target-language pairs beyond the two successful-output fixtures. Keep held-out cases. |
| 2 | Accepted batches are saved by instruction, but no deterministic resume/merge contract exists | After observing real resume failures, add a manifest keyed by source hash, locale, glossary revision, and accepted cue IDs. Test stale checkpoints, duplicate/missing batches, changed terminology, and interrupted publication. Avoid a source-string-only cache. |
| 2 | The helper validates only a complete translation document | If traces show late discovery of batch errors, add partial-batch validation with explicit expected ID ranges. Validate placeholders and line counts before accepting a batch, then keep full-document verification mandatory. |
| 2 | About 30 cues is a heuristic regardless of dialogue density | Evaluate context-budget-aware batches with room for glossary, overlap, and output; on truncation/invalid replies, shrink only the failed batch with a bounded retry budget. Compare continuity errors and token costs, not speed alone. |
| 3 | Readability warnings are requested, but the helper has no measurement command | Add optional report-only line-length/CPS metrics using user-specified limits and documented counting rules for markup, entities, and Unicode. Expose durations without changing the preserved skeleton. Test dense dialogue and non-Latin scripts; never auto-retime or silently compress meaning. |
| 3 | Installation and package checks are manual | Consider a tested no-clobber installer with external backups, plus CI for unit tests, frontmatter, bundled paths, JSON fixtures, and documentation links. Do not add plugin manifests or host-specific metadata without a concrete requirement. |

These priorities apply the guides' recommendations to test before adding rules,
keep the core concise, and bundle repeated deterministic work only when useful.
[Subtitle Edit's advanced-engine documentation](https://subtitleedit.github.io/subtitleedit/features/auto-translate-advanced.html)
provides a concrete precedent for contextual batches, glossary injection, and
shrinking invalid batches.
[LLM-Subtrans's project workflow](https://github.com/machinewrapped/llm-subtrans/wiki/GUI)
provides a precedent for saved state/resumption and documents the continuity
trade-off of parallel translation. These precedents motivate experiments, not
claims that their defaults are optimal here. Transcription and broad format
support remain outside this skill's scope.

## Evaluation status and next iteration

The repository includes runnable deterministic unit tests and three end-to-end agent evaluation specifications. Unit tests exercise the helper, not model adherence or translation quality. A small manually authored Russian translation is tested through the real renderer to exercise the intermediate contract; that is not a controlled LLM benchmark.

Before claiming a model-quality improvement:

1. Run each `subtitle-translation/evals/evals.json` task in separate fresh sessions with and without the skill, using the same model/settings and input files.
2. Keep each configuration's outputs, execution transcript, elapsed time, and actual token count under an external `subtitle-translation-workspace/iteration-N/` directory. Do not invent unavailable measurements.
3. Use the helper for structural assertions. Have a bilingual reviewer grade meaning, names, case forms, homonyms, ambiguity and non-addition with cue-specific evidence. Review the full output, not only assertion phrases.
4. Record per-assertion PASS/FAIL and evidence; compare results blindly where practical. Review routing false positives and false negatives separately.
5. Inspect failed and successful traces, revise the smallest general instruction, rerun the whole set, and retain a previous-version baseline. Add real user failure cases without overfitting to these fixtures.

Independent with/without-skill sessions and multi-model trials have **not** been run as part of creating this package. No semantic accuracy percentage or hallucination-free guarantee is claimed.
