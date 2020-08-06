from pathlib import Path
import math
import re

with open((Path(__file__).parent / 'productions.bnf').resolve()) as f:
  productions = f.read().split('\n\n')

bnf = {}

for p in filter(None, productions):
  name, text = (s.strip() for s in p.split('::='))
  bnf[name] = text


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
    self.text = re.sub(r'/\*.*?\*/', '', text).strip()
    self.i = 0
    self.expr = self.parse()
    if self.i < len(self.text):
      raise ValueError('remaining', self.text[self.i:self.i + 10], 'got',
                       self.expr)

  def parse(self):
    return self.parseSwitch()

  def parseSwitch(self):
    prefix = r'(\w+)\s*=\s*(\w+)\s*⇒'
    signal = self.try_take(prefix)
    if not signal:
      return self.parseOr()

    var, val = re.match(prefix, signal).groups()
    switch = ["switch", var, val, self.parseOr()]
    while self.try_take(var):
      self.take('=')
      switch.append(self.take(r'\w+'))
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
        return items

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
        lo = hi = int(self.take(r'\d+'))
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
    elif name := self.try_take(r'\w[\w(),<≤-]*(?!\s*=)'):
      # Avoid capturing strings followed by '=' because that is switch name
      return "rule", name
    elif self.try_take(r'\('):
      parens = self.parse()
      self.take(r'\)')
      return parens
    else:
      return None

  def try_take(self, pattern='.'):
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


class Document:

  def __init__(self, s: str):
    self.text = s
    self.i = 0
    self.o = self.parse()
    while self.i < len(s) and self.peek().isspace():
      self.pop()
    if self.i < len(s):
      raise ValueError(f"unexpected remaining content: {s[self.i:]}")

  def parse(self):
    if self.at('- '):
      return self.parseSeq()
    line = self.peek_line().strip()

    if ' #' in line:
      line = line[0:line.index(' #')]

    if line[0] in '"\'':
      raise ValueError('not implemented quoted string')
      # need to handle quoted

    if ': ' in line:
      return self.parseMap()

    self.until('\n')

    try:
      return int(line)
    except ValueError:
      pass
    try:
      return float(line)
    except ValueError:
      pass
    return line

  def parseSeq(self):
    seq = []
    while self.take('- '):
      seq.append(self.parse())
    return seq

  def parseMap(self):
    d = {}
    while ': ' in self.peek_line():
      key = self.until(': ')
      d[key] = self.parse()
    return d

  def at(self, s):
    return self.text[self.i:self.i + len(s)] == s

  def take(self, s):
    if self.at(s):
      self.i += len(s)
      return True
    return False

  def peek(self):
    return self.text[self.i]

  def peek_line(self):
    return self.text[self.i:self.text.index('\n', self.i)]

  def pop(self):
    c = self.text[self.i]
    self.i += 1
    return c

  def until(self, c):
    s = self.text[self.i:self.text.index(c, self.i)]
    self.i += len(s) + len(c)
    return s


def yaml(s: str):
  return Document(s).o
