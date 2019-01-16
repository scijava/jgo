python setup.py test
pip install .
python -c 'import sys; sys.path.remove(""); import jgo'
which jgo
test "$(jgo org.scijava:parsington 1+3)" -eq 4
test "$(python -c 'from jgo import __version__; print(__version__)')" = "$(jgo --version)"
