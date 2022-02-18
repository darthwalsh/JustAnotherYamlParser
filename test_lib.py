"""
  Test cases for testing parsing using BNF rules

  Run tests with
     
      pytest test_lib.py
"""

import lib
import math
import pytest

library = None


def get_lib():
  global library
  if not library:
    l = lib.Lib()
    l.load_defs()
    library = l
  return library


def run(text, expr, expected):
  assert ().resolve(0, expr) == expected


def test_single_char():
  assert get_lib().parse('c', 'c') == 'c'


def test_str():
  assert get_lib().parse('az', ('concat', 'a', 'z')) == 'az'


def test_empty():
  assert get_lib().parse('', ('concat',)) == None


def test_range():
  assert get_lib().parse('2', range(0x30, 0x3A)) == '2'


def test_or():
  assert get_lib().parse('0', {'0', '9'}) == '0'


def test_or_repeat():
  assert get_lib().parse('0', {'0', '0'}) == '0'


@pytest.mark.xfail  # TODO
def test_or_many():
  assert get_lib().parse(
      '0', {'0', '0'}) == 'Figure out multiple parse patterns'


def test_star():
  assert get_lib().parse('a', ("repeat", 0, math.inf, "a")) == 'a'


def test_plus():
  assert get_lib().parse('a', ("repeat", 1, math.inf, "a")) == 'a'


def test_plus_not_match():
  assert get_lib().parse('b', {'b', ("repeat", 1, math.inf, "a")}) == 'b'


def test_times():
  assert get_lib().parse('aaaa', ("repeat", 4, 4, "a")) == 'aaaa'


def test_rules():
  assert get_lib().parse('x2A', ("rule", "ns-esc-8-bit")) == 'x2A'


def test_diff():
  diff = ("diff", range(0x20, 0x7F), "0", range(0x35, 0x3A))

  assert get_lib().parse('1', diff) == '1'

  with pytest.raises(ValueError) as e_info:
    get_lib().parse('0', diff)
  assert 'no results' in str(e_info.value)

  with pytest.raises(ValueError) as e_info:
    get_lib().parse('5', diff)
  assert 'no results' in str(e_info.value)
