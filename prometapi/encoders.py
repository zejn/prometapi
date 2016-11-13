# coding: utf-8

import math


def rshift(val, n):
    if val >= 0:
        val2 = val >> n
    else:
        val2 = val + 0x100000000 >> n
    return val2


def str_to_longs(e):
    t = []
    pad = len(e) % 4
    if pad != 0:
        e = e + (4 - pad) * '\x00'
    
    array_len = math.ceil(len(e)/4.0)
    r = 0
    while r < array_len:
        t.append(
            ord(e[4*r]) +
            (ord(e[4*r + 1]) << 8) +
            (ord(e[4*r + 2]) << 16) +
            (ord(e[4*r + 3]) << 24)
        )
        r += 1
    return t


def longs_to_str(e):
    t = []
    for a in e:
        s = chr(255 & a) + chr(a >> 8 & 255) + chr(a >> 16 & 255) + chr(a >> 24 & 255)
        t.append(s)
    return ''.join(t)


def encrypt(e, t):
    r = str_to_longs(e)
    a = str_to_longs(t)
    if len(r) <= 1:
        r = [r[0], 0]
    
    l = len(r)
    g = r[l - 1]
    s = r[0]
    i = 2654435769
    c = math.floor(6 + 52 / l)
    u = 0
    
    while c > 0:
        u += i
        n = rshift(u, 2) & 3
        
        p = 0
        while l > p:
            s = r[(p + 1) % l]
            o = (rshift(g, 5) ^ ((s << 2) & 0xffffffff) ) + (rshift(s, 3) ^ ((g << 4) & 0xffffffff)) ^ (u ^ s) + (a[3 & p ^ n] ^ g)
            g = r[p] = (r[p] + o) & 0xffffffff
            
            p += 1
        c -= 1
    f = longs_to_str(r)
    return f


def decrypt(e, t):
    o = str_to_longs(e)
    n = str_to_longs(t)
    l = len(o)
    g = o[l - 1]
    s = o[0]
    i = 2654435769
    c = long(math.floor(6 + 52 / l))
    u = c * i
    
    while u:
        a = rshift(u, 2) & 3
        
        p = l - 1
        while p >= 0:
            if p > 0:
                g = o[p-1]
            else:
                g = o[l-1]
            
            r = (rshift(g, 5) ^ ((s << 2) & 0xffffffff)) + \
                (rshift(s, 3) ^ ((g << 4) & 0xffffffff)) ^ \
                (u ^ s) + \
                (n[3 & p ^ a] ^ g)
            s = o[p] = (o[p] - r) & 0xffffffff
            
            p -= 1
        u -= i
    
    f = longs_to_str(o)
    return f
