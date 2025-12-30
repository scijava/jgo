Tests jgo --color flag.

  $ jgo --color=never remove
  * (glob)
   Usage: jgo remove [OPTIONS] COORDINATES...* (glob)
  * (glob)
   Try 'jgo remove --help' for help* (glob)
  +- Error ----------------------------*-+ (glob)
  | Missing argument 'COORDINATES...'. * | (glob)
  +------------------------------------*-+ (glob)
  * (glob)
  [2]

  $ jgo --color=always remove
  * (glob)
   \x1b[33mUsage:\x1b[0m \x1b[1mjgo remove\x1b[0m [\x1b[1;36mOPTIONS\x1b[0m] \x1b[1;36mCOORDINATES\x1b[0m...* (esc) (glob)
  * (glob)
  \x1b[2m \x1b[0m\x1b[2mTry \x1b[0m\x1b[1;2;36m'jgo remove --help'\x1b[0m\x1b[2m for help\x1b[0m\x1b[2m*(esc) (glob)
  \x1b[31m╭─\x1b[0m\x1b[31m Error \x1b[0m\x1b[31m─────*─\x1b[0m\x1b[31m─╮\x1b[0m (esc) (glob)
  \x1b[31m│\x1b[0m Missing argument 'COORDINATES...'. *         \x1b[31m│\x1b[0m (esc) (glob)
  \x1b[31m╰───────────────────────────────────────────*─────────────────╯\x1b[0m (esc) (glob)
  * (glob)
  [2]
