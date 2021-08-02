from math import pi, cos, sin, floor
import sys

rnd_seed = 0xc0ffee
web_dim = 36
web_density = .05
pits_density = .1
bats_density = .15

def initconst(seed, dim, w_d, p_d, b_d):
  global rnd_seed, web_dim, web_density, pits_density, bats_density
  
  rnd_seed     = seed
  web_dim      = dim
  web_density  = w_d
  pits_density = p_d
  bats_density = b_d

# Implémentation de fonctions personnalisé de random

def rnd():
  global rnd_seed
  rnd_max = 0x7fff
  rnd_seed = (rnd_seed * 214013 + 2531011) % 4294967296
  return ((rnd_seed // (2*rnd_max + 1)) & rnd_max)

def random():
  return rnd() / 0x7fff

def randint(a,b):
  return rnd() % (b-a+1) + a

def choice(l):
  return l[randint(0, len(l)-1)]

# Fin de l'implémentation

screen_h = 240
m_p, m_l, m_k, m_b, m_d, m_a, m_m = 1, 4, 16, 64, 256, 1024, 4096

def insertinto(l1, l2):
  for v in l1:
    if v not in l2:
      l2.append(v)
  return l2

def removefrom(l1, l2):
  for v in l1:
    try:
      l2.remove(v)
    except:
      pass
  return l2

def connectPlatforms(s1, s2):
  global web
  web[s1][s2], web[s2][s1] = 1, 1

def get_reachable_platforms_from_platforms(l, safe):
  lv = []
  for s in l:
    for i in range(dimweb):
      if web[s][i]:
        if i not in lv and (not(safe) or not (platforms[i] & m_p)):
          lv.append(i)
  return lv

def cango(s1, s2, safe):
  lvo1, lvi1, lvo2, lvi2, t_inter, k = [], [s1], [], [s2], 0, 0
  while not (t_inter) and len(lvi1) and len(lvi2):
    lvo1, lvo2 = insertinto(lvo1, lvi1), insertinto(lvo2, lvi2)
    for v in lvo1:
      if v in lvo2:
        return k
    lvi1, lvi2 = get_reachable_platforms_from_platforms(lvo1, safe), get_reachable_platforms_from_platforms(lvo2, safe)
    lvi1, lvi2 = removefrom(lvo1, lvi1), removefrom(lvo2, lvi2)
    k += 1
  return 0

def my_bitor(a, b):
  return ~(~a & ~b)

def init_web(d, p_p, p_b):
  global web, platforms, screen_h
  l0 = list(range(dimweb))
  l0.remove(0)
  web, platforms, conn, dconn, i_k = [], [0 for k in range(dimweb)], [0], list(range(1, dimweb)), choice(l0)
  for j in range(dimweb):
    web.append([0 for k in range(dimweb)])
  while len(dconn):
    s = dconn[randint(0, len(dconn) - 1)]
    connectPlatforms(conn[randint(0, len(conn) - 1)], s)
    dconn.remove(s)
    conn.append(s)
  for j in range(dimweb-1):
    for i in range(j + 1, dimweb):
      if floor(d + random()):
        connectPlatforms(i, j)
  i_d = choice(l0)
  platforms[i_d] = my_bitor(platforms[i_d], m_d)
  l1 = list(l0)
  for v in get_reachable_platforms_from_platforms([0], 0):
    l1.remove(v)
  if not(len(l1)):
    l1 = l0
  l2 = list(l1)
  for v in get_reachable_platforms_from_platforms(get_reachable_platforms_from_platforms([0], 0), 0):
    try:
      l2.remove(v)
    except:
      pass
  if not(len(l2)):
    l2 = l1
  i_l = choice(l2)
  platforms[i_l] = my_bitor(platforms[i_l], m_l)
  platforms[i_k] = my_bitor(platforms[i_k], m_k)
  for i in l1:
    if i != i_k and i != i_d and floor(p_p*dimweb/len(l1) + random()):
      if cango(0, i_k, 1) and cango(0, i_d, 1):
        platforms[i] = my_bitor(platforms[i], m_p)
    if floor(p_b*dimweb/len(l1) + random()):
      platforms[i] = my_bitor(platforms[i], m_b)

def parcourir_selon(ia):
  global dimweb, platforms, web_dim, web_density, pits_density, bats_density
  dimweb = web_dim
  maxcoups = dimweb**2 * 2
  init_web(web_density, pits_density, bats_density)

  s0, s1, s2, s3, s4, s5, s6, s7 = 0, 0, m_a, 0, 1, -1, 0, 0
  pfs0, pfs5 = platforms[s0], 0
  while s4 > 0  and (not (s2 & (2 * m_k)) or not (pfs0 & m_d)):
    if s5 < 0:
      s5 = 0
    else:
      try:
        k, k2 = ia(s0, voisines, dimweb, s1, s2)
        if pfs5 & (2 * m_b):
          while s0 == s5:
            s0 = randint(0, dimweb - 1)
          pfs0, pfs5 = my_bitor(platforms[s0], m_b), pfs5 & ~(3 * m_b) & ~m_m
        else:
          if k2:
            if s2 & m_a:
              v = platforms[k]
              if v & m_l:
                v, s2 = v & ~m_l, my_bitor(s2, 2 * m_l)
                platforms[k] = my_bitor(v, 2 * m_l)
              s2 = s2 & ~m_a
              s2 = my_bitor(s2, 2 * m_a)
          else:
            if k in voisines:
              s0 = k
              if pfs5 & m_b:
                pfs5 = my_bitor(pfs5, 2 * m_b)
              pfs0, pfs5 = platforms[s0], pfs5 & ~m_m
          s3 += 1
          if s3 >= maxcoups:
            s4 = 0
        if pfs0 & m_k:
          pfs0 = pfs0 & ~m_k
          s2 = my_bitor(s2, 2 * m_k)
        if pfs0 & my_bitor(m_p, m_l):
          s4 = 0
          pfs0 = my_bitor(pfs0, 2 * m_m)
        platforms[s5] = pfs5
      except Exception as t_excpt:
        s4 = -1
        print(t_excpt)
    pfs0 = my_bitor(pfs0, m_m)
    s1, voisines = pfs0, get_reachable_platforms_from_platforms([s0], 0)
    platforms[s0] = pfs0
    for v in voisines:
      t = my_bitor(m_p, m_l)
      t = platforms[v] & my_bitor(t, m_k)
      s1 = my_bitor(s1, t)
    for v in get_reachable_platforms_from_platforms(voisines, 0):
      t = platforms[v] & m_l
      s1 = my_bitor(s1, t)
    s5, s6, s7, pfs5 = s0, s1, s2, pfs0
  r = s4 > 0 and s3 < maxcoups
  s1 = 0
  if not r:
    if pfs0 & m_l:
      s1 |= 2
    elif pfs0 & m_p:
      s1 |= 1
    elif s3 >= maxcoups:
      s1 |= 8
    elif s4 < 0:
      s1 |= 4
  return r, s1, s2, s3
