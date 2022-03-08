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


def test_concat():
  assert library.parse('a3z', ('concat', 'a', range(0x30, 0x3A), 'z')) == 'a3z'


def test_empty():
  assert library.parse('', ('concat',)) is None


def test_range():
  assert library.parse('2', range(0x30, 0x3A)) == '2'


def test_or():
  assert library.parse('0', {'0', '9'}) == '0'


def test_or_repeat():
  assert library.parse('0', {'0', '0'}) == '0'


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


def test_start():
  assert library.parse('\n', ('concat', ("^",), '\n', ("^",))) == '\n'


def test_end():
  assert library.parse('a', ('concat', 'a', ("$",))) == 'a'


def test_diff():
  diff = ("diff", range(0x20, 0x7F), "0", range(0x35, 0x3A))

  assert library.parse('1', diff) == '1'

  with pytest.raises(ValueError) as e_info:
    library.parse('0', diff)
  assert 'no results' in str(e_info.value)

  with pytest.raises(ValueError) as e_info:
    library.parse('5', diff)
  assert 'no results' in str(e_info.value)


tree_lib = lib.Lib(show_parse=True)
from lib import ParseResult as P

def test_tree_trivial_rule():
  assert tree_lib.parse('A', ("rule", "ns-hex-digit")) == P('ns-hex-digit', 0, 1, 'A')

def test_tree_repeat():
  assert tree_lib.parse('ABCD', ("repeat", 4, 4, ("rule", "ns-hex-digit"))) == (P('ns-hex-digit', 0, 1, 'A'), P('ns-hex-digit', 1, 2, 'B'), P('ns-hex-digit', 2, 3, 'C'), P('ns-hex-digit', 3, 4, 'D'))

def test_tree_rule():
  assert tree_lib.parse('x2A', ("rule", "ns-esc-8-bit")) == P('ns-esc-8-bit', 0, 3, ('x', P('ns-hex-digit', 1, 2, P('ns-dec-digit', 1, 2, '2')), P('ns-hex-digit', 2, 3, 'A')))

def test_tree_many_rules():
  assert tree_lib.parse('!', {("rule", "c-non-specific-tag"), ("rule", "c-tag")}) == {P('c-non-specific-tag', 0, 1, '!'), P('c-tag', 0, 1, '!')}

def test_tree_concat_many_rules():
  opts = {("rule", "c-non-specific-tag"), ("rule", "c-tag")}

  assert tree_lib.parse('!!', ('concat', opts, opts)) == {
    (P('c-tag', 0, 1, '!'), P('c-tag', 1, 2, '!')),
    (P('c-tag', 0, 1, '!'), P('c-non-specific-tag', 1, 2, '!')),
    (P('c-non-specific-tag', 0, 1, '!'), P('c-tag', 1, 2, '!')),
    (P('c-non-specific-tag', 0, 1, '!'), P('c-non-specific-tag', 1, 2, '!')),
  }
  
