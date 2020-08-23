"""
  Test cases for YAML inmplicit type parsing

  Run tests with
     
      pytest test_node.py
"""

#TODO !!binary !!float !!merge !!str !!timestamp

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
  assert nv('0x10') == 16
  assert nv('1:1') == 61
  assert nv('10:0') == 600

  assert nv('+-1') == '+-1'
  assert nv('09') == '09'
  assert nv('1:3_0') == '1:3_0'
