help:
	@echo "Available targets:\n\
		clean - remove build files and directories\n\
		setup - create mamba developer environment\n\
		lint  - run code formatters and linters\n\
		test  - run automated test suite\n\
		dist  - generate release archives\n\
	\n\
	Remember to 'mamba activate jgo-dev' first!"

clean:
	bin/clean.sh

setup:
	bin/setup.sh

check:
	@bin/check.sh

lint: check
	bin/lint.sh

test: check
	bin/test.sh

dist: check clean
	python -m build
