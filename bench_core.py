import threading
import multiprocessing
from multiprocessing.managers import BaseManager
import time
import imp, sys

PARAMETRE_ECHEC_EXEPTION = 0
PARAMETRE_ECHEC_PUIT = 1
PARAMETRE_ECHEC_LEVIATHAN = 2
PARAMETRE_ECHEC_ENERGIE = 3
PARAMETRE_ECHEC_NON_REPONSE = 4
PARAMETRE_TOTAL_REUSSITE = 5

class BenchProxy:
    verrou = multiprocessing.Semaphore()
    verrou_maj = multiprocessing.Semaphore()

    m_arret_demande = False

    def __init__(self, seed, threads):
        self.seed = seed
        self.retour_simulation = [None] * threads

        for i in range(threads):
            self.retour_simulation[i] = {
                "graines" : [None] * 5,
                "temps" : [None] * 5,
                "compteur" : [0] * 6,
                "coups_total" : 0,
                "compteur_coups" : 0
            }

    def verrouiller_maj(self):
        self.verrou_maj.acquire()
    
    def deverouiller_maj(self):
        self.verrou_maj.release()
    
    def ajout_compteur(self, identifiant, evenement, graine, temps, coups = 0):
        """
        Ajoute au compteur un événement défini par evenement avec la graine données
        :argument evenent: l'identifiant de l'événement
        :argument graine: la graine pour laquelle l'événement s'est déroulé
        :argument coups: le nombre de coups en cas de victoire
        """
        self.retour_simulation[identifiant]["compteur"][evenement] += 1
        if evenement == PARAMETRE_TOTAL_REUSSITE:
            self.retour_simulation[identifiant]["coups_total"] += coups
            self.retour_simulation[identifiant]["compteur_coups"] += 1
        else:
            if evenement == PARAMETRE_ECHEC_NON_REPONSE:
                print("Echec avec non réponse")
            self.retour_simulation[identifiant]["graines"][evenement] = graine
            self.retour_simulation[identifiant]["temps"][evenement] = temps
    
    def valeurs_generales(self):
        """
        Récupère les valeurs additionnées à partir des données du banc de test
        """
        donnees = self.retour_simulation.copy()

        graines = [None]*5
        temps = [None]*5
        compteur = [0]*6
        coups_totaux, nombre_victoires = 0, 0

        for i in range(len(donnees)):
            for j in range(5):
                if donnees[i]["graines"][j] != None and donnees[i]["temps"][j] != None:
                    if graines[j] == None or temps[j] == None or temps[j] < donnees[i]["temps"][j]:
                        graines[j] = donnees[i]["graines"][j]
                        temps[j] = donnees[i]["temps"][j]

            for j in range(6):
                compteur[j] += donnees[i]["compteur"][j]

            coups_totaux += donnees[i]["coups_total"]
            nombre_victoires += donnees[i]["compteur_coups"]
        
        coups_moyens = 0

        if nombre_victoires:
            coups_moyens = coups_totaux/nombre_victoires

        return compteur, graines, coups_moyens

    def nouvelle_graine(self):
        """
        Génère et retourne une nouvelle graine.
        :return: la nouvelle graine généré
        """
        ret = 0
        self.verrou.acquire()
        self.seed = (self.seed * 214013 + 2531011) % 4294967296
        ret = self.seed
        self.verrou.release()
        return ret

    def demande_arret(self):
        self.m_arret_demande = True

    def arret_demande(self):
        return self.m_arret_demande

