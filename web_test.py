# cas
from web import *
import preview_memory

PRESENCE_INCONNU = 0
PRESENCE_IMPOSSIBLE = 1
PRESENCE_POSSIBLE = 2

CHAUVE_SOURIS_REVEILLE = True
CHAUVE_SOURIS_ENDORMIE = False

PARAMETRE_VOISINES = 0
PARAMETRE_CORNICHE_VISITE = 1
PARAMETRE_PUIT = 2
PARAMETRE_CLE = 3

# Liste de uplet defini comme tel:
# - Liste des corniches voisines            : Liste
# - Defini si la corniche a deja ete visite : Boolean
# - Sensation d'un puit                     : Int
# - Sensation d'une cle                     : Int
g_corniches = None
# Raccourci vers la position de la porte
g_porte = None
# Carte des positions des chauves souris sous la forme:
# - corniche => etat
# Avec:
# - etat = 1 => Chauve souris eveille
# - etat = 0 => Chauve souris endormie
g_chauve_souris = {}
# Donne si la cle est en la possession du personnage
g_possede_cle = False
# Donne si la fleche est en possession du personnage
g_possede_fleche = True

# La position initiale de la chauve souris avant le deplacement du personnage
g_chauve_souris_initial = False
g_leviathan_initial = False

g_leviathan = {}
g_corniches_leviathan = []

# La trajectoire actuellement suivie par le personnage
g_trajectoire = None
g_trajectoire_position = 0

g_precedent = None

g_corniche_visitee = 0
g_candidat_force = None

# Pour l'initialisation, juste générer le tableau de corniches:
# g_corniches,g_porte,g_chauve_souris,g_possede_cle,g_possede_fleche,g_chauve_souris_initial,g_trajectoire,g_trajectoire_position=None,None,{},False,True,False,None,0
# Avec taille la taille du cratère (càd le nombre de corniches)

# Fonction de pathmaking
# - depart : La corniche de depart pour le personnage
# - arrivee : La corniche d'arrivee pour le personnage
# - dangers : Les corniches jugees dangereuses pour le personnage et donc a eviter
# - n : Le nombre maximal d'itération pouvant être accompli par la fonction
# Retourne l'element voisin susceptible de mener vers la corniche d'arrivee si un chemin est possible sinon None


def genere_trajectoire(depart, arrivee, dangers=[]):
    M = set()
    d = {depart: 0}
    p = {}
    suivants = [(0, depart)]
    while len(suivants) != 0:
        dx, x = heappop(suivants)
        if x in M:
            continue
        M.add(x)
        voisins = []
        if g_corniches[x] != None and g_corniches[x][PARAMETRE_CORNICHE_VISITE]:
            voisins = g_corniches[x][PARAMETRE_VOISINES]
        voisins = discrimine(voisins, dangers)
        for y in voisins:
            if y in M:
                continue
            dy = dx + 1
            if y not in d or d[y] > dy:
                d[y] = dy
                heappush(suivants, (dy, y))
                p[y] = x
    path = [arrivee]
    x = arrivee
    if x not in p:
        return None
    while x != depart:
        x = p[x]
        path.insert(0, x)
    return path


def heappush(heap, v):
    pos = len(heap)-1
    while pos >= 0 and v <= heap[pos]:
        pos -= 1
    pos += 1
    heap.insert(pos, v)


def heappop(heap):
    return heap.pop()

# Liste des corniches potentielles ou pourraient se trouver la cle


def corniche_cle():
    global g_corniches
    ret = []
    for i in range(len(g_corniches)):
        if g_corniches[i] is not None:
            if g_corniches[i][PARAMETRE_CLE] == PRESENCE_POSSIBLE:
                ret.append(i)
    return ret

# Liste les corniches dangereuses


def corniche_danger(chauve_souris=True, leviathan = True):
    global g_corniches, g_chauve_souris
    ret = []

    # Ajoute chaque puit et leviathan potentiel dans les corniches dangereuses
    for i in range(len(g_corniches)):
        if g_corniches[i] is not None and g_corniches[i][PARAMETRE_PUIT] == PRESENCE_POSSIBLE:
            ret.append(i)

    # Ajoute chaque corniche ou peux se trouver leviathan
    if g_corniches_leviathan != 0 and leviathan:
        for i in g_corniches_leviathan:
            if i not in ret:
                ret.append(i)
    # Ajoute chaque chauve souris réveillés dans les coniches dangereuses
    if chauve_souris:
        for i in g_chauve_souris.items():
            if i[1] == CHAUVE_SOURIS_REVEILLE and i[0] not in ret:
                ret.append(i[0])

    return ret

