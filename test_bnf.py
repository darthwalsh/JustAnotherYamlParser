"""
  Test cases for BNF grammar

  Run tests with
     
      pytest test_bnf.py
"""

import lib
import math
import pytest

def test_char():
  g = lib.Bnf('"c"')
  assert g.expr == 'c'

def test_string():
  g = lib.Bnf('"abc"')
  assert g.expr == 'abc'


def test_singlequote():
  g = lib.Bnf("'$'")
  assert g.expr == '$'


def test_singlequote_backslash():
  g = lib.Bnf("'\\'")
  assert g.expr == '\\'


def test_str():
  g = lib.Bnf('"y" "a" "m" "l"')
  assert g.expr == ('concat', 'y', 'a', 'm', 'l')


def test_unicode():
  g = lib.Bnf('x9')
  assert g.expr == '\x09'
  g = lib.Bnf('x10FFFF')
  assert g.expr == '\U0010ffff'


def test_range():
  g = lib.Bnf('[x30-x39]')
  assert g.expr == range(0x30, 0x3A)
  g = lib.Bnf('[xA0-xD7FF]')
  assert g.expr == range(0xA0, 0xD800)


def test_rules():
  g = lib.Bnf('s-indent(<n)')
  assert g.expr == ("rule", "s-indent", "<n")

  g = lib.Bnf('nb-json')
  assert g.expr == ("rule", "nb-json")

  g = lib.Bnf('s-separate(n,c)')
  assert g.expr == ("rule", "s-separate", "n", "c")


def test_lookarounds():
  g = lib.Bnf('[ lookahead = ns-plain-safe(c) ]')
  assert g.expr == ("?=", ("rule", "ns-plain-safe", "c"))

  g = lib.Bnf('[ lookahead ≠ ns-char ]')
  assert g.expr == ("?!", ("rule", "ns-char"))

  g = lib.Bnf('[ lookbehind = ns-char ]')
  assert g.expr == ("?<=", ("rule", "ns-char"))


def test_special():
  g = lib.Bnf('<start-of-line>')
  assert g.expr == ("^",)

  g = lib.Bnf('<end-of-input>')
  assert g.expr == ("$",)

  g = lib.Bnf('<empty>')
  assert g.expr == ("concat",)


def test_or():
  g = lib.Bnf('"0" | "9"')
  assert g.expr == {'0', '9'}


def test_opt():
  g = lib.Bnf('"a"?')
  assert g.expr == ("repeat", 0, 1, "a")


def test_star():
  g = lib.Bnf('"a"*')
  assert g.expr == ("repeat", 0, math.inf, "a")


def test_plus():
  g = lib.Bnf('"a"+')
  assert g.expr == ("repeat", 1, math.inf, "a")


def test_curlyrepeat():
  g = lib.Bnf('"a"{4}')
  assert g.expr == ("repeat", 4, 4, "a")


def test_diff():
  g = lib.Bnf('dig - x30')
  assert g.expr == ("diff", ("rule", "dig"), "0")


def test_2diff():
  g = lib.Bnf('dig - x30 - x31')
  assert g.expr == ("diff", ("rule", "dig"), "0", "1")


def test_parens():
  g = lib.Bnf('"x" (hex{2} ) "-"')
  assert g.expr == ("concat", "x", ("repeat", 2, 2, ("rule", "hex")), "-")


def test_empty():
  g = lib.Bnf(' ')
  assert g.expr == ('concat',)


def test_comment():
  g = lib.Bnf(' dig /* Empty */ ')
  assert g.expr == ("rule", "dig")


def test_commenthash():
  g = lib.Bnf(' # Empty ')
  assert g.expr == ('concat',)


def test_comments():
  g = lib.Bnf('[x41-x46] # A-F \n| [x61-x66] # a-f ')
  assert g.expr == {range(0x41, 0x47), range(0x61, 0x67)}


def test_remaining():
  with pytest.raises(ValueError) as e_info:
    lib.Bnf('"1" ^^garbage')
  assert 'garbage' in str(e_info.value)
  assert 'remaining' in str(e_info.value)


def test_bad_string():
  with pytest.raises(ValueError) as e_info:
    lib.Bnf("'1\\'")
  assert "'" in str(e_info.value)
  assert 'expected' in str(e_info.value)


def test_load():
  l = lib.Lib()
  assert len(l.bnf) == 211
  assert sum(len(defs) for defs in l.bnf.values()) == 244
