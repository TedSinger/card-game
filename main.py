from collections import Counter
from ops import ALL_OPS, Op, all_pairs, ADJECTIVE_ORDER
from itertools import combinations
import random


class Rule:
    def __init__(self, ops, xarr):
        self.ops = unify(ops)
        assert isinstance(self.ops, tuple)
        assert all(isinstance(o, Op) for o in self.ops)
        self.last_ops = [o for o in self.ops if o.side == "last"]
        self.ocmp_ops = [o for o in self.ops if o.side == "ocmp"]
        self.new_ops = [o for o in self.ops if o.side == "new"]
        self.xarr = xarr

    @classmethod
    def from_ops(self, ops):
        xarr = ops[0].xarr().copy()
        for o in ops[1:]:
            xarr &= o.xarr()
        return Rule(ops, xarr)

    def __and__(self, other):
        return Rule(self.ops + other.ops, self.xarr & other.xarr)

    def __repr__(self):
        return f"{self.ops} - {self.size}"

    @property
    def size(self):
        same_card = (all_pairs.lastnum == all_pairs.newnum) & (
            all_pairs.newsuit == all_pairs.lastsuit
        )
        x = self.xarr & 1 - same_card
        return (x.sum().item() + self.xarr.sum().item()) / 2

    def size_ok(self):
        return 270 < self.size < 405

    def lonely_sides(self):
        sides = Counter([side for side, *_ in self.ops])
        return [s for s, c in sides.items() if c == 1]

    def is_conditional(self):
        return self.ocmp_ops or (self.last_ops and self.new_ops)

    def as_text(self):
        last_words = sorted([o.word for o in self.last_ops], key=ADJECTIVE_ORDER.index)
        new_words = sorted([o.word for o in self.new_ops], key=ADJECTIVE_ORDER.index)
        for o in self.ocmp_ops:
            if len(last_words) < len(new_words):
                last_words.insert(0, o.last_word())
            else:
                new_words.insert(0, o.new_word())
        last_chunk = _fmt_words(last_words)
        new_chunk = _fmt_words(new_words)
        all_chunks = ["You may not play", new_chunk, "on", last_chunk]
        return " ".join([c for c in all_chunks if c])

    def as_svg(self, e):
        # TODO: background template
        # TODO: top text scaled, font, legible
        # TODO: big red NO sign
        # TODO: ok_examples spaced nicely
        illegal_example, *ok_examples = e.get_examples(self)
        header = """<svg width="889" height="571">
            <rect x="5" y="5" rx="5" ry="5" width="879" height="161" fill="peachpuff"/>
            <rect x="5" y="171" rx="5" ry="5" width="437" height="395" fill="skyblue"/>
            <rect x="447" y="171" rx="5" ry="5" width="437" height="395" fill="tan"/>"""
        text = f'<text x="50%" y="85" font-size="40" text-anchor="middle">{self.as_text()}</text>'
        i = illegal_example.as_svg_elems(447 / 2 - 65, 405 / 2 - 85 + 166)
        es = [
            o.as_svg_elems(500 + 100 * i, 200 + 100 * i)
            for i, o in enumerate(ok_examples)
        ]
        footer = "</svg>"
        return "\n".join([header, text, i, *es, footer])


def _fmt_words(words):
    joiner = ", " if len(words) > 2 else " "
    chunk = joiner.join(words)
    particle = "an" if words[0] in ("even", "odd") else "a"
    chunk = particle + " " + chunk
    omit_card = words[-1] in ("spade", "heart", "diamond", "club")
    if not omit_card:
        chunk += " card"
    return chunk


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


def gen_rules():
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
            f = Rule.from_ops(c)
            if f.size_ok() and f.is_conditional():
                for i, this_op in enumerate(ops):
                    if this_op.side in f.lonely_sides():
                        for a in this_op.complements():
                            blacklist_ops = [*ops]
                            blacklist_ops[i] = a
                            blacklist.add(tuple(sorted(blacklist_ops)))
                yield f


RULES = list(gen_rules())
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
# q = [(c[last].xarr & c[new].xarr).sum().item() for last in good_indices for new in good_indices if new > last]
# e = Counter(q)
# sorted(e.items())
# q = [(c[last].xarr & c[new].xarr).sum().item() for last in range(len(c)) for new in range(len(c)) if new > last]
# e = Counter(q)
# sorted(e.items())