# Liste les corniches non visites


def corniche_vierge():
    global g_corniches
    ret = []

    for i in range(len(g_corniches)):
        if g_corniches[i] is not None:
            if not g_corniches[i][PARAMETRE_CORNICHE_VISITE]:
                ret.append(i)

    return ret

# Discrimine les element de L2 dans L1


def discrimine(l1, l2):
    ret = []

    for i in l1:
        if not i in l2:
            ret.append(i)

    return ret


def trajectoire_indefinie(voisines):
    global g_trajectoire, g_trajectoire_position
    return g_trajectoire is None or len(g_trajectoire) <= g_trajectoire_position or g_trajectoire[g_trajectoire_position] not in voisines

# Le personnage est sur une corniche, il memorise ce qu'il apercoit sur cette derniere ainsi que sur ses voisines
# - corniche : L'identifiant de la corniche actuelle
# - voisines : La liste des proches voisines de la corniche actuelle
# - presence_chauve_souris : Un boolean disant si une chauve souris se trouve sur la corniche ou non
# - presence_porte : Un boolean disant si une porte se trouve sur la corniche ou non
# - sensation_puit : Un boolean disant si une ou plusieurs des corniches voisines possede un puit
# - sensation_cle : Un boolean disant si l'une des corniches voisines possede la cle
# - sensation_leviathan : Un boolean disant si le personnage detecte la presence du leviathan sur une des corniches
# voisines ou une voisine de ces dernieres
#
# Si la corniche a deja ete visite, pas besoin d'effectuer l'action de memorisation


def memorisation_corniche(
    # Informations sur la corniche en elle meme
    corniche, voisines,
    # Informations sur les elements present sur la corniche
    presence_chauve_souris, presence_porte,
    # Informations sur les corniches a proximite
    sensation_puit, sensation_cle, sensation_leviathan
):
    global g_chauve_souris, g_chauve_souris_initial, g_corniches, g_corniches_leviathan, g_corniche_visitee, g_porte, g_leviathan_initial
    # Si la chauve souris a deplace le personnage sur cette corniche
    if g_chauve_souris_initial:
        if presence_chauve_souris:
            g_chauve_souris[corniche] = CHAUVE_SOURIS_REVEILLE
        elif g_precedent is not None:
            g_chauve_souris[g_precedent] = CHAUVE_SOURIS_REVEILLE
        g_chauve_souris_initial = False

    # Une chauve souris se trouve sur la corniche
    if presence_chauve_souris:
        # La chauve souris a deja ete identifie sur la corniche
        if corniche in g_chauve_souris.keys():
            # Cette derniere est endormie, la presence du personnage sur la corniche la reveille
            if g_chauve_souris[corniche] == CHAUVE_SOURIS_ENDORMIE:
                g_chauve_souris[corniche] = CHAUVE_SOURIS_REVEILLE
            # Cette derniere est reveille, elle va nous deplacer sur une nouvelle corniche ou elle se posera
            else:
                del g_chauve_souris[corniche]
                g_chauve_souris_initial = True
        # La chauve souris etait endormie mais pas encore identifiee, notre presence sur la corniche la reveille
        else:
            g_chauve_souris[corniche] = CHAUVE_SOURIS_REVEILLE
    # Si la chauve souris a deplace le personnage sur cette corniche
    if g_corniches[corniche] is None or not g_corniches[corniche][PARAMETRE_CORNICHE_VISITE]:

        g_corniche_visitee += 1
        # Une porte se trouve sur la corniche
        if presence_porte:
            g_porte = corniche
        
        # La corniche n'a ni ete identifie via les voisins, ni via la presence meme du personnage (cas du premier tour)
        g_corniches[corniche] = [
            voisines,  # Voisines de la corniche
            True,  # Dis si la corniche a deja ete visitee
            PRESENCE_IMPOSSIBLE,  # Puit
            PRESENCE_IMPOSSIBLE  # Cle
        ]

        if corniche in g_leviathan and g_leviathan[corniche] and corniche in g_corniches_leviathan:
            g_corniches_leviathan.remove(corniche)
        g_leviathan[corniche] = False

        patron_voisines = [
            [corniche],  # Voisines de la corniche
            False,  # La corniche n'est pas encore visite
            PRESENCE_POSSIBLE if sensation_puit else PRESENCE_IMPOSSIBLE,  # Puit
            PRESENCE_POSSIBLE if sensation_cle else PRESENCE_IMPOSSIBLE  # Cle
        ]

        # Met a jour les voisines a la corniche actuelle
        for i in voisines:
            # Leviathan (pour que la corniche soit identifié comme pouvant loger léviathan, la corniche précédent doit également avoir donné la sensation de léviathan)
            if i not in g_leviathan:
                if sensation_leviathan and g_leviathan_initial:
                    g_leviathan[i] = True
                    if i not in g_corniches_leviathan:
                        g_corniches_leviathan.append(i)
                else:
                    g_leviathan[i] = False
                    if i in g_corniches_leviathan:
                        g_corniches_leviathan.remove(i)
            elif not sensation_leviathan or not g_leviathan_initial:
                g_leviathan[i] = False
                if i in g_corniches_leviathan:
                    g_corniches_leviathan.remove(i)
            # On ne sais encore rien des voisines
            if g_corniches[i] is None:
                g_corniches[i] = patron_voisines.copy()
            # On sais quelque choise des voisines
            else:
                # Puit
                if not sensation_puit:
                    g_corniches[i][PARAMETRE_PUIT] = PRESENCE_IMPOSSIBLE
                # Cle
                if not sensation_cle:
                    g_corniches[i][PARAMETRE_CLE] = PRESENCE_IMPOSSIBLE
            # Traitement du cas leviathan sur les survoisines
            if sensation_leviathan:
                patron_survoisines = [
                    [i],
                    False,
                    PRESENCE_INCONNU,
                    PRESENCE_INCONNU
                ]
                for j in g_corniches[i][PARAMETRE_VOISINES]:
                    if g_corniches[j] is None:
                        g_corniches[j] = patron_survoisines.copy()
                    elif not j in g_leviathan:
                        g_leviathan[j] = True
                        if i not in g_corniches_leviathan:
                            g_corniches_leviathan.append(j)

    g_leviathan_initial = sensation_leviathan
