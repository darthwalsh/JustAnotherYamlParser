from dataclasses import dataclass
from pathlib import Path
from typing import Iterator
import math
import re
import sys


M_VAR_MAX = 6

def solo(items, default=None):
  if len(items) == 1:
    return next(iter(items))
  return default or items


class Bnf:
  """Automatic parse rule based on bnf rule text

  Spec 4.1. Production Syntax
  Represents different entries using python expressions:
    - Atomic terms:
    "abc"                Text string is str "abc" (no backslash escaping)
    'c'                  Text character is str "c" (no backslash escaping)
    x30                  Escaped character is str "0"
    [xA0-xD7FF]          Character range is exclusive range(0xA0, 0xD800)
    l-empty(n,c)         Production is tuple ("rule", "l-empty", "n", "c")
    - Lookarounds produce regex
    [ lookahead = 'c' ]  Production is ("?=", "c")
    [ lookahead ≠ 'c' ]  Production is ("?!", "c")
    [ lookbehind = 'c' ] Production is ("?<=", "c")
    - Special productions also produce regex (different DOTALL)
    <start-of-line>      Start of line is ("^",)
    <end-of-input>       End of whole text stream is ("$",)
    <empty>              Empty string is redundant -- would already be ("concat",)
    "a" "b"              Concatenation is tuple ("concat", "a", "b")
    "a" | "b"            Alternation is frozenset({"a", "b"})
    "a"?                 Option is tuple ("repeat", 0, 1, "a")
    "a"*                 Repeat is tuple ("repeat", 0, inf, "a")
    "a"+                 Repeat is tuple ("repeat", 1, inf, "a")
    "a"{4}               Repeat is tuple ("repeat", 4, 4, "a")
    dig - "0" - "1"      Difference is tuple ("diff", ("rule", "dig"), "0", "1")
  """

  def __init__(self, text: str):
    # '# Comments' shouldn't have semantics
    self.text = re.sub(r'# .*', '', text).strip()

    #TODO some comments have semantics!
    # Not in spec...
    self.text = re.sub(r'/\*.*?\*/', '', self.text, flags=re.DOTALL)
    self.i = 0
    self.expr = self.parse()
    if self.i < len(self.text):
      raise ValueError('remaining', self.text[self.i:self.i + 10], 'got',
                       self.expr)

  def parse(self):
    return self.parseOr()

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
    if c := self.try_take('[+?*{]'):
      lo, hi = 0, math.inf
      if c == '+':
        lo = 1
      elif c == '?':
        hi = 1
      elif c == '{':
        lo = hi = int(self.take(r'\d+'))
        self.take('}')
      return ('repeat', lo, hi, e)
    return e

  # Rule names can contain '+' so if followed by a letter it's part of the name not a regex repeat.
  ident_reg = r'^((?:[\w-]|\+\w)+)(\([\w(),<≤/\+-]+\))?'

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
    elif self.try_take(r'\[ look'):
      return self.parseLookaround()
    elif self.try_take('<'):
      return self.parseSpecial()
    elif self.try_take(r'\('):
      parens = self.parse()
      self.take(r'\)')
      return parens
    else:
      return None

  def parseLookaround(self):
    if self.try_take('ahead'):
      pos = bool(self.try_take('='))
      if not pos:
        self.take('≠')
      e = self.parseSingle()
      self.take(']')
      return ("?=" if pos else "?!", e)

    self.take('behind =')
    e = self.parseSingle()
    self.take(']')
    return ("?<=", e)

  def parseSpecial(self):
    if self.try_take('start-of-line>'): return ("^",)
    if self.try_take('end-of-input>'): return ("$",)

    self.take('empty>')
    return ("concat",)

  def parseString(self):
    cs = []
    while not self.try_take('"'):
      cs.append(self.take())
    return ''.join(cs)

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
  if tail is None:
    return head
  try:
    comb = (head, *tail)
  except:
    return (head, tail)
  return solo(comb)


def split_defs(bnf_text):
  lines = bnf_text.split('\n')
  def_lines = [i for i, line in enumerate(lines) if '::=' in line] + [len(lines)]

  for b, e in zip(def_lines, def_lines[1:]):
    def_str = '\n'.join(lines[b:e]).strip()
    name, text = (s.strip() for s in def_str.split('::='))
    yield name, text

@dataclass(frozen=True)
class ParseResult:
  name: str
  start: int
  end: int
  expr: object

