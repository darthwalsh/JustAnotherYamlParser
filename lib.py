from pathlib import Path
from typing import Callable
import datetime
import math
import re
import sys


def solo(items, default=None):
  if len(items) == 1:
    return next(iter(items))
  return default or items


class Bnf:
  """Automatic parse rule based on bnf rule text

  Spec 4.1. Production Syntax
  Represents different entries using python expressions:
    - Atomic terms:
    "abc"           Text string is str "abc" (no backslash escaping)
    'c'             Text character is str "c" (no backslash escaping)
    x30            Escaped character is str "0"
    [xA0-xD7FF]     Character range is exclusive range(0xA0, 0xD800)
    l-empty(n,c)    Production is tuple ("rule", "l-empty", "n", "c")
    TODO fix below:
    - TODO Lookaround
    "a" "b"         Concatenation is tuple ("concat", "a", "b")
    "a" | "b"       Choice is frozenset({"a", "b"})
    "a"?            Option is tuple ("repeat", 0, 1, "a")
    "a"*            Repeat is tuple ("repeat", 0, inf, "a")
    "a"+            Repeat is tuple ("repeat", 1, inf, "a")
    "a" × 4         Repeat is tuple ("repeat", 4, 4, "a")
    dig - "0" - "1" Difference is tuple ("diff", ("rule", "dig"), "0", "1")
    t=a⇒"-" t=b⇒"+" Switch is tuple ("switch", "t", "a", "-", "b", "+")
  """

  def __init__(self, text: str):
    # Comments shouldn't have semantics
    self.text = re.sub(r'# .*', '', text).strip()
    self.i = 0
    self.expr = self.parse()
    if self.i < len(self.text):
      raise ValueError('remaining', self.text[self.i:self.i + 10], 'got',
                       self.expr)

  def parse(self):
    return self.parseSwitch()

  def parseSwitch(self):
    prefix = r'(\w+)\s*=\s*([\w\-]+)\s*⇒'
    signal = self.try_take(prefix)
    if not signal:
      return self.parseOr()

    var, val = re.match(prefix, signal).groups()
    switch = ["switch", var, val, self.parseOr()]
    while self.try_take(var):
      self.take('=')
      switch.append(self.take(r'[\w\-]+'))
      self.take('⇒')
      switch.append(self.parseOr())

    return tuple(switch)

  def parseOr(self):
    items = set()
    while True:
      items.add(self.parseConcat())
      if not self.try_take(r'\|'):
        return solo(frozenset(items))

  def parseConcat(self):
    items = []
    while True:
      item = self.parseDiff()
      if item:
        items.append(item)
      else:
        return solo(items, ('concat', *items))

  def parseDiff(self):
    subtrahend = self.parseRepeat()
    minuends = []
    while self.try_take('-'):
      minuends.append(self.parseRepeat())
    if minuends:
      return ('diff', subtrahend, *minuends)
    return subtrahend

  def parseRepeat(self):
    e = self.parseSingle()
    if c := self.try_take('[+?*×]'):
      lo, hi = 0, math.inf
      if c == '+':
        lo = 1
      elif c == '?':
        hi = 1
      elif c == '×':
        count = self.take(r'\w+')
        lo = hi = int(count) if count.isdigit() else count
      return ('repeat', lo, hi, e)
    return e

  def parseString(self):
    cs = []
    while not self.try_take('"'):
      cs.append(self.take())
    return ''.join(cs)

  # Avoid capturing strings followed by '=' because that is switch name
  ident_reg = r'^((?:[\w-]|\+\w)+)(\([\w(),<≤/\+-]+\))?(?!\s*=)'

  def parseSingle(self):
    if self.try_take('"'):
      return self.parseString()
    if self.try_take("'"):
      c = self.take() # \ isn't used as an escape
      self.take("'")
      return c
    elif self.try_take('x'):
      return chr(int(self.take(r'[0-9A-F]{1,6}'), 16))
    elif self.try_take(r'\[x'):
      begin = int(self.take(r'[0-9A-F]{1,6}'), 16)
      self.take('-x')
      end = int(self.take(r'[0-9A-F]{1,6}'), 16) + 1
      self.take(r'\]')
      return range(begin, end)
    elif name := self.try_take(Bnf.ident_reg):
      match = re.match(Bnf.ident_reg, name)
      name, args = match.groups()
      if '(' in name:
        raise ValueError(name)

      args = args.strip('()').split(',') if args else ()
      return "rule", name, *args
    elif self.try_take(r'\('):
      parens = self.parse()
      self.take(r'\)')
      return parens
    else:
      return None

  def try_take(self, pattern='.') -> str:
    m = re.match(pattern, self.text[self.i:])
    if not m:
      return None
    s = m.group()
    self.i += len(s)
    self.try_take(r'\s+')
    return s

  def take(self, pattern='.'):
    s = self.try_take(pattern)
    if not s:
      raise ValueError('expected', pattern, 'at', self.text[self.i:self.i + 10])
    return s