"""
def recalculer_trajectoire(corniche, voisines, candidats, dangers):
    global g_trajectoire, g_trajectoire_position
    for i in candidats:
        if i not in dangers:
            if trajectoire_indefinie(voisines):
                tmp = genere_trajectoire(corniche, i, dangers)
                if tmp is not None:
                    g_trajectoire = tmp
                    g_trajectoire_position = 1
                    return

    if trajectoire_indefinie(voisines):
        dangers_sans_chauve_souris = corniche_danger(False)
        for i in candidats:
            if i not in dangers:
                if trajectoire_indefinie(voisines):
                    tmp = genere_trajectoire(corniche, i, dangers_sans_chauve_souris)
                    if tmp is not None:
                        g_trajectoire = tmp
                        g_trajectoire_position = 1
                        return
"""

def recalculer_trajectoire(corniche, candidats, dangers, niveau_risque, trajectoire):
    trajectoires = [None]*len(candidats)
    j = 0

    for i in discrimine(candidats, dangers):
        tmp = genere_trajectoire(corniche, i, dangers)
        if tmp is not None:
            trajectoires[j] = tmp
            j += 1
    
    if j != 0:
        return trajectoires[randint(0, j-1)], niveau_risque
    else:
        return [], niveau_risque+1


# Arbre des décisions de l'IA. Interprète les informations mémorisés afin de prendre la meilleure décision pour sortir vivant
def arbre_decision(corniche, voisines, taille):
    global g_precedent, g_corniches_leviathan, g_candidat_force, g_trajectoire_position, g_trajectoire, g_leviathan, g_possede_fleche

    precedent = g_precedent
    g_precedent = corniche

    if trajectoire_indefinie(voisines):
        candidats = []
        trajectoire = []

        niveau_risque = 0

        # La clé a été ramassée et la porte trouvée, se dirige sans problème vers la porte
        if g_possede_cle and g_porte is not None:
            candidats = [g_porte]
        else:
            candidats_cle = corniche_cle()

            # La clé n'a pas encore été ramassé, se dirige vers cette dernière si possible
            if not g_possede_cle and len(candidats_cle) != 0:
                candidats = candidats_cle
            # Dans le cas ultime, aller visiter une corniche pas encore visité
            else:
                candidats = corniche_vierge()

        # En fonction du niveau de risque actuellement admis par l'IA, il envisage une des quatre stratégies:
        # Niveau de risque de 0: Le personnage passe uniquement sur les corniches où il n'a pas décelé de piège (chauve souris réveillé, léviathan, puit)
        if niveau_risque == 0:
            dangers = corniche_danger()

            trajectoire, niveau_risque = recalculer_trajectoire(corniche, candidats, dangers, niveau_risque, trajectoire)
        # Niveau de risque de 1: Le personnage peut passer par les corniches abritant léviathan. Il tirera une flèche en sa direction
        if niveau_risque == 1:
            if g_possede_fleche and len(g_corniches_leviathan) > 0:
                # Possède encore une flèche, peut passer par des corniches abritant léviathan
                dangers = corniche_danger(True, False)

                trajectoire, niveau_risque = recalculer_trajectoire(corniche, candidats, dangers, niveau_risque, trajectoire)
            else:
                # Ne possède plus de flèche, le niveau de risque s'incrémente
                niveau_risque += 1
        # Niveau de risque de 2: Le personnage tente de passer sur les corniches où il y a des chauve souris (dans l'espoir qu'elles le téléporte sur une bonne corniche)
        if niveau_risque == 2:
            dangers = corniche_danger(False)

            trajectoire, niveau_risque = recalculer_trajectoire(corniche, candidats, dangers, niveau_risque, trajectoire)
        # Niveau de risque de 3: Le personnage n'a plus rien à perdre: il tente tous les chemins possibles
        if niveau_risque == 3:
            dangers = []

            trajectoire, niveau_risque = recalculer_trajectoire(corniche, candidats, dangers, niveau_risque, trajectoire)
        
        g_trajectoire = trajectoire
        g_trajectoire_position = 1

    if not trajectoire_indefinie(voisines):
        tmp = g_trajectoire[g_trajectoire_position]
        if tmp in g_corniches_leviathan and g_possede_fleche:
            g_possede_fleche = False
            return tmp, 1
        else:
            g_trajectoire_position += 1
            return tmp, 0
    else:
        # Si il ne sais rien, retourne sur la corniche précédente
        for i in voisines:
            if g_corniches[i][PARAMETRE_CORNICHE_VISITE] and precedent != i:
                return i, 0
        if precedent != None and precedent in voisines:
            return precedent, 0
        else:
            return voisines[randint(0, len(voisines)-1)], 0

