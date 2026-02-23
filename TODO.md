# jgo 2.0.0 Release TODO

This document tracks remaining work for the jgo 2.0.0 release.

## 📚 Documentation (Blocker)

Documentation to write as part of a comprehensive ReadTheDocs site in `docs/`:

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
