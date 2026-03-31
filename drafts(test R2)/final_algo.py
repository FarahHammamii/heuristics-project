import math
import random

class InitialisationRapideVRPTW:
    def __init__(self, fichier):
        self.fichier = fichier
        self.clients = []
        self.depot = None
        self.nb_vehicules_max = 0
        self.capacite = 0
        self.distance = []
        self.alpha = 1000
        self.SEUIL_DISTANCE = 50
        self.MARGE_TEMPS = 100
        self._charger_donnees()
        self._calculer_distances()

    def _charger_donnees(self):
        """Charge les données du fichier"""
        with open(self.fichier, 'r') as f:
            lignes = f.readlines()
        i = 0
        while i < len(lignes):
            ligne = lignes[i].strip()
            if ligne.startswith('VEHICLE'):
                i += 2
                data = lignes[i].strip().split()
                self.nb_vehicules_max = int(data[0])
                self.capacite = int(data[1])
            elif ligne.startswith('CUSTOMER'):
                i += 3
                while i < len(lignes) and lignes[i].strip():
                    data = lignes[i].strip().split()
                    if len(data) >= 7:
                        client = {
                            'id':      int(data[0]),
                            'x':       float(data[1]),
                            'y':       float(data[2]),
                            'demande': float(data[3]),
                            'debut':   float(data[4]),
                            'fin':     float(data[5]),
                            'service': float(data[6])
                        }
                        if client['id'] == 0:
                            self.depot = client
                        else:
                            self.clients.append(client)
                    i += 1
            i += 1

    def _calculer_distances(self):
        """Calcule la matrice des distances euclidienne"""
        tous = [self.depot] + self.clients
        n = len(tous)
        self.distance = [[0.0] * n for _ in range(n)]
        for i in range(n):
            for j in range(n):
                if i != j:
                    dx = tous[i]['x'] - tous[j]['x']
                    dy = tous[i]['y'] - tous[j]['y']
                    self.distance[i][j] = math.sqrt(dx*dx + dy*dy)

    # ─────────────────────────────────────────────
    #  VÉRIFICATION
    # ─────────────────────────────────────────────

    def verifier_route(self, route):
        """Vérifie capacité et fenêtres de temps pour une route"""
        if route[0] != 0 or route[-1] != 0:
            return False
        charge = 0
        temps  = self.depot['debut']
        courant = 0
        for client_id in route[1:-1]:
            client = self.clients[client_id - 1]
            charge += client['demande']
            if charge > self.capacite:
                return False
            trajet  = self.distance[courant][client_id]
            arrivee = temps + trajet
            if arrivee > client['fin']:
                return False
            arrivee = max(arrivee, client['debut'])
            temps   = arrivee + client['service']
            courant = client_id
        retour = temps + self.distance[courant][0]
        if retour > self.depot['fin']:
            return False
        return True

    def verifier_solution(self, solution):
        """Vérifie une solution complète (faisabilité + couverture)"""
        if len(solution) > self.nb_vehicules_max:
            return False
        visites = set()
        for route in solution:
            if not self.verifier_route(route):
                return False
            for c in route[1:-1]:
                if c == 0:
                    continue
                if c in visites:
                    return False
                visites.add(c)
        return len(visites) == len(self.clients)

    # ─────────────────────────────────────────────
    #  CALCULS DE COÛT
    # ─────────────────────────────────────────────

    def calculer_distance_route(self, route):
        """Distance totale d'une route"""
        dist = 0.0
        for i in range(1, len(route)):
            dist += self.distance[route[i-1]][route[i]]
        return dist

    def calculer_cout(self, solution):
        """Coût total : alpha * nb_véhicules + distance totale"""
        nb_vehicules    = len(solution)
        distance_totale = sum(self.calculer_distance_route(r) for r in solution)
        return self.alpha * nb_vehicules + distance_totale

    # ─────────────────────────────────────────────
    #  UTILITAIRES INTERNES
    # ─────────────────────────────────────────────

    def temps_fin_route(self, route):
        """Temps cumulé à la fin de la route (hors retour dépôt)"""
        if len(route) < 3:
            return self.depot['debut']
        temps   = self.depot['debut']
        courant = 0
        for client_id in route[1:-1]:
            trajet  = self.distance[courant][client_id]
            arrivee = temps + trajet
            if arrivee < self.clients[client_id-1]['debut']:
                arrivee = self.clients[client_id-1]['debut']
            temps   = arrivee + self.clients[client_id-1]['service']
            courant = client_id
        return temps

    def peut_ajouter_rapide(self, route, client_id):
        """Vérification rapide O(1) si un client peut être ajouté"""
        client = self.clients[client_id-1]

        # 1. Capacité
        charge_actuelle = sum(self.clients[c-1]['demande'] for c in route if c != 0)
        if charge_actuelle + client['demande'] > self.capacite:
            return False

        # 2. Distance minimale à la route
        distance_min = float('inf')
        for c in route:
            if c != 0:
                d = self.distance[c][client_id]
                if d < distance_min:
                    distance_min = d
        if distance_min > self.SEUIL_DISTANCE:
            return False

        # 3. Compatibilité temporelle basique
        if len(route) > 2:
            dernier = route[-2]
            if dernier != 0:
                temps_actuel     = self.temps_fin_route(route[:-1])
                arrivee_estimee  = temps_actuel + self.distance[dernier][client_id]
                if arrivee_estimee > client['fin'] + self.MARGE_TEMPS:
                    return False
        return True

    def inserer_meilleur_endroit(self, route, client_id):
        """Teste quelques positions stratégiques et insère si possible"""
        meilleure_pos  = -1
        meilleure_dist = float('inf')

        positions = [1]
        if len(route) > 3:
            positions.append(len(route) // 2)
        positions.append(len(route) - 1)

        for pos in positions:
            route_test = route[:]
            route_test.insert(pos, client_id)
            if self.verifier_route(route_test):
                dist = self.calculer_distance_route(route_test)
                if dist < meilleure_dist:
                    meilleure_dist = dist
                    meilleure_pos  = pos

        if meilleure_pos != -1:
            route.insert(meilleure_pos, client_id)
            return True
        return False

    def _fusionner_routes(self, solution):
        """
        Tente de fusionner des routes pour respecter nb_vehicules_max.
        Fusionne les deux routes les plus courtes dont la concaténation est réalisable.
        """
        solution = [r[:] for r in solution]

        while len(solution) > self.nb_vehicules_max:
            fusion_trouvee = False
            solution.sort(key=lambda r: self.calculer_distance_route(r))

            for i in range(len(solution)):
                if fusion_trouvee:
                    break
                for j in range(i + 1, len(solution)):
                    clients_i      = solution[i][1:-1]
                    clients_j      = solution[j][1:-1]
                    route_fusionnee = [0] + clients_i + clients_j + [0]
                    if self.verifier_route(route_fusionnee):
                        solution[i] = route_fusionnee
                        solution.pop(j)
                        fusion_trouvee = True
                        break

            if not fusion_trouvee:
                break

        return solution

    # ─────────────────────────────────────────────
    #  ALGORITHME 1 : SOLUTION ALÉATOIRE THARAA
    # ─────────────────────────────────────────────

    def generer_solution_aleatoire(self):
        """
        Algorithme 1 : GenererSolutionAleatoire()
        Mélange Fisher-Yates puis construction greedy des routes.
        """
        # Étape 1 : Mélanger les clients (Fisher-Yates)
        clients = [client['id'] for client in self.clients]
        n = len(clients)
        for i in range(n - 1, 0, -1):
            j = random.randint(0, i)
            clients[i], clients[j] = clients[j], clients[i]

        # Étape 2 : Construire les routes
        solution      = []
        route_courante = [0]

        for client in clients:
            route_test = route_courante[:] + [client, 0]
            if self.verifier_route(route_test):
                route_courante.append(client)
            else:
                route_courante.append(0)
                solution.append(route_courante)
                route_courante = [0, client]

        # Étape 3 : Ajouter la dernière route
        route_courante.append(0)
        solution.append(route_courante)

        # Étape 4 : Fusionner si trop de véhicules
        if len(solution) > self.nb_vehicules_max:
            solution = self._fusionner_routes(solution)

        return solution

    # ─────────────────────────────────────────────
    #  ALGORITHME 2 : TRI PAR URGENCE FARAH
    # ─────────────────────────────────────────────

    def generer_solution_rapide(self):
        """
        Algorithme 2 : Tri par urgence O(n log n)
        Construit les routes en priorisant les clients avec les fenêtres les plus serrées.
        """
        n = len(self.clients)

        # Étape 1 : Tri par fin de fenêtre croissante
        clients_avec_fin = [(self.clients[i]['fin'], i+1) for i in range(n)]
        clients_avec_fin.sort()
        clients_tries = [c[1] for c in clients_avec_fin]

        # Étape 2 : Construction greedy
        non_visites = set(clients_tries)
        solution    = []

        while non_visites:
            seed = None
            for c in clients_tries:
                if c in non_visites:
                    seed = c
                    break
            if seed is None:
                break

            route = [0, seed, 0]
            non_visites.remove(seed)

            amelioration = True
            while amelioration and non_visites:
                amelioration = False
                for c in list(non_visites):
                    if self.peut_ajouter_rapide(route, c):
                        if self.inserer_meilleur_endroit(route, c):
                            non_visites.remove(c)
                            amelioration = True
                            break

            solution.append(route)

        return solution

    # ─────────────────────────────────────────────
    #  ALGORITHME 3 : PLUS PROCHE VOISIN AHMED
    # ─────────────────────────────────────────────

    def generer_solution_plus_proche_voisin(self):
        """
        Algorithme 3 : Plus Proche Voisin
        À chaque étape, ajoute le client réalisable le plus proche de la position actuelle.
        """
        solution          = []
        clients_restants  = set(client['id'] for client in self.clients)

        while clients_restants:
            route_courante    = [0]
            position_actuelle = 0

            while True:
                candidat_proche = None
                distance_min    = float('inf')

                for c in clients_restants:
                    dist = self.distance[position_actuelle][c]
                    if dist < distance_min:
                        route_test = route_courante + [c, 0]
                        if self.verifier_route(route_test):
                            candidat_proche = c
                            distance_min    = dist

                if candidat_proche is not None:
                    route_courante.append(candidat_proche)
                    clients_restants.remove(candidat_proche)
                    position_actuelle = candidat_proche
                else:
                    break

            route_courante.append(0)
            solution.append(route_courante)

        return solution

    # ─────────────────────────────────────────────
    #  AFFICHAGE
    # ─────────────────────────────────────────────

    def afficher_resultats(self, solution, nom_algo="SOLUTION"):
        """Affiche la solution et ses métriques"""
        print(f"\n{'='*60}")
        print(f"{nom_algo}")
        print(f"{'='*60}")
        print(f"Nombre de véhicules utilisés : {len(solution)} / {self.nb_vehicules_max}")

        distance_totale = 0
        for i, route in enumerate(solution):
            dist = self.calculer_distance_route(route)
            distance_totale += dist
            clients = [str(c) for c in route[1:-1] if c != 0]
            if clients:
                print(f"Route {i+1}: 0 → {' → '.join(clients)} → 0")
                print(f"  Distance: {dist:.2f}")

        cout = self.calculer_cout(solution)
        print(f"\nDistance totale : {distance_totale:.2f}")
        print(f"Coût total      : {cout:.2f}")

        if self.verifier_solution(solution):
            print("✓ Solution réalisable")
        else:
            print("✗ Solution non réalisable")


# ══════════════════════════════════════════════════════════════
#  EXÉCUTION ET COMPARAISON DES TROIS ALGORITHMES
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    try:
        init = InitialisationRapideVRPTW("RC101.txt")

        # Algorithme 1 : Aléatoire (Fisher-Yates + Greedy)
        solution_aleatoire = init.generer_solution_aleatoire()
        init.afficher_resultats(solution_aleatoire, "SOLUTION ALÉATOIRE (Fisher-Yates + Greedy)")

        # Algorithme 3 : Plus Proche Voisin
        solution_ppv = init.generer_solution_plus_proche_voisin()
        init.afficher_resultats(solution_ppv, "SOLUTION PLUS PROCHE VOISIN")

        # ── Tableau comparatif ──────────────────────────────────
        print(f"\n{'='*60}")
        print("COMPARAISON DES ALGORITHMES")
        print(f"{'='*60}")
        print(f"{'Algorithme':<35} {'Véhicules':>10} {'Distance':>12} {'Coût':>12} {'Réalisable':>12}")
        print(f"{'-'*35} {'-'*10} {'-'*12} {'-'*12} {'-'*12}")

        algos = [
            ("Aléatoire ",  solution_aleatoire),
       
            ("Plus Proche Voisin",        solution_ppv),
        ]

        for nom, sol in algos:
            nb_v   = len(sol)
            dist   = sum(init.calculer_distance_route(r) for r in sol)
            cout   = init.calculer_cout(sol)
            valide = "✓" if init.verifier_solution(sol) else "✗"
            print(f"{nom:<35} {nb_v:>10} {dist:>12.2f} {cout:>12.2f} {valide:>12}")

    except FileNotFoundError:
        print("Erreur : fichier introuvable. Placez-le dans le même dossier que ce script.")