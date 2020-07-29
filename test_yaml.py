"""
  Test cases for toy JAyamlP

  You can filter to just one test case by running:
     
      pytest -k '2-1-'
"""

import glob
import json
import lib
import pytest


@pytest.mark.parametrize("tml_path", [
    pytest.param(path,
                 id=path.replace('yaml-test-suite/test/name/spec-example-',
                                 '').replace('.tml', ''))
    for path in glob.glob("yaml-test-suite/test/name/spec-example-*.tml")
])
def test_(tml_path):
  parts, curr = {}, 'head'
  with open(tml_path) as f:
    for line in f:
      if line.startswith('--- '):
        curr = line[4:].strip()
      else:
        parts.setdefault(curr, []).append(line)
  try:
    in_yaml = ''.join(parts['in-yaml'])
    in_json = ''.join(parts['in-json'])
  except e:
    print(e)
    return

  expected = json.loads(in_json)
  actual = lib.yaml(in_yaml)
  assert expected == actual, in_yaml
