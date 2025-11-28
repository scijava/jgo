# jgo 2.0 Implementation Roadmap

## Critical Path Analysis

This document identifies the critical path for implementing jgo 2.0 and shows task dependencies.

## Dependency Graph

```
┌─────────────────────────────────────────────────────────────┐
│                         PHASE 1                             │
│                      Maven Layer                            │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        v                     v                     v
   1.1 Port              1.2 Fix G/A/C       1.3 SNAPSHOT
   maven.py              interpolation        support
   [2 days]              [3 days] ⚠️          [2 days]
   CRITICAL              CRITICAL
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              │
                              v
                         1.4 Remote
                         metadata
                         [1 day]
                              │
                              v
                         1.5 Tests
                         [2 days]
                         CRITICAL
                              │
┌─────────────────────────────────────────────────────────────┐
│                         PHASE 2                             │
│                   Environment Layer                         │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        v                     v                     v
   2.1 Environment      2.2 Environment       2.3 Cache
   class                Builder               key gen
   [2 days]             [3 days]              [1 day]
   CRITICAL             CRITICAL              CRITICAL
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              │
                              v
                         2.4 Migration
                         [1 day]
                              │
                              v
                         2.5 Tests
                         [2 days]
                         CRITICAL
                              │
┌─────────────────────────────────────────────────────────────┐
│                         PHASE 3                             │
│                    Execution Layer                          │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┴─────────────────────┐
        │                                           │
        v                                           v
   3.1 JVMConfig                               3.2 JavaRunner
   [1 day]                                     [2 days]
   CRITICAL                                    CRITICAL
        │                                           │
        └─────────────────────┬─────────────────────┘
                              │
                              v
                         3.3 Tests
                         [1 day]
                         CRITICAL
                              │
┌─────────────────────────────────────────────────────────────┐
│                         PHASE 4                             │
│                CLI and High-Level API                       │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        v                     v                     v
   4.1 CLI parser       4.2 CLI commands      4.3 High-level
   [2 days]             [2 days]              API
   CRITICAL             CRITICAL              [1 day]
                                              CRITICAL
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              │
                              v
                         4.4 Config
                         [1 day]
                              │
┌─────────────────────────────────────────────────────────────┐
│                         PHASE 5                             │
│                 Backward Compatibility                      │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        v                     v                     v
   5.1 v1 compat        5.3 Endpoint          5.4 Config
   shims                format                compat
   [2 days]             [1 day]               [1 day]
   CRITICAL             CRITICAL              CRITICAL
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                         PHASE 6                             │
│                Documentation & Release                      │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        v                     v                     v
   6.1 API docs         6.2 User guide        6.3 README
   [2 days]             [2 days]              [1 day]
   CRITICAL             CRITICAL              CRITICAL
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              │
                              v
                         6.4 CHANGELOG
                         [1 day]
                         CRITICAL
                              │
                              v
                         6.5 Release
                         [1 day]
                         CRITICAL
```

## Critical Path Items (Must Complete)

These tasks are on the critical path and block other work:

### Week 1: Maven Layer Foundation
1. **1.1 Port maven.py** [2 days] - Everything depends on this
2. **1.2 Fix G/A/C interpolation** [3 days] - Critical bug, blocks correctness
3. **1.5 Maven layer tests** [2 days] - Must verify correctness before building on it

### Week 2: Environment Layer
4. **2.1 Environment class** [2 days] - Core abstraction for next layer
5. **2.2 EnvironmentBuilder** [3 days] - Core functionality of jgo
6. **2.3 Cache key generation** [1 day] - Critical for correctness
7. **2.5 Environment tests** [2 days] - Verify environment building works

### Week 3: Execution Layer
8. **3.1 JVMConfig** [1 day] - Required for JavaRunner
9. **3.2 JavaRunner** [2 days] - Core execution functionality
10. **3.3 Execution tests** [1 day] - Verify end-to-end execution

### Week 4: CLI and API
11. **4.1 CLI parser** [2 days] - Required for CLI commands
12. **4.2 CLI commands** [2 days] - User-facing interface
13. **4.3 High-level API** [1 day] - Python API convenience layer

### Week 5: Compatibility
14. **5.1 v1 compat shims** [2 days] - Required for smooth migration
15. **5.3 Endpoint format compat** [1 day] - Maintain existing syntax
16. **5.4 Config compatibility** [1 day] - Don't break existing configs

### Week 6: Documentation
17. **6.1 API documentation** [2 days] - Users need docs
18. **6.2 User guide** [2 days] - Including migration guide
19. **6.3 README update** [1 day] - First thing users see
20. **6.4 CHANGELOG** [1 day] - Document all changes
21. **6.5 Release prep** [1 day] - Final testing and release

**Total critical path: ~35 days** (7 weeks with 5-day weeks)

## Parallel Work Opportunities

These tasks can be done in parallel to speed up development:

### During Week 1 (Maven Layer):
- While 1.1-1.2 are in progress:
  - Set up new module structure
  - Set up testing infrastructure
  - Design CLI flag syntax

### During Week 2 (Environment Layer):
- While 2.1-2.2 are in progress:
  - Start on 3.1 JVMConfig (independent of environment)
  - Draft documentation structure
  - Design high-level API

### During Week 3 (Execution Layer):
- While 3.1-3.2 are in progress:
  - Start on 4.1 CLI parser (can mock the layers)
  - Start on 6.1 API docs (for maven layer)

### During Week 4 (CLI):
- While 4.1-4.3 are in progress:
  - Start on 5.1 compat shims
  - Continue 6.1 API docs

