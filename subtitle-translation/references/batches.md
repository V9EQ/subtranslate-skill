# Batch failures and resumption

Read only for dense/long jobs, failed batches, or interrupted sessions.

## Keep context bounded

`batch` accepts `--start` (1-based cue position, not original SRT number),
`--count` (default 30), and `--context` (0–5, default 3 on each side).
The final batch may contain fewer cues. `check` uses the same start/count.
Only `cues` belongs in the translation output; context is never translated twice.

Cue count is not a token limit. Leave room for instructions, glossary, neighboring
pairs, output, and tool messages. Use 10–15 cues for dense dialogue or constrained
models; one very long cue may still exceed the budget. Do not split a cue silently.
The helper uses no LLM tokens itself; tool output and model-generated JSON do.
It saves payload to files and prints only a short status, so read just the needed
window. Host conversation history can still grow: bounded files alone do not
bound an agent session. Resume in a fresh/compacted session from saved state when
needed; never rely solely on vanished conversation history.

Keep the complete glossary on disk. For a large glossary, carry relevant entries
and global style rules, looking up uncertain aliases in the full ledger. Do not
mistake a filtered view for the complete project glossary. Keep unresolved facts
with cue evidence, not speculative story summaries. If later context is needed
for a faithful choice, inspect the relevant source range before accepting it;
if it remains ambiguous, preserve ambiguity or report a blocker.

## Failed output

1. Read the error and correct only the named cue(s). Rerun `check`.
2. If output was truncated or repeatedly malformed, halve the failed range,
   create new input/part paths, and check each subrange with its actual count.
   Example: start 31/count 30 becomes start 31/count 15 and start 46/count 15.
3. Allow at most two corrective attempts per range before shrinking it. If a
   single cue still fails, keep work and report the blocker; do not loop forever.
4. Record only accepted parts in state. Exclude abandoned, superseded, and context
   files from `merge`. Never use a broad JSON glob; explicit paths avoid accidental
   inclusion of stale drafts, inputs, or previous merged output.

## Resume safely

`state.md` is an agent-maintained checkpoint, not an automatically verified cache.
The helper checks source hashes and structure, **not locale, glossary revisions,
semantic correctness, or review status**.

1. Read state, glossary, and this skill. Confirm source, target locale, glossary
   revision, and user choices still match. If locale changed, start a new workspace.
2. Re-run `check` for every accepted part with its recorded range. A changed source
   hash means stop and start a new workspace; do not relabel stale translations.
3. If the glossary changed, review every affected earlier occurrence before reuse.
   Do not assume source hashes detect terminology changes.
4. Load the last 3 accepted source/target pairs and unresolved questions. Generate
   the next input window at the recorded next start using a new output path.
5. Continue in order. `merge` will reject gaps, overlaps, and out-of-order parts.
   It does not sort, silently deduplicate, or fill missing translations.

For revisions, edit the affected intermediate part, check it again, and write
merged/rendered output to new paths. Never overwrite source or delete an existing
final file merely to bypass no-clobber protection.
