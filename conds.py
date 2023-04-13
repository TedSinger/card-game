import xarray as xr
from collections import Counter, namedtuple
from itertools import combinations


class Cond(namedtuple("Cond", ["side", "kind", "what"])):
    # FIXME: maybe START with the word and lookup the implementation
    @property
    def word(self):
        if self.side == "comp":
            if self.kind == "num":
                # the word is describing the last card
                return "lower" if self.what == "<" else "higher"
            else:
                return (
                    f"different {self.kind}"
                    if self.what == "!="
                    else f"same {self.kind}"
                )
        else:
            return [k for k, v in WORDS.items() if v == self.what][0]

    def last_word(self):
        if self.what == "<":
            return "lower"
        elif self.what == ">":
            return "higher"
        else:
            return self.word

    def new_word(self):
        if self.what == "<":
            return "higher"
        elif self.what == ">":
            return "lower"
        else:
            return self.word

    def xarr(self):
        if not hasattr(self, "_xarr"):
            x = all_pairs.copy()
            if self.side == "comp":
                if self.kind == "num":
                    if self.what == ">":
                        mask = x.lastnum > x.newnum
                    else:
                        mask = x.lastnum < x.newnum
                elif self.kind == "suit":
                    if self.what == "==":
                        mask = x.lastsuit == x.newsuit
                    else:
                        mask = x.lastsuit != x.newsuit
                else:  # color
                    mask = x.lastsuit.isin(["C", "S"]) ^ x.newsuit.isin(["C", "S"])
                    if self.what == "==":
                        mask = 1 - mask
                x &= mask
            else:
                x *= 0
                x.loc[{f"{self.side}{self.kind}": list(self.what)}] = 1
                x &= all_pairs
            self._xarr = x
        return self._xarr

    @classmethod
    def clashes(cls, conds) -> bool:
        # various pathologies. causes some cards to be too difficult to play on
        last_conds = [c for c in conds if c.side == "last"]
        comp_conds = [c for c in conds if c.side == "comp"]
        new_conds = [c for c in conds if c.side == "new"]
        for group in last_conds, new_conds:
            for op1, op2 in combinations(group, 2):
                if op1.kind == op2.kind == "num":
                    if len(set(op1.what) & set(op2.what)) < 3:
                        # Ex. even high card -> (12,), confusingly narrow
                        return True
        if (11, 12, 13) in what(conds) and ("<" in what(conds) or ">" in what(conds)):
            return True
        elif (
            len(comp_conds) == 1
            and comp_conds[0].kind == "num"
            and last_conds
            and not new_conds
        ):
            # Motivation: "You may not play a higher card on a spade" - well then what to do on low spade?
            allowed_numbers = set(range(1, 14))
            for c in last_conds:
                if c.kind == "num":
                    allowed_numbers &= set(c.what)
            comp = comp_conds[0]
            if comp.what == "<":
                return min(allowed_numbers) < 4
            else:
                return max(allowed_numbers) > 10
        else:
            # last_conds and new_conds -> conditions on both sides. no pathologies
            # new_conds and not last_conds -> it's actually ok for some cards to be nearly unplayable.
            # it is the player's job to identify and get rid of those
            return False

    def bad_representations(self) -> list["Cond"]:
        if self.side == "comp" and self.kind == "color":
            # same/different color on a spade -> red/black on a spade
            # len(suits) <= 2 is an awful hack
            return [
                Cond(side, "suit", suits)
                for word, suits in WORDS.items()
                for side in ("last", "new")
                if len(suits) <= 2
            ]
        elif self.kind == "suit":
            return [
                Cond("comp", "color", "=="),
                Cond("comp", "color", "!="),
                Cond("comp", "suit", "=="),
            ]
        else:
            return []

    def overlaps(self) -> list["Cond"]:
        # Any Cond that is stricter than this one
        # this & other == other and this | other == this
        if self.what == ("D", "H"):
            return [Cond(self.side, self.kind, ("D",)), Cond(self.side, self.kind, ("H",))]
        elif self.what == ("C", "S"):
            return [Cond(self.side, self.kind, ("C",)), Cond(self.side, self.kind, ("S",))]
        elif self.side == "comp" and self.kind == "color" and self.what == "==":
            return [Cond(self.side, "suit", "==")]
        elif self.word == "high":
            return [Cond(self.side, self.kind, (11, 12, 13))]
        elif self.word == "even":
            return [Cond(self.side, self.kind, (4, 8, 12))]
        else:
            return []

    def complements(self) -> list["Cond"]:
        # Any Cond that is the opposite of this one
        # this & other == null and this | other == all
        pairs = [
            (">", "<"),
            (tuple(range(1, 14))[::2], tuple(range(1, 14))[1::2]),
            (tuple(range(8, 14)), tuple(range(1, 8))),
            (("C", "S"), ("D", "H")),
        ]
        for last, new in pairs:
            if self.what == last:
                return [Cond(self.side, self.kind, new)]
            elif self.what == new:
                return [Cond(self.side, self.kind, last)]
        if self.kind == "color":
            return [Cond(self.side, self.kind, "==" if self.what == "!=" else "!=")]
        return []

    def disjoints(self) -> list["Cond"]:
        # this & other == null
        ret = []
        if self.side == "comp":
            if self.kind == "color" and self.what == "!=":
                ret.append(Cond(self.side, "suit", "=="))
            elif self.kind == "suit" and self.what == "==":
                ret.append(Cond(self.side, "color", "!="))
        elif self.kind == "suit":
            # len(suit) < 3 is an awful hack
            ret.extend(
                [
                    Cond(self.side, "suit", suit)
                    for word, suit in WORDS.items()
                    if len(set(suit) & set(self.what)) == 0 and len(suit) < 3
                ]
            )
        elif self.what == (11, 12, 13):
            ret.append(Cond(self.side, "num", tuple(range(1, 8))))
        elif self.what == tuple(range(1, 8)):
            ret.append(Cond(self.side, "num", (11, 12, 13)))
        return ret + self.complements()


