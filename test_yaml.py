import json
import lib

def from_file(path):
  parts, curr = {}, 'head'
  with open(path) as f:
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
  assert expected == actual
  

def test_basic():
  from_file(
      "yaml-test-suite/test/name/spec-example-2-1-sequence-of-scalars.tml")
