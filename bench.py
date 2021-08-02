#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pygame
import threading
import time
import math
import sys
import argparse
import bench_core
import multiprocessing

# Couleurs du programme. Peut être modifié à tout moment
couleur_txt = (0xc0, 0xc0, 0xc0)  # Couleur gris clair pour le texte commun
couleur_vic = (0x28, 0xa7, 0x45)  # Couleur verte pour la gauge et le texte associé
couleur_arp = (0x18, 0x18, 0x18)  # Couleur de l'arrière plan général de l'application (Gris foncé)
couleur_gar = (0x21, 0x21, 0x21)  # Couleur de l'arrière plan de la gauge en mode barre de chargement (Nuance de l'AP)
couleurs_echec = [
    (0xf5, 0xe8, 0x00),  # Couleur jaune pour signaler une exeption (un plantage de l'algorithme)
    (0xff, 0x80, 0x3c),  # Couleur orange pour signaler un puit (Le personnage prend une corniche avec un puit)
    (0xf7, 0x40, 0x3b),  # Couleur rouge pour signaler Léviathan (Le personnage se fait manger par ce dernier)
    (0x7f, 0x7f, 0x7f),  # Couleur grise pour signaler une manque d'énergie (càd le personnage tourne en rond)
    (0xff, 0x00, 0x00)   # Couleur rouge vif pour signaler une non réponse (L'algorithme prennds trop de temps)
]

# Modèles de texte
texte_modeles = [
    "%0.00f%% à cause d'une exeption (%d, %d%% des échecs)%s",
    "%0.00f%% tombé dans un puit (%d, %d%% des échecs)%s",
    "%0.00f%% mangé par leviathan (%d, %d%% des échecs)%s",
    "%0.00f%% par manque d'énergie (%d, %d%% des échecs)%s",
    "%0.00f%% ne répondant pas (%d, %d%% des échecs)%s"
]

# Constantes de mise en page (Metriques)
metrique_mm = 8  # Marges de l'application (entre les bords de la fenêtre et le contenu ainsi que entre les éléments)
metrique_hg = 24  # Hauteur de la gauge en pixels
metrique_pt = 25  # Taille du texte de titre en points
metrique_pp = 12  # Taille du texte général en points

# Variables de benchmark (NE PAS MODIFIER)

# Variable de control de l'IHM
affichage_absolu = False
arret_demande = False

# Système de comptage du temps
heure_depart = 0
heure_fin = 0

# Initialisation de pygame (NE PAS MODIFIER)
pygame.font.init()
pygame.display.init()

# Initialisation des éléments graphiques (NE PAS MODIFIER)
ecran = None

police_titre = pygame.font.Font(pygame.font.get_default_font(), metrique_pt)
police = pygame.font.Font(pygame.font.get_default_font(), metrique_pp)


def cree_jauge(surface, donnees, couleur, rect):
    """
    Dessine une gauge en fonctions des données et couleurs fournis dans une boite défini par rect.

    :param surface: La surface où dessiner la gauge
    :param donnees: Les données de la gauge dans un tableau de taille N
    :param couleur: Les couleurs associés aux données de la gauge dans un tableau de taille N
    :param rect: La boite où dessiner la gauge (coordonnées + taille)
    :return: None
    """
    total_donnees = 0
    nombre_donnees = len(donnees)
    taille_elements = [0] * nombre_donnees
    largeur_donnees = 0

    for i in donnees:
        total_donnees += i

    for i in range(nombre_donnees - 1):
        t = int(rect.width * donnees[i] / total_donnees)
        taille_elements[i] = t
        largeur_donnees += t

    taille_elements[-1] = rect.width - largeur_donnees

    largeur_donnees = 0

    for i in range(nombre_donnees):
        surface.fill(couleur[i], (rect.x + largeur_donnees, rect.y, taille_elements[i], rect.height))
        largeur_donnees += taille_elements[i]


def rendu_temps(temps):
    """
    Affiche l'ordre de grandeur du temps restant
    :param temps: Le temps restant en secondes
    :return: Un texte donnant son ordre de grandeur en jour/heures/minutes
    """
    minutes = temps // 60 % 60
    heures = temps // 3600 % 24
    jours = temps // 86400
    if jours != 0:
        return "~%d jour%s" % (jours, "s" if jours != 1 else "")
    if heures != 0:
        return "~%d heure%s" % (heures, "s" if heures != 1 else "")
    if minutes != 0:
        return "~%d minute%s" % (minutes, "s" if minutes != 1 else "")
    return "<1 minute"


