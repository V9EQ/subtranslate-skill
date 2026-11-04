# Subtitle translation skill

An English-language Agent Skill for faithful **SRT and WebVTT** translation with stable character/location names and lossless timing preservation. Read the design analysis in [docs/research.md](docs/research.md).

## Package

```text
subtitle-translation/
  SKILL.md                       # Core workflow and activation metadata
  scripts/subtitle_guard.py      # Local extraction, rendering, verification
  references/terminology.md      # Evidence-backed glossary and inflection rules
  references/review.md           # Structural and semantic review gates
  assets/glossary.template.json  # Empty reusable project ledger
  evals/                         # Agent tasks, routing checks, source fixtures
tests/test_subtitle_guard.py      # Deterministic Python tests
```

## Compatibility

The same complete skill directory works with **Claude Code, Codex, and Pi**: standard `SKILL.md` frontmatter, relative supporting-file paths, and a standalone Python helper. No host-specific plugin, MCP server, `agents/openai.yaml`, or tool allowlist is required. Optional UI metadata is not needed for Codex discovery.

| Host | Project skills directory | Personal skills directory | Explicit invocation inside the agent |
| --- | --- | --- | --- |
| Claude Code | `<project>/.claude/skills/` | `~/.claude/skills/` | `/subtitle-translation` |
| Codex CLI / IDE | `<project>/.agents/skills/` | `~/.agents/skills/` | `$subtitle-translation` (or select it with `/skills`) |
| Pi | `<project>/.agents/skills/` | `~/.agents/skills/` | `/skill:subtitle-translation` |

Codex and Pi can share **one** `.agents/skills/subtitle-translation/` installation. Claude Code uses its own `.claude/skills/` location; do not assume it discovers `.agents/skills/`. Choose either project or personal scope to avoid duplicate names.

**Verification scope:** official Claude Code/Codex discovery and invocation documentation was checked; both CLIs are unavailable in the current environment, so their live discovery and model execution were not tested. Pi 1.5.0's actual skill loader successfully parsed copied installations with **one skill and zero diagnostics**. All 16 helper tests passed. This establishes package/parser compatibility, not a three-host translation-quality benchmark. See [docs/compatibility.md](docs/compatibility.md) for evidence and limitations.

## Installation

These commands target Bash on Linux, macOS, or WSL. Install Python **3.10+** in the same environment where the agent executes commands. The agent must be permitted to read the skill and source, execute Python, and write to the output/workspace. Read-only sandboxes cannot render translations; grant only the necessary permissions through your host's normal approval mechanism. No extra Python dependencies are needed. Model access/authentication is configured separately in your agent.

### 1. Select the skill source

From the root of this cloned repository:

```bash
SKILL_SOURCE="$(pwd)/subtitle-translation"
python3 --version
```

Copy the **whole directory**, not just `SKILL.md`. The repository root alone is not an automatically discoverable skills location.

### 2. Choose one destination

**Claude Code — project installation:** replace the example path with the project containing your subtitle work.

```bash
SKILLS_DIR="/absolute/path/to/your-project/.claude/skills"
```

Or **Claude Code — personal installation**, available across local projects:

```bash
SKILLS_DIR="$HOME/.claude/skills"
```

**Codex or Pi — project installation:**

```bash
SKILLS_DIR="/absolute/path/to/your-project/.agents/skills"
```

Or **Codex or Pi — personal installation**:

```bash
SKILLS_DIR="$HOME/.agents/skills"
```

### 3. Copy without replacing an existing installation

Run this in the same shell after selecting `SKILL_SOURCE` and **one** `SKILLS_DIR` above:

```bash
(
  set -eu
  : "${SKILL_SOURCE:?Select the source directory first}"
  : "${SKILLS_DIR:?Select a destination first}"
  test -f "$SKILL_SOURCE/SKILL.md"
  destination="$SKILLS_DIR/subtitle-translation"
  if [ -e "$destination" ] || [ -L "$destination" ]; then
    printf 'Already installed; review before updating: %s\n' "$destination" >&2
    exit 1
  fi
  mkdir -p "$SKILLS_DIR"
  cp -R "$SKILL_SOURCE" "$destination"
  python3 "$destination/scripts/subtitle_guard.py" --help
)
```

