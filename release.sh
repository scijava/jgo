#!/bin/sh

die() { echo "[ERROR] $*" >&2; exit 1; }

next_version() {
  v=$1
  prefix=${v%.*}
  suffix=${v##*.}
  echo "$prefix.$((suffix+1)).dev0"
}

for cmd in echo git grep mv python rm sed test twine; do
  which "$cmd" >/dev/null || die "Missing required tool: $cmd"
done

python setup.py test || die "Some tests failed!"

sed 's/\.dev[0-9]\+//' setup.py > setup.py.new &&
mv -f setup.py.new setup.py &&
version=$(grep version= setup.py | sed "s/.*version=\"\([^\"]*\)\".*/\1/") &&
test "$version" && echo "Releasing version: $version" ||
  die "Cannot glean version string!"

git commit -m "Release version $version" setup.py &&
rm -rf dist &&
python setup.py sdist bdist_wheel &&
twine upload dist/* &&
sed "s/version=.*/version=\"$(next_version "$version")\",/" setup.py > setup.py.new &&
mv -f setup.py.new setup.py &&
git commit -m "Bump to next development cycle" setup.py &&
echo "Release complete. Don't forget to git push after ensuring all looks good!"
