pip install --upgrade pip
pip install psutil
python setup.py test
pip install .
python -c 'import sys; sys.path.remove(""); import jgo'
which jgo
test "$(jgo org.scijava:parsington 1+3)" -eq 4
