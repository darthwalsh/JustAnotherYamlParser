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

  Represents different entries using python expressions:
    "0"             Text character is str "0"
    #x30            Escaped character is str "0"
    [#x30-#x39]     Character range is exclusive range(0x30, 0x40)
    "a" "b"         Concatenation is tuple ("concat", "a", "b")
    "a" | "b"       Choice is frozenset({"a", "b"})
    "a"?            Option is tuple ("repeat", 0, 1, "a")
    "a"*            Repeat is tuple ("repeat", 0, inf, "a")
    "a"+            Repeat is tuple ("repeat", 1, inf, "a")
    "a" × 4         Repeat is tuple ("repeat", 4, 4, "a")
    l-empty(n,c)    Rule is tuple ("rule", "l-empty", "n", "c")
    dig - "0" - "1" Difference is tuple ("diff", ("rule", "dig"), "0", "1")
    t=a⇒"-" t=b⇒"+" Switch is tuple ("switch", "t", "a", "-", "b", "+")
  """

  def __init__(self, text: str):
    #TODO maybe comments have semantics?
    self.text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL).strip()
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

  # Avoid capturing strings followed by '=' because that is switch name
  ident_reg = r'^((?:[\w-]|\+\w)+)(\([\w(),<≤/\+-]+\))?(?!\s*=)'

  def parseSingle(self):
    if self.try_take('"'):
      self.try_take(r'\\')
      c = self.take()
      self.take('"')
      return c
    elif self.try_take('#x'):
      return chr(int(self.take(r'[0-9A-F]{1,6}'), 16))
    elif self.try_take(r'\[#x'):
      begin = int(self.take(r'[0-9A-F]{1,6}'), 16)
      self.take('-#x')
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


class Lib:

  def __init__(self):
    self.bnf = {}

  def add(self, name, rule):
    if name in self.bnf:
      raise ValueError(name, 'already in bnf')
    self.bnf[name] = rule

  def load_defs(self):
    with open((Path(__file__).parent / 'productions.bnf').resolve()) as f:
      productions = f.read().split('\n\n')

    for p in filter(None, productions):
      name, text = (s.strip() for s in p.split('::='))
      name = Bnf(name).expr[1]
      #TODO hardcode c-indentation-indicator and c-chomping-indicator
      if name in self.bnf or name in ('c-indentation-indicator', 'c-chomping-indicator'):
        continue
      try:
        rule = Bnf(text)
      except Exception as e:
        raise type(e)(f"{name}: {str(e)}").with_traceback(sys.exc_info()[2])
      self.add(name, rule)

  def parse(self, text, rule):
    return self.parse(text, self.bnf[rule].expr)

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

_fail = object()

def exact_match(pattern, s):
  return re.match('^(?:' + pattern + '\n)$', s, re.VERBOSE)

def parse_bool(s):
  if exact_match(r'y|Y|yes|Yes|YES|true|True|TRUE|on|On|ON', s):
    return True
  if exact_match(r'n|N|no|No|NO|false|False|FALSE|off|Off|OFF', s):
    return False
  return _fail

def parse_null(s):
  if exact_match(r'''
~ # (canonical)
|null|Null|NULL # (English)
| # (Empty)''', s):
    return None
  return _fail

def parse_int(s):
  mult = 1
  if s[0] == '+':
    s = s[1:]
  elif s[0] == '-':
    mult = -1
    s = s[1:]

  def match_base(pattern, base):
      if m := exact_match(pattern, s):
        return mult * int(m.group(1).replace('_', ''), base)

  sexagesimal = None
  if m := exact_match(r'[1-9][0-9_]*(:[0-5]?[0-9])', s):
    n = 0
    for p in s.split(':'):
      n = n * 60 + int(p)
    sexagesimal = n
  

  return next(n for n in (
    match_base(r'0b([0-1_]+)', 2),
    match_base(r'0([0-7_]+)', 8),
    match_base(r'(0|[1-9][0-9_]*)', 10),
    match_base(r'0x([0-9a-fA-F_]+)', 16),
    sexagesimal,
    _fail
   ) if n is not None)

def parse_float(s):
  if exact_match(r'0+', s):
    return 0.0

  if exact_match(r'\.(nan|NaN|NAN)', s):
    return math.nan

  mult = 1
  if s[0] == '+':
    s = s[1:]
  elif s[0] == '-':
    mult = -1
    s = s[1:]

  if exact_match(r'\.(inf|Inf|INF)', s):
    return mult * math.inf

  if exact_match(r'([0-9][0-9_]*)?\.[0-9_]*([eE][-+][0-9]+)?', s):
    if s == '.': return _fail
    return mult * float(s.replace('_', ''))

  if m := exact_match(r'[0-9][0-9_]*(:[0-5]?[0-9])+\.[0-9_]*', s):
    ss = 0.0
    for p in s.split(':'):
      ss = ss * 60 + float(p.replace('_', ''))
    return ss

  return _fail

def zfill_digits(s):
  return re.sub(r'(?<!\d)(\d)(?!\d)', r'0\1', s)

def parse_timestamp(s):
  if exact_match(r'[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]', s):
    return datetime.datetime.fromisoformat(s).replace(tzinfo=datetime.timezone.utc)

  if m := exact_match(r'''
      (
        [0-9][0-9][0-9][0-9] # (year)
        -[0-9][0-9]? # (month)
        -[0-9][0-9]? # (day)
      )
      (?:[Tt]|[ \t]+)
      (
        [0-9][0-9]? # (hour)
        :[0-9][0-9] # (minute)
        :[0-9][0-9] # (second)
      )
      (\.[0-9]*)? # (fraction)
      [ \t]* # not in spec regex, but in spec examples
      (?:
        (Z) |
        ([-+][0-9][0-9]?(:[0-9][0-9])?)
      )?''', s):
    ymd, hms, fs, z, tz, tzs = m.groups()

    fs = fs.ljust(7, '0') if fs else ''

    if tz:
      if not tzs:
        tz += ':00'
    elif z:
      tz = '+00:00'
    else:
      tz = ''

    iso = zfill_digits(f"{ymd}T{hms}{fs}{tz}")
    val = datetime.datetime.fromisoformat(iso)
    if not val.tzinfo:
      val = val.replace(tzinfo=datetime.timezone.utc)
    return val

  return _fail


def node_value(s, schema = None):
  if not isinstance(s, str):
    return s

  if schema:
    f = globals()['parse_' + schema]
    if not f:
      raise ValueError('schema', schema, 'not recognized')
    val = f(s)
    if val is _fail:
      raise ValueError(s, 'is not', schema)
    return val

  for schema in 'bool null int float timestamp'.split():
    if (val := globals()['parse_' + schema](s)) is not _fail:
      return val

  return s
