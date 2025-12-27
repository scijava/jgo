# Future Ideas for jgo

This document tracks ideas and features that have been discussed but are not currently prioritized for implementation. These could be implemented in the future based on user demand and use cases.

## Table of Contents

- [Command-Line Flags](#command-line-flags)
- [Shortcut Features](#shortcut-features)
- [Entrypoint Features](#entrypoint-features)
- [Other Ideas](#other-ideas)

---

## Command-Line Flags

### `--no-env` / `--global` / `-g`

**Purpose**: Instruct jgo to ignore `jgo.toml` in the current working directory and behave as though no project environment exists.

**Use Case**: Force shortcut expansion even when a conflicting entrypoint exists in the local `jgo.toml`.

**Examples**:
```bash
# Project has entrypoint "repl", but you want to use the global shortcut
jgo run --no-env repl

# Equivalent to running jgo outside the project directory
cd /tmp && jgo run repl
```

**Design Considerations**:
- Should this apply to all commands or just `run`?
- Flag name options: `--no-env`, `--global`, `-g`, `--ignore-env`, `--no-project`
- Could be extended to ignore other project-local configs as well
- Could be combined with config command's existing --global flag, since the idea is similar: do something outside of only the current managed environment.

**Comments**: Postponed until users request it. Current workaround: use explicit endpoint or run outside project directory.

---

### `-f` / `--project`

**Purpose**: Instruct jgo to operate within a different project directory (`--project`, like uv has) or different jgo.toml file (`-f` flag, like mvn has) than the one in the CWD.

**Use Case**: More flexible for shell scripting, multiple TOML files in one directory, or files without the normal `jgo.toml` name.

**Examples**:
```bash
# List dependencies from a different jgo.toml environment config.
jgo -f /path/to/special-jgo.toml list

# List dependencies for a different jgo project directory.
jgo --project /path/to/other-project list
```

**Comments**: This is useful with mvn, uv, and conda/mamba. Probably will implement it in jgo sooner rather than later.

---

## Shortcut Features

### Full Command Aliases (Git/Shell Style)

**Purpose**: Allow shortcuts to expand to complete command strings including flags and arguments, similar to `git alias` or shell aliases.

**Example**:
```ini
[shortcuts]
surge = --resolver mvn tree org.scijava:scijava-common+org.scijava:scripting-groovy
```

Then `jgo surge` would expand to:
```bash
jgo --resolver mvn tree org.scijava:scijava-common+org.scijava:scripting-groovy
```

**Comments**: This would add significant complexity and could be confusing. Users who want this behavior can use shell aliases instead:

```bash
# In ~/.bashrc or ~/.zshrc
alias jgosurge='jgo --resolver mvn tree org.scijava:scijava-common+org.scijava:scripting-groovy'
```

**Rationale**: Neither `uv` nor `pixi` support this kind of full-command aliasing. Keeping shortcuts simple (endpoint-only expansion) maintains clarity and consistency with similar tools.

---

## Entrypoint Features

### `jgo entrypoint` Command Group

**Purpose**: Convenience commands for managing entrypoints in `jgo.toml` without manual file editing.

**Proposed Commands**:
```bash
jgo entrypoint add NAME CLASS        # Add new entrypoint
jgo entrypoint remove NAME           # Remove entrypoint
jgo entrypoint list                  # List all entrypoints
jgo entrypoint set-default NAME      # Set default entrypoint
jgo entrypoint rename OLD NEW        # Rename entrypoint
```

**Examples**:
```bash
jgo entrypoint add gui net.imagej.Main
jgo entrypoint set-default gui
jgo entrypoint list
jgo entrypoint remove repl
```

**Comments**: Entrypoints can be managed by directly editing `jgo.toml`, which is simple and transparent. Add this if users frequently request it.
- But should it be under a namespace like `jgo env`? Or even part of `jgo config`? E.g. `jgo config endpoint add gui net.imagej.Main`?
- If so, it leads to the question: should `jgo config -g entrypoint add gui net.imagej.Main` add the entrypoint to jgo's global configuration file? Because global endpoints are not currently supported, but could be...

**Alternative**: Users can edit `jgo.toml` directly:
```toml
[entrypoints]
gui = "net.imagej.Main"
main = "org.scijava.script.ScriptREPL"
default = "gui"
```

---

### Multiple Main Classes per Entrypoint

**Purpose**: Allow an entrypoint to specify multiple main classes to be run in sequence.

**Example**:
```toml
[entrypoints]
setup = ["com.example.Setup", "com.example.Migrate"]
```

Then `jgo run setup` would run both main classes in order.

**Comments**: Postponed until there's a clear use case. Most users run one main class at a time.

---

## Other Ideas

### Interactive `jgo init`

**Purpose**: Prompt user for common settings when creating a new `jgo.toml`.

**Example**:
```bash
$ jgo init --interactive
Environment name [my-project]:
Description [Generated environment]: My awesome project
Add dependency: org.scijava:scijava-common
Add dependency:
Create entrypoint? (y/n) y
Entrypoint name [main]: repl
Main class: org.scijava.script.ScriptREPL
Add another entrypoint? (y/n) n
Created jgo.toml
```

**Comments**: Current `jgo init ENDPOINT` is simple and covers most cases. Interactive mode could be added if users request it.

---

### Environment Variables in Shortcuts

**Purpose**: Allow shortcuts to reference environment variables.

**Example**:
```ini
[shortcuts]
local-dev = ${LOCAL_REPO}:my-artifact:LATEST
```

**Comments**: Could be useful in conjunction with includes, e.g. for referencing machine-agnostic jgo configs from dotfiles repositories.

---

### Includes in jgo config file

**Purpose**: Allow connecting multiple jgo configuration files together.

**Example**:
```ini
[include]
	path = /path/to/another_jgo_config
```

**Comments**: Postponed. Unclear use case. Users can achieve this with shell aliases if needed.

---

### `jgo install` (Tool Installation)

**Purpose**: Install Java tools globally, similar to `uv tool install` or `pipx install`.

**Example**:
```bash
jgo install imagej net.imagej:imagej
# Installs to ~/.local/bin/imagej or similar
# Creates wrapper script that runs jgo

imagej  # Can now run directly
```

**Comments**: This is a significant feature that requires:
- Deciding on installation location
- Creating wrapper scripts
- Managing installed tools
- Handling updates and removal

Could be valuable but needs careful design. See how `uv tool install` works for inspiration.

---

### Lock File Verification

**Purpose**: Verify that `jgo.lock.toml` matches the current environment.

**Example**:
```bash
jgo verify
# Checks that .jgo/ environment matches jgo.lock.toml
# Returns error if out of sync
```

**Comments**: Would be useful for CI/CD or ensuring reproducibility, but not essential for initial release.

---

### Platform-Specific Dependencies

**Purpose**: Specify different dependencies based on OS/platform.

**Example**:
```toml
[dependencies]
coordinates = ["org.scijava:scijava-common"]

[dependencies.macos]
coordinates = ["org.scijava:scijava-native-macos"]

[dependencies.linux]
coordinates = ["org.scijava:scijava-native-linux"]
```

**Comments**: Unusual use case for Java tools (which are generally platform-independent). But there are exceptions e.g. javacpp, javafx, jogamp, lwjgl. Likely to add in future.

---

## Contributing Ideas

Have an idea for jgo? Please:
1. Check if it's already listed here or in [open issues](https://github.com/scijava/jgo/issues)
2. Consider if it aligns with jgo's design philosophy (simplicity, compatibility with Maven/Java ecosystem)
3. Open a GitHub issue with your use case and proposed design

Ideas are more likely to be implemented if they:
- Solve a common problem
- Align with patterns from similar tools (uv, pixi, npm, etc.)
- Don't add much complexity
- Have clear implementation paths
