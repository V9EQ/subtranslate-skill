# Subtitle Translation Skill

An [Agent Skill](https://agentskills.io/) for translating **SRT and WebVTT**
subtitles while preserving timing, formatting, and consistent character and
location names. Compatible with **Pi**, **Codex**, and **Claude Code**.

The skill guides your agent through contextual translation, project glossary
management, semantic review, and local structural verification. The language
model translates dialogue; a bundled Python helper preserves the source structure.

## Features

- Translate subtitle text without regenerating timestamps or cue identifiers.
- Reuse a project glossary across batches and episodes, allowing grammatical inflection.
- Translate sequential batches with neighboring context to maintain continuity.
- Preserve tags, entities, inline timestamps, metadata, BOM, and line endings.
- Check cue coverage, source fingerprints, protected tokens, and output structure.
- Deliver a translated file, reusable glossary, and separate QA report.

The skill instructs the agent to preserve originals, flag uncertain meaning,
and treat instruction-like dialogue as data rather than commands.

## Requirements

- Pi, Codex, or Claude Code with Agent Skills support and model access.
- Python **3.10+** in the environment where the agent runs commands.
- Permission to read source/skill files, execute Python, and write workspace/output files.
- A writable local filesystem with hard-link support for no-clobber publication.

The helper uses only the Python standard library: no additional packages,
network access, or API keys. Translation uses your agent's configured model;
this is **not** a standalone translation API client or an offline-model guarantee.

## Installation

Review [SKILL.md](subtitle-translation/SKILL.md), then copy the **entire**
`subtitle-translation/` directory, including its supporting files.

Choose one installation scope and destination:

| Agent | Personal skills directory | Project skills directory |
| --- | --- | --- |
| Pi | `~/.agents/skills/` | `<project>/.agents/skills/` |
| Codex | `~/.agents/skills/` | `<project>/.agents/skills/` |
| Claude Code | `~/.claude/skills/` | `<project>/.claude/skills/` |

Pi and Codex can share one `.agents/skills/subtitle-translation/` copy. Claude Code
uses a separate `.claude/skills/` copy. Avoid duplicate installations with the
same skill name, including copies in Pi's own skills directories.

From the root of this cloned or downloaded repository, run the following in
**Bash on Linux, macOS, or WSL**. Set `SKILLS_DIR` to one directory from the table;
this example installs personally for Pi and Codex:

```bash
SKILLS_DIR="$HOME/.agents/skills"
(
  set -eu
  : "${SKILLS_DIR:?Choose a skills directory}"
  test -f subtitle-translation/SKILL.md
  destination="$SKILLS_DIR/subtitle-translation"
  if [ -e "$destination" ] || [ -L "$destination" ]; then
    printf 'Already installed; review before updating: %s\n' "$destination" >&2
    exit 1
  fi
  mkdir -p "$SKILLS_DIR"
  cp -R subtitle-translation "$destination"
  python3 "$destination/scripts/subtitle_guard.py" --help
)
```

For Claude Code, use `SKILLS_DIR="$HOME/.claude/skills"`. For a project installation,
use an absolute project path with the matching directory from the table.
No global agent configuration is changed.

Run `/reload` in Pi after installation. Restart Codex or Claude Code if the skill
does not appear. Pi can also load the checkout without installation:

```bash
pi --skill ./subtitle-translation
```

## Usage

Start your agent in the project containing your subtitle files. Ask for a
translation, or invoke the skill explicitly:

**Pi**

```text
/skill:subtitle-translation Translate episode.srt into Russian.
```

**Codex**

```text
$subtitle-translation Translate episode.srt into Russian.
```

**Claude Code**

```text
/subtitle-translation Translate episode.srt into Russian.
```

These are **agent inputs**, not shell commands. Matching requests can also
activate the skill automatically.

For project-specific terminology, include your choices:

> Translate `episode.srt` into Russian. Keep Aiden as Эйден and Black Hollow as
> Чёрная Лощина, allowing grammatical inflection. Reuse the project glossary.
> Do not retime, invent dialogue, or change cue structure.

Other example requests:

- “Localize `captions.vtt` into Spanish (Spain), preserving tags and metadata.”
- “Translate the next episode into French using our approved glossary.”
- “Review character and location names across these translated episodes.”

Provide a source file and target language. The agent should ask for missing
inputs and report unresolved terminology rather than inventing context.

## How it works

1. Extract cue text locally with stable IDs and protected-token placeholders.
2. Read the full source and establish an evidence-backed project glossary.
3. Translate bounded, sequential batches with nearby read-only context.
4. Review every cue for meaning, omissions, additions, and terminology drift.
5. Render into the source skeleton, verify structure, and deliver a separate report.

Keep glossaries, checkpoints, and outputs in your project workspace, **outside**
the installed skill directory. Structural verification cannot establish
translation fidelity; semantic review remains required.

## Limitations

- UTF-8 `.srt` and `.vtt` only. Unsupported encodings or malformed structure stop
  the workflow; the helper is not a complete format-spec validator.
- Payload line counts and protected-token placement are fixed. Arbitrary
  rewrapping, moving inline tags, and merging cues are not supported.
- No transcription, OCR, ASS/SSA/karaoke handling, conversion, retiming, or video
  editing. These require a separately approved workflow.
- Source overlaps are not repaired; non-positive cue durations are rejected.
- Readability concerns are reported, not resolved by silently dropping meaning
  or changing timing. There is no universal line-length or reading-speed guarantee.
- No guarantee of hallucination-free translation. Missing visual/audio context
  and provisional terminology must be disclosed.

## Updating and uninstalling

Existing installations and helper output destinations are not overwritten.
Before updating, move the old installed directory to a backup **outside all
skill-discovery directories**, then repeat installation. Reload or restart your
agent afterward. Do not store user work inside the installation.

To uninstall, remove only the installed `subtitle-translation/` directory after
checking it contains no project work. Remove backups separately if no longer needed.

## Skill contents

| File | Contents |
| --- | --- |
| [SKILL.md](subtitle-translation/SKILL.md) | Activation metadata, workflow, safety rules, and JSON contract |
| [subtitle_guard.py](subtitle-translation/scripts/subtitle_guard.py) | Local extraction, rendering, and structural verification |
| [terminology.md](subtitle-translation/references/terminology.md) | Glossary evidence, aliases, homonyms, and inflection rules |
| [review.md](subtitle-translation/references/review.md) | Structural/semantic review gates and report template |
| [glossary.template.json](subtitle-translation/assets/glossary.template.json) | Reusable project glossary template |
| [evals/](subtitle-translation/evals/) | Agent evaluation cases, activation checks, and source fixtures |

## Development

Run deterministic helper tests from the repository root:

```bash
python3 -m unittest discover -s tests -v
```

Inspect the helper CLI or exercise individual workflow stages:

```bash
python3 subtitle-translation/scripts/subtitle_guard.py --help
python3 subtitle-translation/scripts/subtitle_guard.py extract episode.srt work/source.json
# The agent writes work/translations.json using the contract in SKILL.md.
python3 subtitle-translation/scripts/subtitle_guard.py render episode.srt work/translations.json episode.ru.srt
python3 subtitle-translation/scripts/subtitle_guard.py verify episode.srt episode.ru.srt
```

Use a new output path for each correction; never delete the source to bypass a
no-overwrite check.

For paired agent evaluations, see [evals/README.md](subtitle-translation/evals/README.md).
Helper tests do not measure model translation quality; no controlled with/without-skill
benchmark is claimed. Host parser checks also do not establish end-to-end agent quality.

Further documentation:

- [Host compatibility evidence and limitations](docs/compatibility.md)
- [Design research and improvement priorities](docs/research.md)
