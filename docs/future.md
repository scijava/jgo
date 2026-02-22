# Future Ideas

This page tracks ideas and features that are not currently planned for implementation but could be added in future releases based on user demand.

## Planned (post-2.0)

**Parallel downloads**
: Download multiple artifacts concurrently for faster cache population.

**Shell completion**
: Generate bash/zsh/fish completion scripts for the command-based CLI.

**Version ranges with semantic versioning**
: Report on dependency divergence in scenarios like two different major versions.

## Under consideration

**`jgo install`** (tool installation)
: Install Java tools globally, similar to `uv tool install`. Creates wrapper scripts in `~/.local/bin/`.

**Lock file verification**
: `jgo verify` to check that the environment matches `jgo.lock.toml`.

**Platform-specific dependencies**
: Specify different dependencies per OS in `jgo.toml` (useful for JavaFX, LWJGL, etc.).

**Interactive `jgo init`**
: Prompt for settings when creating a new `jgo.toml`.

**`--no-env` / `--global` flag**
: Ignore `jgo.toml` in the current directory and use global configuration only.

**Full command aliases in shortcuts**
: Allow shortcuts to expand to complete command strings including flags.

**Environment variables in shortcuts**
: Allow `${VAR}` references in shortcut definitions.

**Configuration file includes**
: `[include]` section for composing multiple config files.

**Entrypoint management commands**
: `jgo entrypoint add/remove/list` for managing entrypoints without editing `jgo.toml` manually.

## Contributing ideas

Have an idea for jgo? Please:

1. Check if it's already listed here or in [open issues](https://github.com/apposed/jgo/issues).
2. Consider whether it aligns with jgo's design philosophy: simplicity, Maven/Java ecosystem compatibility, and Python-first tooling.
3. Open a [GitHub issue](https://github.com/apposed/jgo/issues/new) with your use case and proposed design.