def str_concat(head, tail):
  if isinstance(head, str) and isinstance(tail, str):
    return head + tail
  return solo((head, *(tail if tail is not None else ())))


def split_defs(bnf_text):
  lines = bnf_text.split('\n')
  def_lines = [i for i, line in enumerate(lines) if '::=' in line] + [len(lines)]

  for b, e in zip(def_lines, def_lines[1:]):
    def_str = '\n'.join(lines[b:e]).strip()
    name, text = (s.strip() for s in def_str.split('::='))
    yield name, text


class Lib:

  def __init__(self):
    self.bnf = {}

  def add(self, name, rule):
    if name in self.bnf:
      raise ValueError(name, 'already in bnf')
    self.bnf[name] = rule

  def load_defs(self):
    productions_path = (Path(__file__).parent / 'productions.bnf').resolve()
    with open(productions_path, 'r', encoding="utf-8") as f:
      productions = f.read()

    for name, text in split_defs(productions):
      name = Bnf(name).expr[1]
      #TODO hardcode c-indentation-indicator and c-chomping-indicator
      # if name in self.bnf or name in ('c-indentation-indicator', 'c-chomping-indicator'):
      if name in self.bnf:
        continue
      try:
        rule = Bnf(text)
      except Exception as e:
        raise type(e)(f"{name}: {str(e)}").with_traceback(sys.exc_info()[2])
      self.add(name, rule)

  def parse(self, text, expr):
    self.text = text
    results = set()
    self.resolve(0, expr, lambda v, i: results.add(v) if i == len(text) else 0)
    if not results:
      raise ValueError('no results')
    return solo(results)

  def resolve(self, i, expr, cb: Callable[[object, int], None]) -> None:
    if isinstance(expr, str):
      if i < len(self.text) and self.text[i] == expr:
        cb(self.text[i], i + 1)

    elif isinstance(expr, range):
      if i < len(self.text) and ord(self.text[i]) in expr:
        cb(self.text[i], i + 1)

    elif isinstance(expr, frozenset) or isinstance(expr, set):
      for e in expr:
        result = self.resolve(i, e, cb)

    elif isinstance(expr, tuple):
      kind = expr[0]

      if kind == 'concat':
        if len(expr) == 1:
          cb(None, i)
          return

        self.resolve(
            i, expr[1], lambda v, ii: self.resolve(
                ii, ('concat', *expr[2:]), lambda vv, iii: cb(
                    str_concat(v, vv), iii)))

      elif kind == 'repeat':
        _, lo, hi, e = expr

        if not lo:
          cb(None, i)

        if hi:
          dec = ('repeat', max(lo - 1, 0), hi - 1, e)
          self.resolve(
              i, e, lambda v, ii: self.resolve(
                  ii, dec, lambda vv, iii: cb(str_concat(v, vv), iii)))

      elif kind == 'rule':
        self.resolve(i, self.bnf[expr[1]].expr, cb)

      elif kind == 'diff':
        _, e, *subtrahends = expr

        allowed = True

        def not_allowed(v, i):
          nonlocal allowed
          allowed = False

        for s in subtrahends:
          self.resolve(i, s, not_allowed)

        if allowed:
          self.resolve(i, e, cb)

      else:
        raise ValueError('unknown tuple:', expr)

    else:
      raise ValueError('unknown type:', expr)
