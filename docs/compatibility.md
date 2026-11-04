# Host compatibility check

## Common package contract

The skill has a matching directory/name (`subtitle-translation`), a specific description below the standard 1,024-character limit, and only standard frontmatter fields: `name`, `description`, and `compatibility`. Instructions refer to bundled files relative to the skill directory. Python 3.10+ is the only helper dependency. There are no host-specific prompt substitutions, assumed MCP tool names, hardcoded installation paths, or plugin dependencies.

All three hosts can read instructions and supporting resources and execute the helper when their tool permissions permit it. The helper uses a writable local filesystem with hard-link support for no-clobber output publication. Native Windows shell instructions and filesystems without hard links were not tested; README installation commands target Bash on Linux/macOS/WSL. Model credentials belong to the host, not this package.

## Claude Code

Primary reference: [Extend Claude with skills](https://code.claude.com/docs/en/skills).

- Project location: `.claude/skills/subtitle-translation/SKILL.md`.
- Personal location: `~/.claude/skills/subtitle-translation/SKILL.md`.
- Explicit invocation: `/subtitle-translation`, followed by task arguments.
- `name` and `description` identify the workflow; `compatibility` is accepted standard metadata, not environment enforcement.
- Supporting scripts/references belong inside the skill folder. No `.claude-plugin/plugin.json` is required for a local skill.
- Current documentation describes live skill change detection. Restarting remains a straightforward fallback after first installation.

**Status:** package and installation instructions checked against official documentation. `claude` is not installed on PATH in the test environment; no Claude Code runtime parsing, slash-command discovery, or model translation run is claimed.

## Codex

Primary reference: [Agent skills](https://developers.openai.com/codex/skills).

- Project location: `.agents/skills/subtitle-translation/SKILL.md`, discovered from the working directory through repository ancestors.
- Personal location: `~/.agents/skills/subtitle-translation/SKILL.md`.
- Explicit invocation in CLI/IDE: `$subtitle-translation`; `/skills` provides discovery/selection.
- Skill folders may contain scripts and references. `agents/openai.yaml` provides optional UI/policy/dependency metadata, not mandatory discovery metadata.
- Codex detects changes automatically; restart if updates are not visible.

**Status:** package and instructions checked against official documentation. `codex` is not installed on PATH in the test environment; no Codex runtime parsing, selector discovery, or model translation run is claimed.

## Pi

Reference: the installed Pi **1.5.0** `docs/skills.md`, shipped with `@earendil-works/pi-coding-agent`; CLI flags additionally checked with `pi --help`.

- Pi supports shared project `.agents/skills/` and personal `~/.agents/skills/` directories, so the same installed copy can serve Codex and Pi.
- Explicit invocation: `/skill:subtitle-translation`, followed by the task. `/reload` refreshes an existing session.
- `pi --skill /absolute/path/to/subtitle-translation` loads a checkout explicitly without copying it into a discovery directory.

**Runtime parser check performed:** in temporary directories, the complete package was copied beneath `.claude/skills/`, `.agents/skills/`, and `.pi/skills/`. Pi 1.5.0's installed `loadSkillsFromDir` implementation was called with each explicitly selected parent. Each returned exactly one skill named `subtitle-translation` and no diagnostics. The temporary trees were removed afterward; no personal/global skills were installed.

This test establishes that the copied package is loadable by Pi's actual parser. Calling the parser on `.claude/skills/` explicitly does **not** imply Pi automatically discovers that location, nor does it test Claude Code's parser. Likewise, the temporary `.pi/skills/` copy is not an extra recommended installation or a claim about another host's search paths.

No model request was made. Full Pi TUI command discovery and autonomous translation quality were not tested in a separate session.

## Supporting tests

`python3 -m unittest discover -s tests -q` passed **16 tests** after the compatibility review. They cover extraction/rendering/verification, protected tokens, SRT/WebVTT skeleton preservation and fail-closed behavior; they are host-independent helper tests.

README copy instructions were exercised in a temporary project for both `.claude/skills/` and `.agents/skills/`: the installed helper was executable through Python, its extraction command completed, and a second install was rejected without changing the first copy. No external host was installed and no credentials or global configuration were modified.

For stronger compatibility evidence, install the folder using README instructions on a machine with each CLI, confirm its explicit invocation, then run `evals/evals.json` in a fresh session. Record host/model versions and permission settings. A document-format check must not be reported as an end-to-end agent benchmark.
