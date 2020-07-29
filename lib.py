import re

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

