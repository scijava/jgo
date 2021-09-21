#!/bin/sh

die() { echo "[ERROR] $*" >&2; exit 1; }

next_version() {
  v=$1
  prefix=${v%.*}
  suffix=${v##*.}
  echo "$prefix.$((suffix+1)).dev0"
}

# Check for .pypirc which is required for uploading via twine
if [ ! -f ~/.pypirc ]; then
  die "Please set set up a .pypirc file with username and password in your user home directory before proceeding. See https://packaging.python.org/specifications/pypirc/"
fi

# Check for required commands
for cmd in echo git grep mv python rm sed test twine; do
  which "$cmd" >/dev/null || die "Missing required tool: $cmd"
done

# Run the unit tests
python setup.py test || die "Some tests failed!"

# Update the version string to non-dev version
sed 's/\.dev[0-9]\+//' setup.py > setup.py.new &&
mv -f setup.py.new setup.py &&
version=$(grep version= setup.py | sed "s/.*version=\"\([^\"]*\)\".*/\1/") &&
test "$version" && echo "Releasing version: $version" ||
  die "Cannot glean version string!"

# Create release commit
git commit -m "Release version $version" setup.py &&
# Clear old builds and re-build distribution
rm -rf dist &&
python setup.py sdist bdist_wheel &&
# Create the release tag
git tag "$version" &&
# Bump to the next dev version
sed "s/version=.*/version=\"$(next_version "$version")\",/" setup.py > setup.py.new &&
mv -f setup.py.new setup.py &&
git commit -m "Bump to next development cycle" setup.py &&
echo "Release complete. Don't forget to run:
twine upload dist/*
git push
git push origin $version"