This is a local folder installation, not a plugin installation. No global configuration is edited. Keep project glossaries and translation checkpoints outside the installed skill directory so future skill updates do not replace your work. To uninstall, remove only the installed `subtitle-translation/` directory after checking it contains no user work.

### 4. Load and invoke

Start the chosen agent from the target project directory:

- **Claude Code:** run `claude`, then `/subtitle-translation Translate episode.srt into Russian.` Claude Code also supports automatic activation. Current versions watch skill changes; restart if it is not discovered, particularly after creating a new skills directory.
- **Codex:** run `codex`, then `$subtitle-translation Translate episode.srt into Russian.` Use `/skills` to check discovery. Codex detects changes automatically; restart if the skill is missing.
- **Pi:** run `pi`, use `/reload` in an existing session, then `/skill:subtitle-translation Translate episode.srt into Russian.` If command discovery is disabled, the manually entered `/skill:subtitle-translation` command still works.

Pi also supports loading this checkout directly without installation:

```bash
pi --skill "$SKILL_SOURCE"
```

Invocation lines beginning with `/` or `$subtitle-translation` above are **agent input**, not shell commands. Each host may also select the skill automatically for matching translation requests. For a quick discovery check, ask it to identify the loaded skill and its bundled helper without translating anything; then run the fixture tasks in `evals/` for a real workflow check.

Example request for any host:

> Translate `episode.srt` into Russian. Keep Aiden as Эйден and Black Hollow as Чёрная Лощина, allowing grammatical inflection. Reuse the project glossary. Do not retime, invent dialogue, or change cue structure.

## How it works

1. Parse the source locally and extract cue text with stable IDs and protected-token placeholders.
2. Inventory recurring names/places across the full source and lock an evidence-backed glossary.
3. Translate sequential batches with nearby read-only context; preserve meaning and ambiguity.
4. Review every cue and glossary occurrence for omissions, inventions, naming drift and inflection.
5. Render into the unchanged source skeleton, verify it, and deliver a separate QA report.

The language model supplies **text**, not timestamp lines. Original timing lines, cue identifiers/settings, headers, metadata, separators, UTF-8 BOM and line endings are copied from the source. Tags/entities/inline timestamps are protected; their order and payload line are checked.

## Helper CLI

Python **3.10+**, standard library only; no network calls, API keys, or provider SDKs. Use a writable local filesystem supporting hard links for atomic no-clobber publication.

```bash
python3 subtitle-translation/scripts/subtitle_guard.py extract episode.srt work/source.json
# The agent writes work/translations.json using the contract in SKILL.md.
python3 subtitle-translation/scripts/subtitle_guard.py render episode.srt work/translations.json episode.ru.srt
python3 subtitle-translation/scripts/subtitle_guard.py verify episode.srt episode.ru.srt
python3 -m unittest discover -s tests -v
```

The helper is **not an automatic translation API client**: translation is performed by the agent using the skill. Existing destinations are never overwritten. On correction, write a new destination or explicitly manage prior outputs yourself; do not delete the original source.

## Boundaries

- UTF-8 `.srt` and `.vtt` only. Conservative parsing stops on unsupported/malformed structure; it is not a full format-spec validator.
- ASS/SSA, karaoke, OCR, transcription, conversion, retiming and video processing require a separately approved workflow.
- Preserve payload line counts and speaker turns. Arbitrary rewrapping and moving inline tags are intentionally not supported.
- Overlapping source cues are not automatically repaired. Non-positive cue durations are rejected.
- Glossary consistency allows grammatical case forms; it does not mean forcing the same nominative substring everywhere.
- **Mechanical validation cannot prove fidelity or prevent all hallucinations.** Semantic review is required. Missing visual/audio context must not be filled in by invention.

## Evaluation

[evals/evals.json](subtitle-translation/evals/evals.json) defines continuity, protected-WebVTT and malformed-input scenarios, plus activation checks. Run these in isolated with/without-skill sessions before making claims about model quality. The Python tests cover structural integrity and failure behavior only; no controlled model benchmark is claimed.
