Tests jgo version command.

Test version command.

  $ jgo version
  jgo [0-9a-z.]+ (re)

Test --version flag on main command.

  $ jgo --version
  jgo [0-9a-z.]+ (re)

Test version with --color=never.

  $ jgo --color=never version
  jgo [0-9a-z.]+ (re)

Test version with --color=always.

  $ jgo --color=always version
  jgo [0-9a-z.]+ (re)

Test version with other global flags (should still work).

  $ jgo --quiet version
  jgo [0-9a-z.]+ (re)

  $ jgo --verbose version
  jgo [0-9a-z.]+ (re)