def format_duree(duree):
    """
    Formate une durée en ensemble jours/heure/minutes/secondes
    Cette durée formaté n'affiche pas les ordres de grandeurs nuls
    :param duree: La durée à formater
    :return: Le texte de la durée formaté sour le format <j>j <hh>h <mm>min <ss>s
    """
    duree = int(math.floor(duree))
    return "{}{:02d}s".format(
        "{}{:02d}min".format(
            "{}{:02d}h".format(
                "{}j".format(duree // 86400) if duree // 86400 != 0 else "",
                duree // 3600 % 24
            ) if duree // 3600 != 0 else "",
            duree // 60 % 60
        ) if duree // 60 != 0 else "",
        duree % 60
    )


def afficher_graine(graine):
    """
    Formate un texte avec la graine donnée ou ne donner rien si cette dernière est None
    :param graine: La graine à afficher
    :return: Un texte sous la forme ". Graine aléatoire: <graine>" si seed différent de None sinon ""
    """
    if graine is None:
        return ""
    else:
        return ". Graine aléatoire: %d" % graine


# TODO: Nettoyer et documenter cette fonction
def affichage_donnees():
    # temps_restant = math.ceil(args.max_duration - temps_exec_unitaire)

    duree = time.time() - heure_depart
    total_tst = bench.total_compteur
    temps_exec = duree * (args.number / total_tst - 1)

    score = (1000 * (bench.compteur[bench_core.PARAMETRE_TOTAL_REUSSITE] - 2 * bench.compteur[bench_core.PARAMETRE_ECHEC_NON_REPONSE] - bench.compteur[bench_core.PARAMETRE_ECHEC_EXEPTION] // 2) - bench.trajet_moyen) * args.web_dim / total_tst

    largeur = 512
    hauteur = metrique_mm

    texte_compteur = police_titre.render(
        "Simulation %d sur %d (%0.00f%%)" % (total_tst, args.number, 100. * float(total_tst) / float(args.number)),
        True, couleur_txt)
    largeur = max(largeur, texte_compteur.get_width())
    hauteur += texte_compteur.get_height() + metrique_mm
    texte_score = police.render("Score: %d" % score, True, couleur_txt)
    largeur = max(largeur, texte_score.get_width())
    hauteur += texte_score.get_height() + metrique_mm
    texte_victoire = police.render(
        "%0.00f%% de victoires (%d). Trajet moyen: %d" % (
            100 * bench.compteur[bench_core.PARAMETRE_TOTAL_REUSSITE] / total_tst, bench.compteur[bench_core.PARAMETRE_TOTAL_REUSSITE], bench.trajet_moyen),
        True, couleur_vic)
    largeur = max(largeur, texte_victoire.get_width())
    hauteur += texte_victoire.get_height() + metrique_mm
    # texte_temps_annulation = None
    texte_temps_restant = None
    if total_tst != args.number:
        texte_temps_restant = police.render(
            "Temps restant: %s. Écoulé %s" % (rendu_temps(math.ceil(temps_exec)), format_duree(duree)), True,
            couleur_txt)
        # texte_temps_annulation = police.render("Temps restant avant annulation: %d seconde%s" % (
        #     temps_restant if temps_restant > 0 else 0, "s" if temps_restant > 1 else ""), True,
        #                                        couleur_txt if temps_restant > 5 else couleur_lvt)
    else:
        texte_temps_restant = police.render("Tests effectués en %s" % (format_duree(heure_fin - heure_depart)), True,
                                            couleur_vic)
        # texte_temps_annulation = police.render("", True, couleur_txt)
    # largeur = max(largeur, texte_temps_annulation.get_width())
    # hauteur += texte_temps_annulation.get_height() + metrique_mm
    largeur = max(largeur, texte_temps_restant.get_width())
    hauteur += texte_temps_restant.get_height() + metrique_mm

    texte_echec = []
    valeur_gauge = [bench.compteur[bench_core.PARAMETRE_TOTAL_REUSSITE]]
    couleur_gauge = [couleur_vic]
    for i in range(5):
        if bench.compteur[i] != 0:
            texte_echec.append(
                police.render(
                    texte_modeles[i] % (
                        100 * bench.compteur[i] / total_tst,
                        bench.compteur[i],
                        100 * bench.compteur[i] / bench.total_ech,
                        afficher_graine(bench.graines[i])
                    ),
                    True, couleurs_echec[i]
                )
            )
            valeur_gauge.append(bench.compteur[i])
            couleur_gauge.append(couleurs_echec[i])
    if affichage_absolu:
        valeur_gauge.append(args.number - total_tst)
        couleur_gauge.append(couleur_gar)

    for i in texte_echec:
        hauteur += i.get_height() + metrique_mm
        largeur = max(largeur, i.get_width())

    hauteur += metrique_hg + metrique_mm
    largeur += 2 * metrique_mm

    surface = pygame.Surface((largeur, hauteur))
    surface.fill(couleur_arp)

    y = metrique_mm
    surface.blit(texte_compteur, (
        largeur / 2 - texte_compteur.get_width() / 2, y, texte_compteur.get_width(), texte_compteur.get_height()))
    y += texte_compteur.get_height() + metrique_mm
    surface.blit(texte_score,
                 (largeur / 2 - texte_score.get_width() / 2, y, texte_score.get_width(), texte_score.get_height()))
    y += texte_score.get_height() + metrique_mm
    cree_jauge(surface, valeur_gauge, couleur_gauge,
               pygame.Rect(metrique_mm, y, largeur - 2 * metrique_mm, metrique_hg))
    y += metrique_hg + metrique_mm
    surface.blit(texte_temps_restant, (
        largeur / 2 - texte_temps_restant.get_width() / 2, y, texte_temps_restant.get_width(),
        texte_temps_restant.get_height()))
    y += texte_temps_restant.get_height() + metrique_mm
    surface.blit(texte_victoire, (metrique_mm, y, texte_victoire.get_width(), texte_victoire.get_height()))
    y += texte_victoire.get_height() + metrique_mm

    for i in texte_echec:
        surface.blit(i, (metrique_mm, y, i.get_width(), i.get_height()))
        y += i.get_height() + metrique_mm

    # surface.blit(texte_temps_annulation, (
    #     largeur / 2 - texte_temps_annulation.get_width() / 2, y, texte_temps_annulation.get_width(),
    #     texte_temps_annulation.get_height()))

    return surface


def fonction_affichage():
    """
    Routine d'affichage. Cette fonction tourne dans un thread indépendant
    :return: None
    """
    global arret_demande, affichage_absolu, ecran, heure_fin

    temps_mise_a_jour = 0
    duree_mise_a_jour = 1/args.update_frequency
    debut_clic = False

    while not arret_demande:
        if time.time() - temps_mise_a_jour >= duree_mise_a_jour:
            bench.mise_a_jour_donnees()
            if bench.total_compteur != 0:
                if bench.total_compteur < args.number:
                    heure_fin = time.time()
                surface = affichage_donnees()
                if ecran is None or surface.get_width() != ecran.get_width() or surface.get_height() != ecran.get_height():
                    ecran = pygame.display.set_mode((surface.get_width(), surface.get_height()))
                ecran.blit(surface, (0, 0, ecran.get_width(), ecran.get_height()))
                pygame.display.flip()
                temps_mise_a_jour = time.time()
        if ecran is not None:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    bench.arret()
                    arret_demande = True
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    debut_clic = True
                elif event.type == pygame.MOUSEBUTTONUP and debut_clic:
                    affichage_absolu = not affichage_absolu
                    debut_clic = False

# Objet gérant le benchmark de l'IA
bench = None

# Parsing des options d'exécution
parser = argparse.ArgumentParser(
    description="Effectue de nombreux tests dans le but de vérifier le comportement de l'IA pour le défi python "
                "du Leviathan dans des cas aléatoires. Voir "
                "https://tiplanet.org/forum/viewtopic.php?f=49&t=24387&p=257174#p257172 pour plus d'informations "
                "sur le défi."
)
# Argument pour l'intelligence artificielle
parser.add_argument("ia", help="Fichier de l'IA à tester")
parser.add_argument('-n', "--number", default=100000, type=int, help="Nombre de tests à effectuer")
parser.add_argument('-s', "--seed", default=0xc0ffee, type=int, help="Graine aléatoire du benchmark")
parser.add_argument('-w', "--web-dim", default=36, type=int, help="Nombre de corniches")
parser.add_argument("-d", "--web-density", default=0.05, type=float,
                    help="Densité moyenne de voisine à chaque corniche")
parser.add_argument("-b", "--bats-density", default=0.1, type=float, help="Densité de chauve souris par parties")
parser.add_argument("-p", "--pit-density", default=0.15, type=float, help="Densité de puit par parties")
parser.add_argument("-m", "--max-duration", default=20, type=float, help="Durée maximum d'une partie en seconde")
parser.add_argument("-t", "--threads", default=1, type=int, help="Nombre de fils d'exécution pour les tests")
parser.add_argument("-f", "--update-frequency", default=24, type=int, help="Fréquence de rafraichssement de l'interface")

args = parser.parse_args(sys.argv[1:])
err = False
err_text = "\n"

if args.web_density >= 1 or args.web_density <= 0:
    err_text += "La densité de corniche voisine doit être comprise entre 0 et 1, non inclu\n"
    err = True
if args.bats_density >= 1 or args.bats_density <= 0:
    err_text += "La densité de chauve souris doit être comprise entre 0 et 1, non inclu\n"
    err = True
if args.pit_density >= 1 or args.pit_density <= 0:
    err_text += "La densité de puit doit être comprise entre 0 et 1, non inclu\n"
    err = True
if args.max_duration <= 0:
    err_text += "La durée maximum d'une partie doit être strictement supérieure à 0\n"
    err = True
if args.threads <= 0:
    err_text += "Le nombre de fils d'exécution doit être supérieur à 0\n"
    err = True
if args.web_dim <= 3:
    err_text += "Un nombre raisonnable de corniche doit être fourni pour le bon fonctionnement de l'algorithme\n"
    err = True
if args.number <= 0:
    err_text += "Il faut au minimum un test pour pouvoir avoir des données exploitables\n"
    err = True
if args.update_frequency <= 0:
    err_text += "La fréquence de rafraichissement de l'interface doit être strictement positive"
    err = True
if args.update_frequency > 60:
    print("Alerte: La fréquence de rafraichissement choisi est très élevée. Cela pourra impacter négativement la vitesse du test")
if args.threads >= multiprocessing.cpu_count():
    print("Alerte: Le nombre de fils d'exécution demandé est supérieur au nombre de processeurs disponibles. Cela risque d'impacter les performance totales de votre ordinateur")

"""
try:
    bench = bench_core.Bench(
        args.threads,
        args.seed,
        args.number,
        args.ia,
        args.max_duration,
        args.web_dim,
        args.web_density,
        args.pit_density,
        args.bats_density
    )
except Exception as _:
    err_text += "L'ia spécifié ne peut être ouvert en tant que script. Il se peut que ce dernier n'existe pas ou ne " \
                "soit pas un script python valide\n"
    err = True
"""

bench = bench_core.Bench(
    args.threads,
    args.seed,
    args.number,
    args.ia,
    args.max_duration,
    args.web_dim,
    args.web_density,
    args.pit_density,
    args.bats_density
)

if err:
    parser.print_usage()
    print(err_text)
    quit()

del parser

# Programme principal: Crée les fils d'exécution et fait tourner l'algorithme
fil_exec_interface_utilisateur = threading.Thread(target=fonction_affichage)

heure_depart = time.time()

fil_exec_interface_utilisateur.start()

# Lance les boucles de test
bench.demarre()

fil_exec_interface_utilisateur.join()

bench.arret()

pygame.quit()

if bench.total_compteur != 0:
    total_tst = bench.total_compteur
    total_vic = bench.compteur[bench_core.PARAMETRE_TOTAL_REUSSITE]
    total_ech = total_tst - total_vic
    total_lvt = bench.compteur[bench_core.PARAMETRE_ECHEC_LEVIATHAN]
    total_pit = bench.compteur[bench_core.PARAMETRE_ECHEC_PUIT]
    total_nrj = bench.compteur[bench_core.PARAMETRE_ECHEC_ENERGIE]
    total_exc = bench.compteur[bench_core.PARAMETRE_ECHEC_EXEPTION]
    total_nrp = bench.compteur[bench_core.PARAMETRE_ECHEC_NON_REPONSE]

    graine_lvt = bench.graines[bench_core.PARAMETRE_ECHEC_LEVIATHAN]
    graine_pit = bench.graines[bench_core.PARAMETRE_ECHEC_PUIT]
    graine_nrj = bench.graines[bench_core.PARAMETRE_ECHEC_ENERGIE]
    graine_exc = bench.graines[bench_core.PARAMETRE_ECHEC_EXEPTION]
    graine_nrp = bench.graines[bench_core.PARAMETRE_ECHEC_NON_REPONSE]

    score = (1000 * (total_tst - 2 * total_nrp - total_exc // 2) - bench.trajet_moyen) * args.web_dim / bench.total_compteur
    
    print(
        "Statistiques finales:\n\tNombre total test: %d\n\n"
        "Score final: %d\n"
        "%d succès (%0.00f%%) avec un trajet moyen de %d\n"
        "%d échecs (%0.00f%%) avec comme détails:\n"
        "\t%d dues à un léviathan (%0.00f%%)%s\n"
        "\t%d dues à un puit (%0.00f%%)%s\n"
        "\t%d dues à un manque d'énergie (%0.00f%%)%s\n"
        "\t%d dues à une exeption (%0.00f%%)%s\n"
        "\t%d dues à un temps de réponse trop élevé (%0.00f%%)%s\n"
        "" % (
            total_tst,
            score,
            total_vic, 100 * total_vic / bench.total_compteur, bench.trajet_moyen,
            total_ech, 100 * total_ech / bench.total_compteur,
            total_lvt, 100 * total_lvt / bench.total_ech, afficher_graine(graine_lvt),
            total_pit, 100 * total_pit / bench.total_ech, afficher_graine(graine_pit),
            total_nrj, 100 * total_nrj / bench.total_ech, afficher_graine(graine_nrj),
            total_exc, 100 * total_exc / bench.total_ech, afficher_graine(graine_exc),
            total_nrp, 100 * total_nrp / bench.total_ech, afficher_graine(graine_nrp)
        )
    )
