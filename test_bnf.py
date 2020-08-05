"""
  Test cases for BNF grammar

  Run tests with
     
      pytest test_bnf.py
"""

import lib


def test_char():
  g = lib.Bnf('"c"')
  assert g.expr == ['c']


def test_str():
  g = lib.Bnf('"y" "a" "m" "l"')
  assert g.expr == ['y', 'a', 'm', 'l']


def test_quote():
  g = lib.Bnf(r'"\""')
  assert g.expr == ['"']


def test_backslash():
  g = lib.Bnf(r'"\\"')
  assert g.expr == ['\\']


def test_unicode():
  g = lib.Bnf('#x9')
  assert g.expr == ['\x09']
  g = lib.Bnf('#x10FFFF')
  assert g.expr == ['\U0010ffff']


def test_range():
  g = lib.Bnf('[#x30-#x39]')
  assert g.expr == [('0', '9')]


def test_or():
  g = lib.Bnf('"0" | "9"')
  assert g.expr == [['0'] '9')]
