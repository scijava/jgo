#!/bin/sh

# submodule relationships
pydeps src/jgo -o layers.svg --max-module-depth 2 -xx jgo jgo.jgo jgo.__main__

# source file relationships
pydeps src/jgo -o files.svg -xx jgo jgo.jgo jgo.__main__
