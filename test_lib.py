"""
  Test cases for testing parsing using BNF rules

  Run tests with
     
      pytest test_lib.py
"""

import lib
import math
import pytest

library = lib.Lib()


def test_single_char():
  assert library.parse('c', 'c') == 'c'


def test_str():
  assert library.parse('az', ('concat', 'a', 'z')) == 'az'


def test_empty():
  assert library.parse('', ('concat',)) is None


def test_range():
  assert library.parse('2', range(0x30, 0x3A)) == '2'


def test_or():
  assert library.parse('0', {'0', '9'}) == '0'


def test_or_repeat():
  assert library.parse('0', {'0', '0'}) == '0'


@pytest.mark.xfail  # TODO
def test_or_many():
  assert library.parse(
      '0', {'0', '0'}) == 'Figure out multiple parse patterns'


def test_star():
  assert library.parse('a', ("repeat", 0, math.inf, "a")) == 'a'


def test_plus():
  assert library.parse('a', ("repeat", 1, math.inf, "a")) == 'a'


def test_plus_not_match():
  assert library.parse('b', {'b', ("repeat", 1, math.inf, "a")}) == 'b'


def test_times():
  assert library.parse('aaaa', ("repeat", 4, 4, "a")) == 'aaaa'


def test_rules():
  assert library.parse('x2A', ("rule", "ns-esc-8-bit")) == 'x2A'


def test_diff():
  diff = ("diff", range(0x20, 0x7F), "0", range(0x35, 0x3A))

  assert library.parse('1', diff) == '1'

  with pytest.raises(ValueError) as e_info:
    library.parse('0', diff)
  assert 'no results' in str(e_info.value)

  with pytest.raises(ValueError) as e_info:
    library.parse('5', diff)
  assert 'no results' in str(e_info.value)
