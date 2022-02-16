"""
Parses the MD in https://github.com/yaml/yaml-spec/blob/1.2.2/spec/1.2.2/spec.md into BNF
"""
import re

from pathlib import Path
from lib import split_defs

def generate_bnf(md_text):
  matches = re.finditer(r'```\n\[#\](.*?)```', md_text, re.DOTALL)

  bnf_text = '\n\n'.join(m.group(1).strip() for m in matches)

  expected_defs = len(bnf_text.split('::=')) - 1
  actual = list(split_defs(bnf_text))
  if expected_defs != len(actual):
    print('Generated', len(actual), 'BNF rules but expected', expected_defs)
    exit(1)

  return bnf_text


md_file = (Path(__file__).parent / 'spec' / 'spec' / '1.2.2' / 'spec.md').resolve()
with open(md_file, 'r', encoding="utf-8") as f:
  md_text = f.read()

bnf_text = generate_bnf(md_text)

bnf_file = (Path(__file__).parent / 'productions.bnf').resolve()
with open(bnf_file, 'w', encoding="utf-8") as f:
  f.write(bnf_text)

#TODO once parsing is done, compare before/after of parsed BNF
