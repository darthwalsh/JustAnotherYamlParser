"""
  Test cases for testing parsing using BNF rules

  Run tests with
     
      pytest test_lib.py
"""

import lib
import math

def get_lib():
  library = lib.Lib()
  library.add('c-indentation-indicator(m)', 'SKIP')
  library.add('c-chomping-indicator(t)', 'SKIP')
  library.load_defs()
  return library


def run(text, expr, expected):
  assert ().resolve(0, expr) == expected


def test_single_char():
  assert get_lib().value('c', 'c') == 'c'


def test_str():
  assert get_lib().value('yaml', ('concat', 'y', 'a', 'm', 'l')) == 'yaml'


def test_concat():
  assert get_lib().value('abab', ('concat', ('concat', 'a', 'b'),
                                  ('concat', 'a', 'b'))) == 'ab'


def test_range():
  assert get_lib().parse('2', range(0x30, 0x3A)) == '2'


def test_or():
  assert get_lib().parse('0', {'0', '9'}) == '0'


def test_or_repeat():
  assert get_lib().parse('0', {'0', '0'}) == '0'


def test_or_many():
  assert get_lib().parse(
      '0', {'0', '0'}) == 'Figure out multiple parse patterns'  # TODO


##### TODO test below this


def test_repeat():
  assert get_lib().parse('0', ("repeat", 0, math.inf, "a")) == '0'



def test_star():
  g = lib.Bnf('"a"*')
  assert g.expr == ("repeat", 0, math.inf, "a")


def test_plus():
  g = lib.Bnf('"a"+')
  assert g.expr == ("repeat", 1, math.inf, "a")


def test_times():
  g = lib.Bnf('"a" × 4')


def test_times_n():
  g = lib.Bnf('"a" × n')
  assert g.expr == ("repeat", "n", "n", "a")


def test_rules():
  g = lib.Bnf('s-indent(<n)')
  assert g.expr == ("rule", "s-indent(<n)")


def test_diff():
  g = lib.Bnf('dig - #x30')
  assert g.expr == ("diff", ("rule", "dig"), "0")


def test_2diff():
  g = lib.Bnf('dig - #x30 - #x31')
  assert g.expr == ("diff", ("rule", "dig"), "0", "1")


def test_parens():
  g = lib.Bnf('"x" (hex × 2 ) "-"')
  assert g.expr == ("concat", "x", ("repeat", 2, 2, ("rule", "hex")), "-")


def test_switch():
  g = lib.Bnf('t=a⇒"-" t=b⇒"+"')
  assert g.expr == ("switch", "t", "a", "-", "b", "+")


def test_empty():
  g = lib.Bnf(' ')
  assert g.expr == ('concat',)


def test_comment():
  g = lib.Bnf(' /* Empty */ ')
  assert g.expr == ('concat',)


def test_comments():
  g = lib.Bnf('[#x41-#x46] /* A-F */ | [#x61-#x66] /* a-f */ ')
  assert g.expr == {range(0x41, 0x47), range(0x61, 0x67)}


def test_remaining():
  with pytest.raises(ValueError) as e_info:
    lib.Bnf('"1" ^^garbage')
  assert 'garbage' in str(e_info.value)
  assert 'remaining' in str(e_info.value)


def test_bad_string():
  with pytest.raises(ValueError) as e_info:
    lib.Bnf('"1\' "2"')
  assert '"2"' in str(e_info.value)
  assert 'expected' in str(e_info.value)


def test_load():
  library = lib.Lib()
  library.add('c-indentation-indicator(m)', 'SKIP')
  library.add('c-chomping-indicator(t)', 'SKIP')
  library.load_defs()
