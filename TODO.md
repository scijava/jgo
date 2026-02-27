# jgo 2.0.0 Release TODO

This document tracks remaining work for the jgo 2.0.0 release.

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

### Scope Matching Improvements
**Files**: `src/jgo/jgo.py:615,706`
**Issue**: Compile/runtime/provided scope matching might fail in edge cases
**Impact**: Rare dependency resolution issues
**Priority**: Low - works for common cases
