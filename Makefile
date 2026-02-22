help:
	@echo "Available targets:\n\
		clean - remove build files and directories\n\
		docs  - build documentation site locally\n\
		lint  - run code formatters and linters\n\
		test  - run automated test suite\n\
		dist  - generate release archives\n\
	"

clean:
	bin/clean.sh

docs:
	bin/docs.sh

check:
	@bin/check.sh

lint: check
	bin/lint.sh

test: check
	bin/test.sh

dist: check clean
	bin/dist.sh

.PHONY: help clean docs check lint test dist
