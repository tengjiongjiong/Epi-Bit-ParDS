from functools import lru_cache
import random

import numpy as np

from bch_class import GF, BCH


DATA_BITS = 91
CODEWORD_BITS = 255

random.seed(1)


@lru_cache(maxsize=1)
def _coder():
    return BCH(GF(8, useLUT=0), 24)


def bchencode(seq):
    word = np.fromiter(seq, dtype=int)
    encoded = "".join(_coder().Encode(word).astype(str).tolist())
    print(encoded)
    return encoded


def bchdecode(inplist):
    codeword = np.asarray(inplist, dtype=int)
    return "".join(_coder().Decode(codeword).astype(str).tolist())
