# jgo 2.0.0 Release TODO

This document tracks remaining work for the jgo 2.0.0 release.

## 🚨 Blockers for 2.0.0 Release

These items **must** be completed before releasing 2.0.0:

- [x] **CLI Command-Based Interface**: Finalize command-based CLI design (`jgo run`, `jgo add`, etc.) - see `docs/cli-redesign.md`
- [x] **Dependency Resolution**: `PythonResolver` and `MvnResolver` must produce the same dependency graphs in both managed and no-managed modes.
- [ ] **Documentation**: Write user-facing documentation (see Documentation section below)
- [ ] **CHANGELOG.md**: Create comprehensive changelog documenting all changes from 1.x
- [ ] **README.md**: Update with jgo 2.0 features and architecture
- [ ] **Release testing**: Test on Windows, macOS, and Linux
- [ ] **Docstrings**: Ensure all public APIs have comprehensive docstrings for `help()`

## 📚 Documentation (Blocker)

Documentation to write as part of a comprehensive ReadTheDocs site in `docs/`:

- [ ] **User Guide** (`docs/user-guide.md`)
  - Installation
  - Quick start examples
  - CLI command reference (new command-based interface)
  - jgo.toml specification and usage
  - Common recipes and patterns

- [ ] **Migration Guide** (`docs/migration-guide.md`)
  - Already exists, needs review and polish
  - Add more examples of common migration patterns
  - Document cache directory migration strategy

- [ ] **Architecture Overview** (`docs/architecture.md`)
  - Three-layer architecture explanation
  - When to use each layer directly
  - Integration points between layers

- [ ] **API Reference via Docstrings**
  - Enhance docstrings in `src/jgo/__init__.py` for high-level API
  - Enhance docstrings in `src/jgo/maven/__init__.py`
  - Enhance docstrings in `src/jgo/env/__init__.py`
  - Enhance docstrings in `src/jgo/exec/__init__.py`
  - Ensure `help(jgo)`, `help(jgo.maven)`, etc. are comprehensive

## 🧪 Testing (Blocker)

- [ ] **Cross-platform testing**
  - [ ] Linux (already working)
  - [ ] macOS (already working)
  - [ ] Windows (needs verification)

- [ ] **Integration testing**
  - [ ] Test with real-world projects (imagej, fiji, scijava)
  - [ ] Test jgo.toml workflow end-to-end
  - [ ] Test cjdk integration on clean system

- [ ] **Backward compatibility testing**
  - [ ] Verify all jgo 1.x scripts still work
  - [ ] Test deprecated API warnings

## 🐛 Known Issues (Non-Blockers)

These can be deferred to 2.1.0 or later:

### SNAPSHOT Improvements
**Files**: `src/jgo/maven/core.py:226,436`
**Issue**: SNAPSHOT locking to exact timestamps not fully implemented
**Impact**: jgo.lock.toml doesn't lock SNAPSHOTs to specific builds
**Priority**: Low - SNAPSHOTs work, just not perfectly reproducible

### JVM Options from Config
**File**: `src/jgo/cli/commands.py:405`
**Issue**: TODO for loading JVM options from config file
**Impact**: Can't configure default JVM args in ~/.jgorc
**Priority**: Low - can pass via CLI

### Scope Matching Improvements
**Files**: `src/jgo/jgo.py:615,706`
**Issue**: Compile/runtime/provided scope matching might fail in edge cases
**Impact**: Rare dependency resolution issues
**Priority**: Low - works for common cases

### Checksum Files
**File**: `src/jgo/maven/resolver.py:60`
**Issue**: TODO to also download MD5/SHA1 checksum files
**Impact**: No checksum verification during download
**Priority**: Low - integrity is less critical for Maven Central

## ✨ Future Enhancements (Post-2.0.0)

Ideas for future releases (not tracked in this file, move to GitHub issues):

- (HIGH) Parallel downloads for faster cache population
- (HIGH) Shell completion (bash/zsh)
- (MEDIUM) Version ranges with semantic versioning
  - E.g. report on dependency divergence in desired scenarios (e.g. two different major versions)
- (LOW) Checksum verification for jgo.lock.toml

See also [future.md](docs/future.md).

## 📋 Release Checklist

Before tagging 2.0.0:

- [ ] All blockers resolved (see above)
- [ ] All tests passing (currently: 108/108 ✅)
- [ ] Documentation complete and reviewed
- [ ] CHANGELOG.md finalized
- [ ] README.md updated
- [ ] Version is 2.0.0.dev0 (already done ✅)
- [ ] CI/CD pipeline green
- [ ] Cross-platform testing complete
- [ ] Migration guide tested by users
- [ ] Docstrings comprehensive for `help()` output

## 🚀 Release Process

When ready to release:

1. Update version from `2.0.0.dev0` to `2.0.0` in `pyproject.toml`
2. Finalize CHANGELOG.md with release date
3. Create git tag: `git tag -a v2.0.0 -m "Release version 2.0.0"`
4. Push tag: `git push origin v2.0.0`
5. Merge `redesign` branch to `main`
6. Build and publish to PyPI: `uv build && uv publish`
7. Create GitHub release with notes
8. Announce on scijava forum

## 📝 Notes

- Version already bumped to 2.0.0.dev0 ✅
- All coding phases (1-5) complete ✅
- Tests: 108/108 passing ✅
- Primary focus: Documentation and polish
- Target: Feature-complete, production-ready 2.0.0 release
