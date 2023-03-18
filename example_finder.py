import itertools
import random

class Example:
    def __init__(self, inverted_ops, leftnum, leftsuit, rightnum, rightsuit):
        self.leftnum = leftnum
        self.leftsuit = leftsuit
        self.rightnum = rightnum
        self.rightsuit = rightsuit
        self.inverted_ops = inverted_ops

    def __repr__(self):
        return f"{self.leftnum}{self.leftsuit}->{self.rightnum}{self.rightsuit}, {self.inverted_ops}"

    def as_text(self):
        return f""

class ExampleFinder:
    def __init__(self):
        all_pairs = list(itertools.product(range(1,14), "SHDC", range(1,14), "SHDC"))
        random.shuffle(all_pairs)
        self._pairs = itertools.cycle(all_pairs)

    def _find(self, xarr):
        for (leftnum, leftsuit, rightnum, rightsuit) in self._pairs:
            if xarr.loc[{'leftnum':leftnum,'rightnum':rightnum,'leftsuit':leftsuit,'rightsuit':rightsuit}].sum().item():
                return (leftnum, leftsuit, rightnum, rightsuit)

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
                # left low, >, right low will have no counterexamples violating only right low
                # FIXME: left DH, suit==, right DH doesn't get the full suite of counterexamples, but it could
                false_example = self._find(xarr)
                examples.append(Example([op], *false_example))
        return examples