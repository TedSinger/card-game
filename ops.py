import xarray as xr
from collections import Counter, namedtuple


class Op(namedtuple("Op", ["side", "kind", "what"])):
    # FIXME: maybe START with the word and lookup the implementation
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
    @classmethod
    def clashes(cls, ops) -> bool:
        # various pathologies. either it causes some cards to be too difficult to play on, or it makes a rule confusing
        # even&face
        # suit&<
        # low&<

        ocmp_color = False
        side_color = False
        for side, kind, _ in self.ops:
            if side == 'ocmp' and kind in ('color', 'suit'):
                ocmp_color = True
            if side in ('left', 'right') and kind == 'suit':
                side_color = True
        return ocmp_color and side_color


    def overlaps(self) -> list['Op']:
        # Any Op that is stricter than this one
        # this & other == other and this | other == this
        if self.what == ('D', 'H'):
            return [Op(self.side, self.kind, ('D',)), Op(self.side, self.kind, ('H',))]
        elif self.what == ('C', 'S'):
            return [Op(self.side, self.kind, ('C',)), Op(self.side, self.kind, ('S',))]
        elif self.side == 'ocmp' and self.kind == 'color' and self.what == '==':
            return [Op(self.side, 'suit', '==')]
        elif self.word == 'high':
            return [Op(self.side, self.kind, (11,12,13))]
        elif self.word == 'even':
            return [Op(self.side, self.kind, (4,8,12))]
        else:
            return []
    def complements(self) -> list['Op']:
        # Any Op that is the opposite of this one
        # this & other == null and this | other == all
        pairs = [
            ('>', '<'),
            (tuple(range(1, 14))[::2],tuple(range(1, 14))[1::2]),
            (tuple(range(8, 14)), tuple(range(1, 8))),
            (('C', 'S'), ('D', 'H')),
        ]
        for left, right in pairs:
            if self.what == left:
                return [Op(self.side, self.kind, right)]
            elif self.what == right:
                return [Op(self.side, self.kind, left)]
        if self.kind == 'color':
            return [Op(self.side, self.kind, '==' if self.what == '!=' else '!=')]
        return []
        
    def disjoints(self) -> list['Op']:
        # this & other == null
        ret = []
        if self.side == 'ocmp':
            if self.kind == 'color' and self.what == '!=':
                ret.append(Op(self.side, 'suit', '=='))
            elif self.kind == 'suit' and self.what == '==':
                ret.append(Op(self.side, 'color', '!='))
        elif self.kind == 'suit':
            ret.extend([Op(self.side, 'suit', suit) for suit in SUITS_WORDS if len(set(suit) & set(self.what)) == 0])
        elif self.what == (11,12,13):
            ret.append(Op(self.side, 'num', tuple(range(1, 8))))
        elif self.what == tuple(range(1, 8)):
            ret.append(Op(self.side, 'num', (11,12,13)))
        return ret + self.complements()

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
    Op('ocmp', 'color', '=='),
])
