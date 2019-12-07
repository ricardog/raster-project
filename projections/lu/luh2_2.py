
import re

from ..r2py import reval as reval
from ..r2py import rparser

LU = {'annual': 'c3ann + c4ann',
      'nitrogen': 'c3nfx',
      'cropland': 'c3ann + c4ann + c3nfx',
      'pasture': 'pastr',
      'perennial': 'c3per + c4per',
      'plantation': 0,
      'primary': 'primf + primn',
      'rangelands': 'range',
      'urban': 'urban',
      'secondary': 'secd'
}

TREES = ('banana', 'cocoa' ,'coffee', 'eucalyptus', 'pine', 'fruit_mix',
         'oil_palm', 'oil_palm_mix', 'rubber_mix', 'timber', 'unknown')
funcs = {}
symbols = {}
trees = {}

def types():
  return sorted(tuple(LU.keys()) + TREES)

def expr(lu):
  if lu not in LU:
    raise ValueError("unknown land use type: '%s'" % lu)
  return LU[lu]

def tree(lu):
  if lu not in trees:
    trees[lu] = reval.make_inputs(rparser.parse(expr(lu)))
  return trees[lu]

def func(lu):
  if lu not in funcs:
    lokals = {}
    exec(reval.to_py(tree(lu), lu), None, lokals)
    funcs[lu] = lokals[lu + '_st']
  return funcs[lu]

def syms(lu):
  if lu not in symbols:
    root = tree(lu)
    symbols[lu] = reval.find_inputs(root)
  return symbols[lu]

def _predictify(sym, prefix):
  newr = sym.replace(prefix, '')
  newr = newr.replace(' vegetation', '')
  newr = newr.replace(' forest', '_pri')
  newr = newr.replace('Managed ', '')
  newr = newr.replace(' secondary', '_secondary')
  newr = re.sub(r'(Minimal|Light|Intense) use', "\\1", newr)
  newr = newr.lower()
  name = newr.split(' ')[0]
  newr = newr.replace(' ', '_')
  print(sym, prefix, name, newr)
  assert name in types(), 'unknown land use type %s' % sym
  return newr

def matches(syms, prefix):
  for sym in syms:
    try:
      _ = _predictify(sym, prefix)
      del _
    except AssertionError:
      import pdb; pdb.set_trace()
      return False
  return True

def predictify(root, prefix):
  if isinstance(root, str) and re.match(prefix, root):
    newr = _predictify(root, prefix)
    return newr
  return root
