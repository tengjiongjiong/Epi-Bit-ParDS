# -*- coding: utf-8 -*-
"""
Created on Mon Aug 12 10:29:13 2024

@author: Fajia Sun
"""

import numpy as np
import random
import time

def pseudo(length):
    lp = []
    for i in range(length):
        lp.append(random.randint(0,1))
    lp = [str(_) for _ in lp]
    return ''.join(lp)

def consec(lt):
    lt = [str(_) for _ in lt]
    stream = ''.join(lt)
    if '11111' in stream:
        return False
    else:
        return True

def sparse_seq(seq):
    lt = [int(_) for _ in seq]
    for i in range(100000):
        ls = []
        rng = np.random.RandomState(i)
        ranseq = list(rng.randint(2, size=len(lt)))
        for j in range(len(lt)):
            ls.append((lt[j] + ranseq[j]) % 2)
        #print(ls.count(1), consec(ls), end=' ')
        if ls.count(1) <= 100 and consec(ls):
            #print(ls.count(1))
            ls = [str(_) for _ in ls]
            sparsed = ''.join(ls)
            return i, sparsed
            break
    return False