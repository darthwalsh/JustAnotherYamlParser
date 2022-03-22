"""
  Test cases for BNF grammar

  Run tests with
     
      pytest test_define_unbound.py
"""

import lib

l = lib.Lib()

def test_find_vars():
  assert lib.find_vars(l.bnf['c-l+literal'][0]) == set('ntm')
  assert lib.find_vars(l.bnf['l-nb-literal-text'][0]) == set('n')
  assert lib.find_vars(l.bnf['s-l+block-indented'][0]) == set('nmc')

def test_define_unbound():
  assert list(lib.define_unbound([])) == [{}]
  assert list(lib.define_unbound('m')) == [{"m": m} for m in range(0, lib.M_VAR_MAX)]
  assert list(lib.define_unbound('t')) == [
      {
          "t": 'CLIP'
      },
      {
          "t": 'KEEP'
      },
      {
          "t": 'STRIP'
      },
  ]
  assert list(lib.define_unbound(['t', 'm']))[:4] == [
      {
          "m": 0,
          "t": 'CLIP'
      },
      {
          "m": 0,
          "t": 'KEEP'
      },
      {
          "m": 0,
          "t": 'STRIP'
      },
      {
          "m": 1,
          "t": 'CLIP'
      },
  ]

def test_automagically_define_unbound():
  assert list(lib.automagically_define_unbound(l.bnf['s-l+block-indented'][0], dict(n='42', c='99')))[:2] == [{
      'c': '99',
      'm': 0,
      'n': '42'
  }, {
      'c': '99',
      'm': 1,
      'n': '42'
  }]
