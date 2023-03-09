import xarray as xr
from collections import Counter, namedtuple


class Op(namedtuple("Op", ["side", "kind", "what"])):
    @property
    def word(self):
        if self.side == 'ocmp':
            if self.kind == 'num':
                # the word is describing the left card
                return 'lower' if self.what == '<' else 'higher'
            else:
                return f'different {self.kind}' if self.what == '!=' else f'same {self.kind}'
        else:
            if self.kind == 'suit':
                return SUIT_WORDS[self.what]
            else:
                return [k for k, v in NUM_WORDS.items() if v == self.what][0]

    def xarr(self):
        if not hasattr(self, '_xarr'):
            x = all_pairs.copy()
            if self.side == 'ocmp':
                if self.kind == 'num':
                    if self.what == '>':
                        mask = x.leftnum > x.rightnum
                    else:
                        mask = x.leftnum < x.rightnum
                elif self.kind == 'suit':
                    if self.what == '==':
                        mask = x.leftsuit == x.rightsuit
                    else:
                        mask = x.leftsuit != x.rightsuit
                else: # color
                    mask = x.leftsuit.isin(['C', 'S']) ^ x.rightsuit.isin(['C', 'S'])
                    if self.what == '==':
                        mask = 1-mask
                x &= mask
            else:
                x *= 0
                x.loc[{f'{self.side}{self.kind}':list(self.what)}] = 1
                x &= all_pairs
            self._xarr = x
        return self._xarr


all_pairs = xr.DataArray(
    data = [[[[1]*4]*13]*4]*13,
    coords = {'leftnum': range(1,14), 'rightnum': range(1,14), 'leftsuit':['S','H','C','D'], 'rightsuit':['S','H','C','D']},
    dims = ('leftnum', 'leftsuit', 'rightnum', 'rightsuit')
)


SUIT_WORDS = {
    ('S',): 'spade',
    ('C',): 'club',
    ('D',): 'diamond',
    ('H',): 'heart',
    ('D', 'H'): 'red', # caring about order within a color is a bug waiting to happen
    ('C', 'S'): 'black'
}
# FIXME: one of these two is backwards
NUM_WORDS = {
    'odd': tuple(range(1, 14))[::2],
    'even': tuple(range(1, 14))[1::2],
    'high': tuple(range(8, 14)),
    'low': tuple(range(1, 8)),
    'face': (11, 12, 13),
    'quartet': (4, 8, 12),
    'trio': (3, 6, 9, 12),
}



SUITS = 'SHCD'
COLORS = [('C', 'S'), ('D', 'H')]

ALL_OPS = []
for side in ['left', 'right']:
    for suit in SUITS:
        o = Op(side, 'suit', (suit,))
        ALL_OPS.append(o)
    for color in COLORS:
        o = Op(side, 'suit', color)
        ALL_OPS.append(o)


for side in ['left', 'right']:
    for name, vals in NUM_WORDS.items():
        o = Op(side, 'num', tuple(sorted(vals)))
        ALL_OPS.append(o)
ALL_OPS.extend([
    Op('ocmp', 'num', '>'),
    Op('ocmp', 'num', '<'),
    Op('ocmp', 'suit', '=='),
    Op('ocmp', 'color', '!='),
    Op('ocmp', 'color', '!='),
])
