import itertools
import random

class Example:
    def __init__(self, inverted_ops, lastnum, lastsuit, newnum, newsuit):
        self.lastnum = lastnum
        self.lastsuit = lastsuit
        self.newnum = newnum
        self.newsuit = newsuit
        self.inverted_ops = inverted_ops

    def __repr__(self):
        return f"{self.lastnum}{self.lastsuit}->{self.newnum}{self.newsuit}, {self.inverted_ops}"

    def as_text(self):
        return f""

class ExampleFinder:
    def __init__(self):
        all_pairs = list(itertools.product(range(1,14), "SHDC", range(1,14), "SHDC"))
        random.shuffle(all_pairs)
        self._pairs = itertools.cycle(all_pairs)

    def _find(self, xarr):
        for (lastnum, lastsuit, newnum, newsuit) in self._pairs:
            if xarr.loc[{'lastnum':lastnum,'newnum':newnum,'lastsuit':lastsuit,'newsuit':newsuit}].sum().item():
                return (lastnum, lastsuit, newnum, newsuit)

    def get_examples(self, f):
        # FIXME: would like the set of examples to have as few differences as possible
        true_example = self._find(f.xarr)
        examples = [Example([], *true_example)]
        for op in f.ops:
            other_ops = [o for o in f.ops if o != op]
            xarr = 1 - op.xarr()
            for o in other_ops:
                xarr &= o.xarr()
            if xarr.any():
                # last low, >, new low will have no counterexamples violating only new low
                # FIXME: last DH, suit==, new DH doesn't get the full suite of counterexamples, but it could
                false_example = self._find(xarr)
                examples.append(Example([op], *false_example))
        return examples