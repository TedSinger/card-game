import itertools
import random


def card_to_unicode(number, suit):
    suit_offset = {"S": 0, "C": 3, "D": 2, "H": 1}[suit]
    number_offset = number + (
        number > 11
    )  # the unicode symbol range includes chevaliers, which aren't in our deck
    symbol_range_start = 0x1F0A0
    return chr(symbol_range_start + 16 * suit_offset + number_offset)


def card_to_svg(number, suit, x, y):
    # TODO: shadows
    rx = x
    ry = y + 4
    rect = (
        f'<rect x="{rx}" y="{ry}" rx="5" ry="5" width="80" height="110" fill="white"/>'
    )
    tx = x - 11
    ty = y + 94
    ch = card_to_unicode(number, suit)
    color = {"S": "#00377B", "C": "#004900", "H": "#B3005D", "D": "#9A4700"}[suit]
    text = f'<text x="{tx}" y="{ty}" fill="{color}" font-size="100">{ch}</text>'
    return rect + "\n" + text


class Example:
    def __init__(self, lastnum, lastsuit, newnum, newsuit):
        self.lastnum = lastnum
        self.lastsuit = lastsuit
        self.newnum = newnum
        self.newsuit = newsuit

    def __repr__(self):
        return f"{card_to_unicode(self.lastnum, self.lastsuit)}->{card_to_unicode(self.newnum, self.newsuit)}"

    def as_svg_elems(self, x, y):
        return (
            card_to_svg(self.lastnum, self.lastsuit, x, y + 60)
            + "\n"
            + card_to_svg(self.newnum, self.newsuit, x + 50, y)
        )


class ExampleFinder:
    def __init__(self):
        all_pairs = list(itertools.product(range(1, 14), "SHDC", range(1, 14), "SHDC"))
        random.shuffle(all_pairs)
        self._pairs = itertools.cycle(all_pairs)

    def _find(self, xarr):
        for lastnum, lastsuit, newnum, newsuit in self._pairs:
            if (
                xarr.loc[
                    {
                        "lastnum": lastnum,
                        "newnum": newnum,
                        "lastsuit": lastsuit,
                        "newsuit": newsuit,
                    }
                ]
                .sum()
                .item()
            ):
                return (lastnum, lastsuit, newnum, newsuit)

    def get_examples(self, f):
        # FIXME: would like the set of examples to have as few differences as possible
        true_example = self._find(f.xarr)
        examples = [Example(*true_example)]
        for cond in f.conds:
            other_conds = [c for c in f.conds if c != cond]
            xarr = 1 - cond.xarr()
            for c in other_conds:
                xarr &= c.xarr()
            if xarr.any():
                # last low, >, new low will have no counterexamples violating only new low
                # FIXME: last DH, suit==, new DH doesn't get the full suite of counterexamples, but it could
                false_example = self._find(xarr)
                examples.append(Example(*false_example))
        return examples
