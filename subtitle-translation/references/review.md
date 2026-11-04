# Review gates

Read before finalizing a translation. Run mechanical checks and semantic review separately; neither substitutes for the other.

## Structural gate (helper)

- Every helper cue ID appears once and in order; the full source SHA-256 matches.
- Timing lines, original indices/identifiers, cue settings, metadata, NOTE/STYLE/REGION blocks, separators, BOM, and non-payload bytes are unchanged.
- Payload line count and original line endings are unchanged.
- Tags, entities, inline timestamps, and recognized override blocks retain their exact bytes and sequence. Placeholders cannot move between payload lines.
- No new blank line, timing arrow, markup, or reserved placeholder remains in a rendered payload.
- Source and existing output files are not overwritten. Invalid intermediate results do not create a final output.

The parser is deliberately conservative, not a full subtitle-spec validator. It accepts positive-duration overlapping or out-of-order source cues without “fixing” them. It rejects malformed timings and structures it cannot safely interpret. Unsupported syntax is a reason to stop, not strip data. Non-UTF-8 files need separate approved transcoding. Numeric SRT indices need not be sequential or unique: helper IDs use cue position instead.

## Semantic gate (agent/human)

Compare every cue with its source and neighboring context:

- All source propositions survive: negation, tense/aspect where relevant, modality, questions, numbers, units, names, and uncertainty. Localize numeric punctuation only without changing value; flag any uncertainty.
- No invented fact, named speaker, relationship, explanation, motive, or completed missing sentence appears.
- Each proper noun resolves to its ledger entry, using only its canonical spelling and appropriate recorded forms. Review aliases in context; do not treat ordinary-word homonyms as names.
- No source content is omitted, duplicated, summarized away, or displaced to another cue. Sound cues, lyrics, interruptions, and speaker turns remain represented.
- Pronouns, register, profanity, honorifics, and address remain faithful across scene and batch boundaries.
- Readability concerns are reported, not fixed by retiming or sacrificing meaning. If the user supplies a line-length/CPS specification, measure against that specification; otherwise do not claim compliance with a universal limit.

For each issue record cue ID, source evidence, issue type, and resolution in a sidecar report. A failed cue is not “completed” because it was copied from the source. Back-translation may raise questions but is not an independent guarantee.

## Final report

```text
Source / target locale:
Cues translated:
Structural verification: PASS / FAIL / NOT RUN (include command and result)
Semantic review: completed / blocked (state scope)
Glossary: path; provisional entries and revisions
Unresolved issues: cue IDs and specific questions, or none identified
Readability warnings: cue IDs and applicable user-specified limits
```

Say “no issues identified,” not “guaranteed hallucination-free.” Keep all commentary outside the subtitle file.
