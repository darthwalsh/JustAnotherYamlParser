"""
  Test cases for YAML implicit type parsing

  Run tests with
     
      pytest test_node.py
"""

#TODO !!binary !!merge !!str

import math
from datetime import datetime, timedelta, timezone
from lib import node_value as nv


def test_bool():
  assert nv('true', 'bool') == True
  assert nv('FALSE') == False

  assert nv('FAlse') == 'FAlse'
  assert nv('y ') == 'y '


def test_null():
  assert nv('null', 'null') == None
  assert nv('~') == None
  assert nv('') == None

  assert nv(' ') == ' '


def test_int():
  assert nv('0b0', 'int') == 0
  assert nv('+0b10') == 2
  assert nv('-0b0') == 0
  assert nv('-0b11') == -3

  assert nv('010') == 8
  assert nv('0') == 0
  assert nv('10') == 10
  assert nv('1_') == 1
  assert nv('0x10') == 16
  assert nv('1:1') == 61
  assert nv('10:0') == 600

  assert isinstance(nv('0'), int)

  assert nv('+-1') == '+-1'
  assert nv('09') == '09'
  assert nv('1:3_0') == '1:3_0'


def test_float():
  assert nv('0', 'float') == 0.0
  assert math.isnan(nv('.nan'))
  assert nv('-.inf') == -math.inf
  assert nv('+.inf') == math.inf

  assert nv('1.2') == 1.2
  assert nv('2.') == 2.0
  assert nv('2_.') == 2.0
  assert nv('.2') == 0.2
  assert nv('._2') == 0.2
  assert nv('.1e+1') == 1.0
  assert nv('1.e-1') == 0.1
  assert nv('1.1e1') == '1.1e1'
  assert nv('1e+1') == '1e+1'

  assert nv('1:1.') == 61.0
  assert nv('0:1._1') == 1.1
  assert nv('100:1._1') == 6001.1
  assert nv('1:3_0.0') == '1:3_0.0'

  assert isinstance(nv('0', 'float'), float)

  assert nv('+-1.0') == '+-1.0'


def test_timestamp():
  date01 = datetime(2000, 1, 1, 0, 0, tzinfo=timezone.utc)

  assert nv('2000-01-01', 'timestamp') == date01
  assert nv('2000-01-01') == date01
  assert nv('2000-01-1') == '2000-01-1'
  """
  - 
  - 2001-12-14t21:59:43.10-05:00
  - 2001-12-14 21:59:43.10 -5
  - 2001-12-15 2:59:43.10
  - 2002-99-14
  """

  dtz = datetime(2001,
                 2,
                 3,
                 4,
                 5,
                 6,
                 789000,
                 tzinfo=timezone(timedelta(hours=1)))

  assert nv('2001-02-03T04:05:06.789000+01:00') == dtz
  assert nv('2001-2-3T4:05:06.789+1') == dtz
  assert nv('2001-2-3t4:05:06.789 +1') == dtz
  assert nv('2001-2-3T4:05:06.789+1') == dtz

  west = dtz.replace(
      tzinfo=timezone(-timedelta(hours=11, minutes=45)))
  assert nv('2001-2-3 4:05:06.789-11:45') == west

  utc = dtz.replace(tzinfo=timezone.utc)
  assert nv('2001-2-3T4:05:06.789Z') == utc
  assert nv('2001-2-3T4:05:06.789') == utc
  assert nv('2001-2-3T4:05:06') == utc.replace(microsecond=0)

  assert nv('2001-2-3T4:05:06.789+1:2') == '2001-2-3T4:05:06.789+1:2'
  assert nv('2001-2-3 4:5:06.789 +1') == '2001-2-3 4:5:06.789 +1'
  assert nv('96-2-3 4:05:06.789 +1') == '96-2-3 4:05:06.789 +1'
  assert nv('96-02-03') == '96-02-03'
  assert nv('2001-2-3') == '2001-2-3'
