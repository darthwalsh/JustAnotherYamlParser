import base64
import datetime
import math
import re


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

def parse_str(s):
  return s

def parse_binary(s):
  return base64.b64decode(re.sub(r'\s', '', s), validate=True)


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

  # MAYBE implement merge value yaml
  for schema in 'bool null int float timestamp str binary'.split():
    if (val := globals()['parse_' + schema](s)) is not _fail:
      return val

  raise ValueError('no types parse', s)
