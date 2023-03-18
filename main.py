from collections import Counter
from ops import ALL_OPS, Op, all_pairs, ADJECTIVE_ORDER
from itertools import combinations
import random


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
    def __repr__(self):
        return f'{self.ops} - {self.size}'
    @property
    def size(self):
        same_card = (all_pairs.leftnum == all_pairs.rightnum) & (all_pairs.rightsuit == all_pairs.leftsuit)
        x = self.xarr & 1-same_card
        return (x.sum().item() + self.xarr.sum().item()) / 2
    
    def size_ok(self):
        return 270 < self.size < 405

    def lonely_sides(self):
        sides = Counter([side for side, *_ in self.ops])
        return [s for s, c in sides.items() if c == 1]

    def is_conditional(self):
        return self.ocmp_ops or (self.left_ops and self.right_ops)

    def as_text(self):
        left_words = sorted([o.word for o in self.left_ops], key=ADJECTIVE_ORDER.index)
        right_words = sorted([o.word for o in self.right_ops], key=ADJECTIVE_ORDER.index)
        for o in self.ocmp_ops:
            if len(left_words) < len(right_words):
                left_words.insert(0, o.left_word())
            else:
                right_words.insert(0, o.right_word())
        left_chunk = _fmt_words(left_words)
        right_chunk = _fmt_words(right_words)
        all_chunks = ["You may not play", right_chunk, "on", left_chunk]
        return " ".join([c for c in all_chunks if c])



def _fmt_words(words):
    joiner = ', ' if len(words) > 2 else ' '
    chunk = joiner.join(words)
    particle = 'an' if words[0] in ('even', 'odd') else 'a'
    chunk = particle + ' ' + chunk
    omit_card = words[-1] in ('spade', 'heart', 'diamond', 'club')
    if not omit_card:
        chunk += ' card'
    return chunk

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
            if f.size_ok() and f.is_conditional():# and not nullities(f.xarr):
                for i, this_op in enumerate(ops):
                    if this_op.side in f.lonely_sides():
                        for a in this_op.complements():
                            new_ops = [*ops]
                            new_ops[i] = a
                            blacklist.add(tuple(sorted(new_ops)))
                yield f


FILTERS = list(cards())
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
