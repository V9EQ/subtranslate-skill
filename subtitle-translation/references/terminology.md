# Terminology and continuity

Read before creating or changing a glossary. The glossary records translation decisions, not additional story facts.

## Build an evidence-backed entity ledger

1. Read the full source and any supplied series material. Inventory recurring names, places, factions, organizations, titles, invented words, and ambiguous capitalized terms. Include cue-ID evidence for each identity/alias decision.
2. Keep the user's approved spelling, locale, transliteration system, honorific policy, and punctuation conventions. A glossary for one target locale is not automatically valid for another.
3. Use one entry per entity. Record source spellings and aliases, a canonical target, and approved target forms. Do not merge two people simply because they have similar names. A title or surname is an alias only when the source establishes that link.
4. Distinguish proper nouns from common words in context: “Rose” can be a person or a flower; “the North” can be a named region or a direction. Do not apply global substring replacement.
5. Assign status `approved` for a user/supplied approved choice; `provisional` for a translator's documented choice. Both remain stable during the job. A provisional choice does not become official just because it repeats.
6. If established localization is requested but not supplied, ask for a reference or permission to research it. Do not use model familiarity as proof of official canon. Do not search the web on every job.

## Inflection is allowed; identity drift is not

A canonical Russian name `Эйден` may become `Эйдена`, `Эйдену`, or `Эйденом` where grammar requires. These are forms of the same choice, not permission to switch to `Айдан`. For a location, choose one base rendering and inflect it grammatically; do not alternate transliteration and semantic translation.

`target_forms` is an auditable list of forms actually approved or used, not an exhaustive morphology engine. Add a grammatically necessary form with its cue evidence. Preserve inflection even when an exact-string checker would prefer the nominative.

Do not expand an abbreviation, translate a nickname differently halfway through, or replace a surname with a full name unless the source does so. Preserve whether the source uses a full name, alias, rank, or shortened form.

## Resolve conflicts explicitly

- A user correction can revise a mapping. Record old/new forms, reason, and affected cue IDs in `revisions`.
- If two approved sources disagree, ask which governs. Do not choose a third spelling.
- On revision, audit every earlier occurrence, including other batches and supplied project files in scope. Never silently rewrite unrelated existing episodes.
- If later context clarifies a tentative choice, update the ledger and affected translations together. If uncertainty remains, keep the stable choice and disclose it outside the subtitle text.
- Keep evidence-backed style decisions for formality and pronouns. Do not infer gender, family ties, speaker identity, or backstory solely to make the translation more specific.

## Example entry

```json
{
  "id": "person-aiden",
  "kind": "person",
  "source_forms": ["Aiden"],
  "canonical_target": "Эйден",
  "target_forms": ["Эйден", "Эйдена", "Эйдену", "Эйденом"],
  "status": "approved",
  "evidence": ["User-provided spelling; c000001, c000004"],
  "notes": "Do not substitute Айдан. No expanded name is established."
}
```

The example is illustrative, not a default dictionary. Copy the empty template and derive entries from the actual task.