def ia(corniche, voisines, taille, capteurs, evenements):
    global g_corniches, g_porte, g_chauve_souris, g_possede_cle, g_possede_fleche, g_chauve_souris_initial, g_leviathan_initial, g_trajectoire, g_trajectoire_position, g_precedent, g_leviathan, g_corniche_visitee, g_candidat_force, g_corniches_leviathan
    # Nous sommes dans un cratere de volcan.
    # Il y a un nombre {taille} de corniches.
    # Les corniches sont numerotees de 0 a {taille - 1}.

    if g_corniches is None:
        g_corniches = [None]*taille

    preview_memory.init(taille, g_corniches, g_chauve_souris,
                        g_leviathan, g_porte, g_trajectoire, g_trajectoire_position)

    
    memorisation_corniche(
        corniche, voisines,
        capteurs & m_b != 0, capteurs & m_d != 0,
        capteurs & m_p != 0, capteurs & m_k != 0, capteurs & m_l != 0
    )

    preview_memory.history_add(corniche)
    preview_memory.display_memory()
    preview_memory.update_display()

    if evenements & (2 * m_k):
        # La cle a ete trouvee
        if not g_possede_cle:
            g_possede_cle = True
            g_trajectoire = None
            for i in range(len(g_corniches)):
                if g_corniches[i] is not None:
                    g_corniches[i][PARAMETRE_CLE] = PRESENCE_IMPOSSIBLE
    if evenements & (2 * m_l):
        # Appele si leviathan a ete trouve
        if len(g_leviathan) != 0:
            g_leviathan = {}
            g_corniches_leviathan = []
            g_trajectoire = None
    if evenements & (2 * m_b):
        # Une chauve-souris t'as attrape.e, et t'emmene sur une autre corniche
        # sans te demander ton avis. Tu ne peux pas choisir ta destination !
        g_precedent = None
        return None, 0

    return arbre_decision(corniche, voisines, taille)

def explore(seed, dim, web_d, pits_d, bats_d):
    global g_corniches, g_porte, g_chauve_souris, g_possede_cle, g_possede_fleche, g_chauve_souris_initial, g_leviathan_initial, g_trajectoire, g_trajectoire_position, g_precedent, g_corniche_visitee, g_candidat_force, g_corniches_leviathan
    
    # Variables globales du programme
    g_corniches             = None
    g_porte                 = None
    g_chauve_souris         = {}
    g_possede_cle           = False
    g_possede_fleche        = True
    g_chauve_souris_initial = False
    g_leviathan_initial     = False
    g_trajectoire           = None
    g_trajectoire_position  = 0
    g_precedent             = None
    g_corniche_visitee      = 0
    g_candidat_force        = None
    g_corniches_leviathan   = []

    initconst(seed, dim, web_d, pits_d, bats_d)

    return parcourir_selon(ia)

if __name__ == "__main__":
    explore(1845129891, 36, .05, .1, .15)
