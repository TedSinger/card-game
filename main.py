from collections import Counter
from ops import ALL_OPS, Op, all_pairs, SUITS

class Filter:    
    def __init__(self, ops, xarr):
        self.ops = unify_recursive(ops)
        assert isinstance(self.ops, tuple)
        assert all(isinstance(o, Op) for o in self.ops)
        self.left_ops = [o for o in ops if o.side == 'left']
        self.ocmp_ops = [o for o in ops if o.side == 'ocmp']
        self.right_ops = [o for o in ops if o.side == 'right']
        self.xarr = xarr

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

    def ocmp_num_clash(self):
        if self.ocmp_ops:
            # low <
            biased_sides = set()
            right_features = 0
            for side, kind, cond in self.ops:
                if kind == 'num' and side != 'ocmp':
                    if 7 < min(cond) or 8 > max(cond):
                        biased_sides.add(side)
                if side == 'right' or (side == 'ocmp' and kind != 'num'):
                    right_features += 1
            if len(biased_sides) % 2 == 1:
                # (('left', 'num', 'low'), ('ocmp', 'num', '<'))
                # kinda redundant
                return True
            elif right_features == 0:
                # (('left', 'suit', ('C',)), ('ocmp', 'num', '<'))
                # very difficult to play anything on 1C
                return True
            else:
                return False
        else:
            return False
    def omcp_suit_clash(self):
        if ('ocmp', 'color', '!=') in self.ops and ('ocmp', 'suit', '==') in self.ops:
            return True
        ocmp_color = False
        side_color = False
        for side, kind, _ in self.ops:
            if side == 'ocmp' and kind in ('color', 'suit'):
                ocmp_color = True
            if side in ('left', 'right') and kind == 'suit':
                side_color = True
        return ocmp_color and side_color

    def as_text(self):
        left_words = [o.word for o in self.left_ops]
        ocmp_words = [o.word for o in self.ocmp_ops]
        right_words = [o.word for o in self.right_ops]
        left_chunk = ', '.join(left_words)
        right_chunk = ', '.join(ocmp_words + right_words)
        all_chunks = ["You may not play a", left_chunk, "card on a", right_chunk, "card"]
        return " ".join([c for c in all_chunks if c])


def nullities(xarr):
    # want to check it does not make it impossible to place or place on certain cards
    # FIXME: it's also bad if some cards have very few ways to play on them
    return xarr.all('leftnum').all('leftsuit').any().item() or xarr.all('rightnum').all('rightsuit').any().item()

def unify(a, b):
    # FIXME: high/face on a low
    if a.side == b.side and a.side in ['left', 'right']:
        if a.kind == 'suit' == b.kind:
            return [Op(a.side, a.kind, tuple(sorted(set(a.what) & set(b.what))))]
        elif a.kind == 'num' == b.kind:
            if {a.what, b.what} == {(11,12,13), (8,9,10,11,12,13)}:
                return [Op(a.side, a.kind, (11,12,13))]
            elif {a.what, b.what} == {(4,8,12), (2,4,6,8,12)}:
                return [Op(a.side, a.kind, (4,8,12))]
            else:
                return [a, b]
    return [a,b]

def unify_recursive(ops):
    for i, lop in enumerate(ops):
        for j, rop in enumerate(ops):
            if i < j:
                u = unify(lop, rop)
                if len(u) == 1:
                    return unify_recursive(u + [o for k, o in enumerate(ops) if k != i and k != j])
    return tuple(sorted(set(ops)))
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

CLASHES = {}

def opposite(op):
    return (op.side, op.kind, tuple(sorted(set(SUITS) - set(op.what))))

def clashes(op):
    if not op in CLASHES:
        ret = set()
        if op.side in ('left', 'right') and op.kind == 'suit':
            return [opposite(op)]
        elif op.side == 'ocmp' and op.kind == 'num':
            return [('ocmp', 'num', '<>'['><'.index(op.what)])]
        elif op in FILTERS_BY_NAME:
            this_f = FILTERS_BY_NAME[op]
        else:
            return []
        size = this_f.size
        for other_op, other_f in FILTERS_BY_NAME.items():
            if other_op != op:
                orred = this_f | other_f
                if orred.xarr.all().item() or orred.size == size or orred.size == other_f.size:
                    ret.add(other_op)
        CLASHES[op] = ret
    return CLASHES[op]

def test_clashes():
    o = ('left', 'suit', ('D', 'H'))
    assert ('left', 'suit', ('C', 'S')) in clashes(o)

from itertools import combinations
import random
def cards():
    returned_keys = set()
    combos = list(combinations(FILTERS, 3))
    random.shuffle(combos)
    blacklist = set()
    for c in combos:
        ops = tuple(sorted(unify_recursive([o for f in c for o in f.ops])))
        if ops in blacklist:
            continue
        elif any(((o.side != 'ocmp') and (o.kind == 'num') and (len(o.what) < 3) for o in ops)):
            # a restriction to just two allowed numbers is not ok. face & odd -> (11, 13) for example
            continue
        else:
            f = c[0] & c[1] & c[2]
            if f.size_ok() and not nullities(f.xarr) and not f.ocmp_num_clash() and not f.omcp_suit_clash():
                for i, this_op in enumerate(ops):
                    if this_op.side in f.lonely_sides():
                        for a in clashes(this_op):
                            new_ops = [*ops]
                            new_ops[i] = a
                            blacklist.add(tuple(sorted(new_ops)))
                if f.ops not in returned_keys:
                    returned_keys.add(f.ops)
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
