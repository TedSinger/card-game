from collections import Counter
from ops import ALL_OPS, Op, all_pairs, SUITS

class Filter:    
    def __init__(self, ops, xarr):
        self.ops = unify(ops)
        assert isinstance(self.ops, tuple)
        assert all(isinstance(o, Op) for o in self.ops)
        self.left_ops = [o for o in self.ops if o.side == 'left']
        self.ocmp_ops = [o for o in self.ops if o.side == 'ocmp']
        self.right_ops = [o for o in self.ops if o.side == 'right']
        self.xarr = xarr

    @classmethod
    def from_ops(self, ops):
        xarr = ops[0].xarr().copy()
        for o in ops[1:]:
            xarr &= o.xarr()
        return Filter(ops, xarr)

    def __and__(self, other):
        return Filter(self.ops + other.ops, self.xarr & other.xarr)
    def __or__(self, other):
        # FIXME: first arg is lying
        return Filter(self.ops + other.ops, self.xarr | other.xarr)
    def __repr__(self):
        return f'{self.ops} - {self.size}'
    @property
    def size(self):
        same_card = (all_pairs.leftnum == all_pairs.rightnum) & (all_pairs.rightsuit == all_pairs.leftsuit)

        x = self.xarr & 1-same_card
        return x.sum().item()
    
    def size_ok(self):
        return 270 < self.size < 405

    def lonely_sides(self):
        sides = Counter([side for side, *_ in self.ops])
        return [s for s, c in sides.items() if c == 1]

    def as_text(self):
        left_words = [o.word for o in self.left_ops]
        ocmp_words = [o.word for o in self.ocmp_ops]
        right_words = [o.word for o in self.right_ops]
        left_chunk = ', '.join(ocmp_words + left_words)
        right_chunk = ', '.join(right_words)
        all_chunks = ["You may not play a", right_chunk, "card on a", left_chunk, "card"]
        return " ".join([c for c in all_chunks if c])


def nullities(xarr):
    # want to check it does not make it impossible to place or place on certain cards
    # FIXME: it's also bad if some cards have very few ways to play on them
    return xarr.all('leftnum').all('leftsuit').any().item() or xarr.all('rightnum').all('rightsuit').any().item()


def unify(ops):
    ret = []
    for o in ops:
        dominated = False
        for stricter in o.overlaps():
            if stricter in ops:
                dominated = True
        if not dominated:
            ret.append(o)
    return tuple(sorted(ret))

FILTERS = [Filter([o], o.xarr()) for o in ALL_OPS]
FILTERS_BY_NAME = {list(f.ops)[0]:f for f in FILTERS}

def test_sizes():
    assert FILTERS_BY_NAME[('ocmp', 'color', '==')].size == 1300
    assert FILTERS_BY_NAME[('ocmp', 'color', '!=')].size == 2704 / 2
    assert FILTERS_BY_NAME[('ocmp', 'suit', '==')].size == 624
    assert FILTERS_BY_NAME[('ocmp', 'num', '>')].size == 4 * 4 * 12 * 13 / 2
    assert FILTERS_BY_NAME[('left', 'num', (1,3,5,7,9,11,13))].size == 7 * 4 * 51
    assert FILTERS_BY_NAME[('right', 'num', (2,4,6,8,10,12))].size == 6 * 4 * 51
    assert FILTERS_BY_NAME[('left', 'suit', ('D', 'H'))].size == 26 * 51
    assert FILTERS_BY_NAME[('right', 'suit', ('C',))].size == 13 * 51

def test_nullities():
    zeroes = all_pairs * 0
    assert not nullities(zeroes)
    zeroes.loc[{'leftsuit':'H', 'leftnum':13}] = 1
    assert nullities(zeroes)
    zeroes = all_pairs * 0

    zeroes.loc[{'leftsuit':list(SUITS)}] = 1
    assert nullities(zeroes)

    op = ('right', 'suit', ('D', 'H'))
    f = FILTERS_BY_NAME[op]
    other_op = ('right', 'suit', ('C', 'S'))
    other_f = FILTERS_BY_NAME[other_op]
    assert nullities((f | other_f).xarr)


from itertools import combinations
import random
def cards():
    combos = list(combinations(ALL_OPS, 3))
    random.shuffle(combos)
    blacklist = set()
    for c in combos:
        ops = tuple(sorted(unify(c)))
        if ops in blacklist:
            continue
        elif Op.clashes(ops):
            continue
        else:
            enemies = sum([o.disjoints() + o.bad_representations() for o in ops], [])
            if len(set(enemies) & set(ops)) > 1:
                continue
            f = Filter.from_ops(c)
            if f.size_ok() and not nullities(f.xarr):
                for i, this_op in enumerate(ops):
                    if this_op.side in f.lonely_sides():
                        for a in this_op.complements():
                            new_ops = [*ops]
                            new_ops[i] = a
                            blacklist.add(tuple(sorted(new_ops)))
                yield f


c = list(cards())
# at ~156 rules. 0.66% of rule pairings have high overlap
# excluding the worst behaving rules brought this down to 0.26%

# bad_pairs = set()
# for i in range(len(c)):
#     for j in range(i+1, len(c)):
#         overlap = (c[i].xarr & c[j].xarr).sum().item()
#         if overlap > 51*52/16:
#             bad_pairs.add((i,j))
# to_remove_list = []
# for i in range(41):
#     w = Counter(sum(bad_pairs, ()))
#     to_remove = w.most_common(n=1)[0][0]
#     to_remove_list.append(to_remove)
#     bad_pairs = [b for b in bad_pairs if to_remove not in b]
# good_indices = set(range(len(c))) - set(to_remove_list)
# q = [(c[left].xarr & c[right].xarr).sum().item() for left in good_indices for right in good_indices if right > left]
# e = Counter(q)
# sorted(e.items())
# q = [(c[left].xarr & c[right].xarr).sum().item() for left in range(len(c)) for right in range(len(c)) if right > left]
# e = Counter(q)
# sorted(e.items())
