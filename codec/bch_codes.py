import random
import numpy as np

from bch_class import GF, BCH

random.seed(1)

def bchencode(seq):

    q = 8
    t = 24
    n = 2 ** q - 1
    
    field = GF(q, useLUT=0)
    coder = BCH(field, t)
    
    lt = list(seq)
    lt = [int(_) for _ in lt]
    
    code_word = coder.Encode(np.array(lt))
    array = np.array(code_word).astype(int)
    la = list(array)
    la = [str(_) for _ in la]
    
    print(''.join(la))
    
    return ''.join(la)


def bchdecode(inplist):

    q = 8
    t = 24
    n = 2 ** q - 1
    
    field = GF(q, useLUT=0)
    coder = BCH(field, t)
    
    broken_code_word = np.array(inplist).astype(int)
    
    decode = coder.Decode(broken_code_word)
    
    return ''.join(decode.astype(str).tolist())

