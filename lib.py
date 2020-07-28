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
    line = self.until('\n')
    return line

  def parseSeq(self):
    seq = []
    while self.take('- '):
      seq.append(self.parse())
      self.pop()
    return seq

  def at(self, s):
    return self.text[self.i:self.i + len(s)] == s

  def take(self, s):
    if self.at(s):
      self.i += len(s)
      return True
    return False

  def peek(self):
    return self.text[self.i]

  def pop(self):
    c = self.text[self.i]
    self.i += 1
    return c

  def until(self, c):
    s = self.text[self.i:self.text.index(c, self.i)]
    self.i += len(s)
    return s

def yaml(s: str):
  return Document(s).o