def what(conds):
    return [c.what for c in conds]


all_pairs = xr.DataArray(
    data=[[[[1] * 4] * 13] * 4] * 13,
    coords={
        "lastnum": range(1, 14),
        "newnum": range(1, 14),
        "lastsuit": ["S", "H", "C", "D"],
        "newsuit": ["S", "H", "C", "D"],
    },
    dims=("lastnum", "lastsuit", "newnum", "newsuit"),
)


WORDS = {
    "odd": tuple(range(1, 14))[::2],
    "even": tuple(range(1, 14))[1::2],
    "high": tuple(range(8, 14)),
    "low": tuple(range(1, 8)),
    "face": (11, 12, 13),
    # 'quartet': (4, 8, 12), these give about 16 new rules, total. not necessary or worth the player confusion
    # 'trio': (3, 6, 9, 12),
    "spade": ("S",),
    "club": ("C",),
    "diamond": ("D",),
    "heart": ("H",),
    "red": ("D", "H"),
    "black": ("C", "S"),
}

ADJECTIVE_ORDER = [
    "high",
    "low",
    "odd",
    "even",
    "red",
    "black",
    "quartet",
    "trio",
    "spade",
    "heart",
    "diamond",
    "club",
    "face",
]


ALL_OPS = []
for side in ["last", "new"]:
    for name, vals in WORDS.items():
        kind = "num" if len(vals) >= 3 else "suit"
        c = Cond(side, kind, vals)
        ALL_OPS.append(c)
ALL_OPS.extend(
    [
        Cond("comp", "num", ">"),
        Cond("comp", "num", "<"),
        Cond("comp", "suit", "=="),
        Cond("comp", "color", "!="),
        Cond("comp", "color", "=="),
    ]
)
