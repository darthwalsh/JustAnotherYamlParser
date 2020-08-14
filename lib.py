from pathlib import Path
import math
import re
import sys


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
    ns-char         Rule is tuple ("rule", "ns-char")
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
        if len(items) == 1:
          [item] = items
          return item
        return frozenset(items)

  def parseConcat(self):
    items = []
    while True:
      item = self.parseDiff()
      if item:
        items.append(item)
      else:
        if len(items) == 1:
          [item] = items
          return item
        return ('concat', *items)

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
    elif name := self.try_take(r'\w[\w(),<≤/\-]*(?!\s*=)'):
      # Avoid capturing strings followed by '=' because that is switch name
      return "rule", name
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


class Lib:
  def __init__(self):
    self.bnf = {}

  def add(self, name, rule):
    self.bnf[name] = rule

  def load_defs(self):
    with open((Path(__file__).parent / 'productions.bnf').resolve()) as f:
      productions = f.read().split('\n\n')

    for p in filter(None, productions):
      name, text = (s.strip() for s in p.split('::='))
      if name in self.bnf: continue
      try:
        self.bnf[name] = Bnf(text)
      except Exception as e:
        raise type(e)(f"{name}: {str(e)}").with_traceback(sys.exc_info()[2])

  def parse(self, text, rule):
    return self.parse(text, self.bnf[rule].expr)

  def parse(self, text, expr):
    self.text = text
    result, lastI = self.resolve(0, expr)
    if lastI != len(text):
      raise ValueError('remaining', text[lastI:])
    return result

  def resolve(self, i, expr):
    if i == len(self.text):
      raise ValueError('at end')
    c = self.text[i]
    if isinstance(expr, str):
      if c == expr:
        return c, i + 1
    elif isinstance(expr, range):
      if ord(c) in expr:
        return c, i + 1
    elif isinstance(expr, frozenset) or isinstance(expr, set):
      items = set()
      for e in expr:
        result = self.resolve(i, e)
        if result:
          items.add(result)
      if len(items) == 1:
        return result
      return items

    elif isinstance(expr, tuple):
      kind = expr[0]

      if kind == 'concat':
        nextI = i
        items = []
        for e in expr[1:]:
          o, nextI = self.resolve(nextI, e)
          items.append(o)

        if len(items) == 1:
          return items[0], nextI
        return items, nextI

      elif kind == 'repeat':
        _, lo, hi, e = expr
        

      else:
        raise ValueError('unknown tuple:', expr)


    else:
      raise ValueError('unknown type:', expr)
