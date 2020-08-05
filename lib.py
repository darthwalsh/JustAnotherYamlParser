from pathlib import Path
import re


with open((Path(__file__).parent / 'productions.bnf').resolve()) as f:
  productions = f.read().split('\n\n')

bnf = {}

for p in filter(None, productions):
  name, text = (s.strip() for s in p.split('::='))
  bnf[name] = text
  # without_comments = re.sub(r'/\*.*?\*/', '', text)

class Bnf:
  def __init__(self, text: str):
    self.text = text
    self.i = 0
    self.expr = self.parse()

  def parse(self):
    items = []
    while True:
      self.take_match(r'\s*')
      if self.i == len(self.text):
        return items
      c = self.pop()
      if c == '"':
        c = self.pop()
        if c == '\\':
          c = self.pop()
        items.append(c)
        if self.pop() != '"':
          raise ValueError()
      elif c == '#' and self.pop() == 'x':
        items.append(chr(int(self.take_match(r'[0-9A-F]{1,6}'), 16)))
      elif c == '[' and self.pop() == '#' and self.pop() == 'x':
        begin = chr(int(self.take_match(r'[0-9A-F]{1,6}'), 16))
        if self.pop() != '-' or self.pop() != '#' or self.pop() != 'x':
          raise ValueError()
        end = chr(int(self.take_match(r'[0-9A-F]{1,6}'), 16))
        if self.pop() != ']':
          raise ValueError()
        items.append((begin, end))
      else:
        raise ValueError(c)

  def pop(self):
    c = self.text[self.i]
    self.i += 1
    return c

  def take_match(self, s):
    m = re.match(s, self.text[self.i:])
    if not m:
      raise ValueError(s)
    s = m.group()
    self.i += len(s)
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

    try: return int(line)
    except ValueError: pass
    try: return float(line)
    except ValueError: pass
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