def find_vars(expr):
  match expr:
    case ('rule', _, *args):
      return set(a for arg in args for a in arg.split('+') if a.isalpha() and a.islower() and len(a) == 1)
    case (_, *es):
      return set(v for e in es for v in find_vars(e))
    case set() | frozenset():
      return set(v for e in expr for v in find_vars(e))
    case _:
      return set() 

def define_unbound(vars):
  if not vars:
    yield {}
    return

  var, *vars = vars
  match var:
    case 'm':
      for f in define_unbound(vars):
        for m in range(0, M_VAR_MAX):
          yield f | {'m': m}
    case 't':
      for f in define_unbound(vars):
        for t in 'CLIP KEEP STRIP'.split():
          yield f | {'t': t}
    case _:
      raise ValueError(var)

def automagically_define_unbound(expr: any, frame: dict[str, str]):
  vars = find_vars(expr) - set(frame)
  for f in define_unbound(vars):
    yield f | frame

class Lib:

  def __init__(self, *, show_parse=False):
    self.bnf = {}
    self.load_defs()
    self.show_parse = show_parse

  def load_defs(self):
    productions_path = (Path(__file__).parent / 'productions.bnf').resolve()
    with open(productions_path, 'r', encoding="utf-8") as f:
      productions = f.read()

    for name, text in split_defs(productions):
      _, name, *params = Bnf(name).expr
      try:
        rule = Bnf(text)
      except Exception as e:
        raise type(e)(f"{name}: {str(e)}").with_traceback(sys.exc_info()[2])
      self.bnf.setdefault(name, []).append((params, rule.expr))

  def parse(self, text, expr):
    self.text = text

    results = set()
    for result, lastI in self.resolve(0, expr, {}):
      if lastI == len(text):
        results.add(result)

    if not results:
      raise ValueError('no results')
    return solo(results)

  enums = set('BLOCK-IN BLOCK-KEY BLOCK-OUT CLIP FLOW-IN FLOW-KEY FLOW-OUT KEEP STRIP'.split())
  def new_frame(self, params, args, old_frame):
    frame = {}
    for param, arg in zip(params, (old_frame.get(arg, arg) for arg in args)):
      if param.isdigit() or param in self.enums:
        if param != arg: return None
      elif param == 'n+1':
        if arg == '0': return None
        frame['n'] = str(int(arg)-1)
      else:
        if not param.isalpha():
          raise NotImplementedError(param)
        frame[param] = arg
    return frame

  def resolve(self, i: int, expr: any, frame: dict[str, str]) -> Iterator[tuple[object, int]]:
    match expr:
      case str(s):
        if i < len(self.text) and self.text[i] == s:
          yield s, i + 1
      case range():
        if i < len(self.text) and ord(self.text[i]) in expr:
          yield self.text[i], i + 1
      case set() | frozenset():
        for e in expr:
          yield from self.resolve(i, e, frame)
      case ('concat',):
        yield None, i
      case ('concat', e, *exprs):
        for vv, ii in self.resolve(i, e, frame):
          for vvv, iii in self.resolve(ii, ('concat', *exprs), frame):
            yield str_concat(vv, vvv), iii
      case ('repeat', lo, hi, e):
        if not lo:
          yield None, i
        if hi:
          dec = ('repeat', max(lo - 1, 0), hi - 1, e)
          for vv, ii in self.resolve(i, e, frame):
            for vvv, iii in self.resolve(ii, dec, frame):
              yield str_concat(vv, vvv), iii
      case ('rule', name, *args):
        for params, expr in self.bnf[name]:
          if len(params) != len(args):
            raise ValueError("arity mismatch")

          new_frame = self.new_frame(params, args, frame)
          if new_frame is None: continue

          for bound_frame in automagically_define_unbound(expr, new_frame):
            rec = self.resolve(i, expr, bound_frame)

            if self.show_parse:
              for e, ii in rec:
                yield ParseResult(name, i, ii, e), ii
            else:
              yield from rec
      case ('diff', e, *subtrahends):
        for s in subtrahends:
          for o in self.resolve(i, s, frame):
            return
        if not any(any(self.resolve(i, s, frame)) for s in subtrahends):
          yield from self.resolve(i, e, frame)
      case ('^',):
        if i == 0 or self.text[i - 1] == '\n':
          yield '', i
      case ('$',):
        if i == len(self.text):
          yield '', i
      case _:
        raise ValueError('unknown type:', expr)