### During Week 5 (Compatibility):
- While 5.x are in progress:
  - Full focus on 6.2 user guide
  - Draft 6.4 CHANGELOG

With 2-3 developers working in parallel, timeline could be compressed to 4-5 weeks.

## Risk Areas

### High Risk (require careful implementation)

**1. Property interpolation in G/A/C** (Task 1.2)
- **Risk**: Changing GACT keys during interpolation could cause correctness bugs
- **Mitigation**: Interpolate early (in `Environment.dependency()`), comprehensive tests
- **Contingency**: If too complex, defer to 2.1.0 and document as known limitation

**2. SNAPSHOT resolution** (Task 1.3)
- **Risk**: Complex logic, many edge cases, timestamp parsing
- **Mitigation**: Study Maven's implementation, extensive testing
- **Contingency**: Can ship without it if needed, add in 2.1.0

**3. Backward compatibility** (Phase 5)
- **Risk**: Breaking existing user scripts/code
- **Mitigation**: Comprehensive compat layer, extensive testing with real-world usage
- **Contingency**: Maintain jgo 1.x LTS branch for slow migrators

### Medium Risk

**4. Cache key generation** (Task 2.3)
- **Risk**: Hash collisions, cache invalidation bugs
- **Mitigation**: Use robust hashing (SHA-256), include all relevant factors
- **Contingency**: Can force cache rebuild on upgrade if needed

**5. Cross-platform testing** (Throughout)
- **Risk**: Windows path handling, symlinks, etc.
- **Mitigation**: CI testing on Windows/Mac/Linux
- **Contingency**: Document platform-specific limitations

### Low Risk

**6. Performance regressions**
- **Risk**: New code might be slower
- **Mitigation**: Benchmark against 1.x, optimize hot paths
- **Contingency**: Performance tuning in 2.0.1 if needed

## Testing Strategy

### Unit Tests (Each Phase)
- Test each class/function in isolation
- Mock dependencies
- Aim for >80% coverage per module

### Integration Tests (After Each Phase)
- Test layer interactions
- Use real Maven artifacts
- Test with and without network

### End-to-End Tests (Phase 4-5)
- Full CLI invocations
- Common real-world scenarios
- Test on actual projects (imagej, fiji, scyjava)

### Regression Tests (Phase 5)
- Run all jgo 1.x tests against 2.x
- Verify backward compatibility
- Test migration scenarios

### Performance Tests (Phase 6)
- Benchmark key operations
- Compare to 1.x performance
- Memory usage profiling

## Release Criteria

Before tagging 2.0.0:

### Functionality
- [ ] All critical path tasks complete
- [ ] All high-risk areas tested thoroughly
- [ ] SNAPSHOT support working (or documented as limitation)
- [ ] Both resolvers (pure Python and Maven) working

### Quality
- [ ] Test coverage >80% overall, >90% for critical paths
- [ ] No known critical bugs
- [ ] Passes all jgo 1.x tests (via compat layer)
- [ ] Passes new jgo 2.x tests

### Compatibility
- [ ] Backward compat layer tested with real-world code
- [ ] Configuration files migrate cleanly
- [ ] CLI maintains common use cases
- [ ] Python API compat shims work

### Documentation
- [ ] API docs complete and accurate
- [ ] User guide covers all major features
- [ ] Migration guide tested by users
- [ ] CHANGELOG comprehensive
- [ ] README updated

### Platform Testing
- [ ] Passes tests on Linux
- [ ] Passes tests on macOS
- [ ] Passes tests on Windows
- [ ] CI/CD pipeline green

### Performance
- [ ] No regressions vs 1.x for common operations
- [ ] Memory usage reasonable (<500MB for typical dep trees)
- [ ] Cache hits are fast (<100ms)

## Rollout Plan

### Alpha Release (End of Week 3)
- Core functionality works
- Not feature complete
- Invite early adopters to test
- Gather feedback

### Beta Release (End of Week 5)
- All features implemented
- Compatibility layer working
- Documentation draft complete
- Wider testing with real users

### Release Candidate (End of Week 6)
- All tests passing
- Documentation complete
- No known critical bugs
- Final review period

### 2.0.0 Release
- Tag and publish to PyPI
- Announce on scijava forum
- Update documentation site
- Create GitHub release with notes

### Post-Release
- Monitor for bug reports
- Prepare 2.0.1 with any hot fixes
- Plan 2.1.0 features (e.g., conda integration)

## Success Metrics

After 3 months:
- [ ] >50% of jgo users upgraded to 2.x
- [ ] <5 critical bugs reported
- [ ] Positive community feedback
- [ ] At least one other project depends on jgo.maven
- [ ] Documentation viewed regularly
- [ ] Active development continues on 2.x

## Team Recommendations

### Minimum Team (1 developer)
- Follow critical path strictly
- 6-7 weeks full-time
- Higher risk but doable

### Recommended Team (2 developers)
- Dev 1: Maven + Environment layers (Weeks 1-2)
- Dev 2: Testing + Docs (Weeks 1-2)
- Dev 1: Execution + CLI (Weeks 3-4)
- Dev 2: Compatibility + Docs (Weeks 3-4)
- Both: Testing + Polish (Weeks 5-6)
- **Timeline: 5-6 weeks**

### Optimal Team (3 developers)
- Dev 1: Maven layer
- Dev 2: Environment + Execution layers
- Dev 3: CLI + Compatibility + Docs
- **Timeline: 4-5 weeks**

All timelines assume developers familiar with Python, Maven concepts, and the existing jgo codebase.