class Bench:
    """
    Classe générale du banc de test. Initialise les variables ainsi que fils d'exécution
    """
    # nb_exec
    # Compteur des événements
    compteur = [0]*6

    total_ech = 0
    total_compteur = 0

    trajet_moyen = 0

    # Graines des événements
    graines = [None]*5

    arrete = False

    def __init__(self, nb_fil_exec, graine, nombre, module, duree_max, web_dim, web_density, pit_density, bats_density):
        """
        Initialise le banc de test
        :argument nb_fil_exec: le nombre de fils d'exécution à utiliser
        :argument graine: la graine du test, est utilisé par la suite afin d'identifier les tests ayant échoué
        :argument nombre: le nombre de tests à effectuer
        :argument module: le nom du module à charger
        :argument duree_max: la durée maximale pour l'exécution d'un test. Au delà de cette durée, ce test sera annulé
        :argument web_dim: la taille de la zone de jeu
        :argument web_density: la densité de corniches voisine à chaque corniche
        :argument pit_density: la densité de puits dans une partie
        :argument bats_density: la densité de chauve-souris dans une partie
        """
        fil_exec = [None]*nb_fil_exec
        nombre_restant = nombre
        nombre_thread = nombre_restant // nb_fil_exec
        donnees_module = ""

        BaseManager.register('BenchProxy', BenchProxy)
        self.mgr = BaseManager()
        self.mgr.start()

        self.proxy = self.mgr.BenchProxy(graine, nb_fil_exec)
        
        with open(module, 'r') as f:
            donnees_module = f.read()

        for i in range(nb_fil_exec):
            fil_exec[i] = BenchmarkThread(
                i, self.proxy, nombre_thread if i < nb_fil_exec - 1 else nombre_restant,
                Bench.charge_ia(donnees_module, "ia_%d"%i), duree_max, web_dim, web_density, pit_density, bats_density
            )
            nombre_restant -= nombre_thread
        self.fil_exec = fil_exec
        self.nb_exec = nombre
        self.graine = multiprocessing.Value('i', graine)

    def demarre(self):
        """
        Démarre les tests
        """
        for i in self.fil_exec:
            i.start()

    def mise_a_jour_donnees(self):
        """
        Met à jour les valeurs du test général à partir des valeurs données par les différents fils d'exécution
        """
        self.compteur, self.graines, self.trajet_moyen = self.proxy.valeurs_generales()

        self.total_compteur = 0
        self.total_ech = 0

        for i in range(len(self.compteur)):
            self.total_compteur += self.compteur[i]
            if i != len(self.compteur):
                self.total_ech += self.compteur[i]

    def test_en_cours(self):
        """
        Dit si les tests sont terminés ou pas
        :return: True si les tests sont en cours sinon False
        """
        for i in self.fil_exec:
            if i.is_alive():
                return True
        return False

    def arret(self):
        """
        Arrête les tests en cours et patiente jusqu'à l'arrêt définitif de ces derniers
        """
        if not self.arrete:
            self.proxy.demande_arret()
            for i in self.fil_exec:
                if i.is_alive():
                    i.terminate()
            self.mgr.shutdown()
            self.arrete = True

    @staticmethod
    def charge_ia(donnees, nom):
        """
        Génère un module de l'IA en fonction des données et du nom donné
        :argument donnees: le code source de l'IA écrit en python
        :argument nom: le nom du module. Ce dernier doit être unique afin d'éviter tout conflit entre les fils d'exécution
        :return: le module généré
        """
        ret = imp.new_module(nom)
        exec(donnees, ret.__dict__)
        sys.modules[nom] = ret
        return ret

class BenchmarkThread(multiprocessing.Process):
    """
    Fil d'exécution unique du banc de test
    """
    attente_mise_a_jour = False

    def __init__(self, identifiant, proxy, nombre, module, duree_max, web_dim, web_density, pit_density, bats_density):
        """
        Initialise un fil de benchmark.
        :param nombre: Le nombre de test à effectuer
        :param module_name: Le nom du module à importer
        """

        super().__init__()
        self.proxy = proxy

        self.nb_exec = nombre
        self.module = module
        self.id = identifiant

        # Paramètres d'une partie
        self.duree_max = duree_max
        self.web_dim = web_dim
        self.web_density = web_density
        self.pit_density = pit_density
        self.bats_density = bats_density

    def run(self):
        compteur = 0

        while compteur < self.nb_exec and not self.proxy.arret_demande():
            graine = self.proxy.nouvelle_graine()

            test = threading.Thread(target=BenchmarkThread.unitary_loop, args=[self, graine])
            test.start()

            action_annulee = False
            temps_depart = time.time()

            while (test.is_alive() and not self.proxy.arret_demande() and not action_annulee) or self.attente_mise_a_jour:
                if time.time() - temps_depart > self.duree_max:
                    action_annulee = True

            if action_annulee or self.proxy.arret_demande():
                if action_annulee:
                    self.proxy.ajout_compteur(self.id, PARAMETRE_ECHEC_NON_REPONSE, graine, time.time())
                    self.attente_mise_a_jour = False
                del test
            
            compteur += 1
        
    def unitary_loop(self, graine):
        (victoire, type_defaite, _, nombre_coups) = self.module.explore(
            graine,
            self.web_dim,
            self.web_density,
            self.pit_density,
            self.bats_density
        )

        self.attente_mise_a_jour = True
        if victoire:
            self.proxy.ajout_compteur(self.id, PARAMETRE_TOTAL_REUSSITE, 0, 0, nombre_coups)
        else:
            if type_defaite & 1:
                self.proxy.ajout_compteur(self.id, PARAMETRE_ECHEC_PUIT, graine, time.time())
            elif type_defaite & 2:
                self.proxy.ajout_compteur(self.id, PARAMETRE_ECHEC_LEVIATHAN, graine, time.time())
            elif type_defaite & 4:
                self.proxy.ajout_compteur(self.id, PARAMETRE_ECHEC_EXEPTION, graine, time.time())
            elif type_defaite & 8:
                self.proxy.ajout_compteur(self.id, PARAMETRE_ECHEC_ENERGIE, graine, time.time())
        self.attente_mise_a_jour = False
