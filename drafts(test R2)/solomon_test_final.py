import math
import random
import time

class InitialisationRapideVRPTW:
    def __init__(self, fichier):
        self.fichier = fichier
        self.clients = []
        self.depot = None
        self.nb_vehicules_max = 0
        self.capacite = 0
        self.distance = []
        self.alpha = 1000
        self.SEUIL_DISTANCE = 50  # à ajuster
        self.MARGE_TEMPS = 100     # marge pour compatibilité
        self._charger_donnees()
        self._calculer_distances()
    
    def _charger_donnees(self):
        """Charge les données du fichier C101.txt"""
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
                            'id': int(data[0]),
                            'x': float(data[1]),
                            'y': float(data[2]),
                            'demande': float(data[3]),
                            'debut': float(data[4]),
                            'fin': float(data[5]),
                            'service': float(data[6])
                        }
                        if client['id'] == 0:
                            self.depot = client
                        else:
                            self.clients.append(client)
                    i += 1
            i += 1
    
    def _calculer_distances(self):
        """Calcule la matrice des distances"""
        tous = [self.depot] + self.clients
        n = len(tous)
        self.distance = [[0.0] * n for _ in range(n)]
        
        for i in range(n):
            for j in range(n):
                if i != j:
                    dx = tous[i]['x'] - tous[j]['x']
                    dy = tous[i]['y'] - tous[j]['y']
                    self.distance[i][j] = math.sqrt(dx*dx + dy*dy)
    
    def verifier_route(self, route):
        """Vérifie si une route respecte capacité et fenêtres de temps"""
        if route[0] != 0 or route[-1] != 0:
            return False

        charge = 0
        temps = self.depot['debut']
        courant = 0

        for client_id in route[1:-1]:
            client = self.clients[client_id - 1]

            # Capacité
            charge += client['demande']
            if charge > self.capacite:
                return False

            # Trajet
            trajet = self.distance[courant][client_id]
            arrivee = temps + trajet

            # Fenêtre
            if arrivee > client['fin']:
                return False

            # Attente si nécessaire
            arrivee = max(arrivee, client['debut'])

            # Mise à jour
            temps = arrivee + client['service']
            courant = client_id

        # Retour dépôt
        retour = temps + self.distance[courant][0]
        if retour > self.depot['fin']:
            return False

        return True
    
    def verifier_solution(self, solution):
        """Vérifie si une solution complète est réalisable"""
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
    
    def calculer_distance_route(self, route):
        """Calcule la distance totale d'une route"""
        dist = 0.0
        for i in range(1, len(route)):
            dist += self.distance[route[i-1]][route[i]]
        return dist
    
    def calculer_cout(self, solution):
        """Calcule le coût total d'une solution"""
        nb_vehicules = len(solution)
        distance_totale = sum(self.calculer_distance_route(r) for r in solution)
        return self.alpha * nb_vehicules + distance_totale
    
    def temps_fin_route(self, route):
        """Calcule le temps à la fin de la route (sans retour dépôt)"""
        if len(route) < 3:
            return self.depot['debut']
        
        temps = self.depot['debut']
        courant = 0
        
        for client_id in route[1:-1]:
            trajet = self.distance[courant][client_id]
            arrivee = temps + trajet
            
            if arrivee < self.clients[client_id-1]['debut']:
                arrivee = self.clients[client_id-1]['debut']
            
            temps = arrivee + self.clients[client_id-1]['service']
            courant = client_id
        
        return temps
    
    def peut_ajouter_rapide(self, route, client_id):
        """Vérification rapide O(1) si un client peut être ajouté"""
        client = self.clients[client_id-1]
        charge_actuelle = sum(self.clients[c-1]['demande'] for c in route if c != 0)
        if charge_actuelle + client['demande'] > self.capacite:
            return False
        
        distance_min = float('inf')
        for c in route:
            if c != 0:
                d = self.distance[c][client_id]
                if d < distance_min:
                    distance_min = d
        
        if distance_min > self.SEUIL_DISTANCE:
            return False
        
        if len(route) > 2:
            dernier = route[-2]
            if dernier != 0:
                temps_actuel = self.temps_fin_route(route[:-1])
                arrivee_estimee = temps_actuel + self.distance[dernier][client_id]
                if arrivee_estimee > client['fin'] + self.MARGE_TEMPS:
                    return False
        
        return True
    
    def inserer_meilleur_endroit(self, route, client_id):
        """Teste quelques positions stratégiques O(1)"""
        meilleure_pos = -1
        meilleure_dist = float('inf')
        positions = [1]
        if len(route) > 3:
            positions.append(len(route)//2)
        positions.append(len(route)-1)
        
        for pos in positions:
            route_test = route[:]
            route_test.insert(pos, client_id)
            if self.verifier_route(route_test):
                dist = self.calculer_distance_route(route_test)
                if dist < meilleure_dist:
                    meilleure_dist = dist
                    meilleure_pos = pos
        
        if meilleure_pos != -1:
            route.insert(meilleure_pos, client_id)
            return True
        return False
    
    def generer_solution_rapide(self):
        """Algorithme d'origine en O(n log n) (Tri par urgence)"""
        n = len(self.clients)
        clients_avec_fin = [(self.clients[i]['fin'], i+1) for i in range(n)]
        clients_avec_fin.sort()
        clients_tries = [c[1] for c in clients_avec_fin]
        
        non_visites = set(clients_tries)
        solution = []
        
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

    def generer_solution_plus_proche_voisin(self):
        """Algorithme du Plus Proche Voisin"""
        solution = []
        clients_restants = set(client['id'] for client in self.clients)
        
        while clients_restants:
            route_courante = [0]
            position_actuelle = 0
            while True:
                candidat_proche = None
                distance_min = float('inf')
                for c in clients_restants:
                    dist = self.distance[position_actuelle][c]
                    if dist < distance_min:
                        route_test = route_courante + [c, 0]
                        if self.verifier_route(route_test):
                            candidat_proche = c
                            distance_min = dist
                if candidat_proche is not None:
                    route_courante.append(candidat_proche)
                    clients_restants.remove(candidat_proche)
                    position_actuelle = candidat_proche
                else:
                    break
            route_courante.append(0)
            solution.append(route_courante)
        return solution

    # ==========================================
    # NOUVEL ALGORITHME : SOLOMON INSERTION (I1)
    # ==========================================

    def calculer_temps_arrivee_client(self, route, index_dans_route):
        """Calcule le temps d'arrivée à un point précis de la route"""
        temps = self.depot['debut']
        courant = 0
        for k in range(1, index_dans_route + 1):
            client_id = route[k]
            dist = self.distance[courant][client_id]
            if client_id == 0: 
                return temps + dist
            client = self.clients[client_id-1]
            temps = max(temps + dist, client['debut'])
            if k < index_dans_route:
                temps += client['service']
            courant = client_id
        return temps

    def generer_solution_solomon(self, mu=1.0, alpha=1.0, beta=1.0):
        solution = []
        # On travaille sur les IDs des clients (1 à n)
        clients_restants = set(client['id'] for client in self.clients)

        while clients_restants:
            # --- INITIALISATION DE LA ROUTE (Client Germe) ---
            # Trouver le client le plus éloigné du dépôt parmi les restants
            seed = max(clients_restants, key=lambda c: self.distance[0][c])
            route = [0, seed, 0]
            clients_restants.remove(seed)

            # --- INSERTION SÉQUENTIELLE ---
            while True:
                meilleur_client = None
                meilleure_pos = -1
                cout_minimal = float('inf')

                for u in clients_restants:
                    for p in range(len(route) - 1):
                        i = route[p]
                        j = route[p+1]
                        
                        # Inserer(Route, u, p+1)
                        route_test = route[:p+1] + [u] + route[p+1:]
                        
                        if self.verifier_route(route_test):
                            # C1 : Coût de distance (écart d'insertion)
                            c1 = self.distance[i][u] + self.distance[u][j] - mu * self.distance[i][j]
                            
                            # C2 : Coût temporel (Impact sur le client j)
                            # On compare l'heure d'arrivée chez j avant et après l'insertion de u
                            t_j_ancien = self.calculer_temps_arrivee_client(route, p+1)
                            t_j_nouveau = self.calculer_temps_arrivee_client(route_test, p+2)
                            
                            c2 = t_j_nouveau - t_j_ancien
                            
                            # Coût Total selon les paramètres alpha et beta
                            cout_total = alpha * c1 + beta * c2
                            
                            if cout_total < cout_minimal:
                                cout_minimal = cout_total
                                meilleur_client = u
                                meilleure_pos = p + 1

                # Si on a trouvé un client insérable sur cette route
                if meilleur_client is not None:
                    route.insert(meilleure_pos, meilleur_client)
                    clients_restants.remove(meilleur_client)
                else:
                    # Plus aucun client n'est insérable sur la route actuelle
                    break 

            solution.append(route)
        
        return solution

    def afficher_resultats(self, solution, nom_algo="SOLUTION"):
        """Affiche la solution et ses caractéristiques"""
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
                print(f"         Distance: {dist:.2f}")
        
        cout = self.calculer_cout(solution)
        print(f"\nDistance totale: {distance_totale:.2f}")
        print(f"Coût total: {cout:.2f}")
        
        if self.verifier_solution(solution):
            print("✓ Solution réalisable")
        else:
            print("✗ Solution non réalisable")
if __name__ == "__main__":

    import os

    print("\n" + "="*80)
    print("TEST GLOBAL - COMPARAISON DES ALGORITHMES (TOUTES INSTANCES)")
    print("="*80)

    fichiers = sorted([f for f in os.listdir(".") if f.endswith(".txt")])

    if not fichiers:
        print("Aucun fichier .txt trouvé dans le dossier.")
        exit()

    for fichier in fichiers:
        print("\n" + "-"*80)
        print(f"Instance : {fichier}")
        print("-"*80)

        try:
            init = InitialisationRapideVRPTW(fichier)



          
            start = time.perf_counter()
            solution_solomon = init.generer_solution_solomon()
            end = time.perf_counter()
            duree_solomon = end - start

            faisable_solomon = init.verifier_solution(solution_solomon)

            print("\n[3] SOLOMON I1")
            print(f"Véhicules : {len(solution_solomon)} / {init.nb_vehicules_max}")
            print(f"Temps exécution : {duree_solomon:.4f} s")
            print(f"Distance  : {sum(init.calculer_distance_route(r) for r in solution_solomon):.2f}")
            print(f"Faisable  : {faisable_solomon}")

            if not faisable_solomon:
                print("Instance NON réalisable avec SOLOMON")
                print("Arrêt immédiat.")
                break

        except Exception as e:
            print(f"Erreur sur l'instance {fichier}: {e}")
            break

    else:
        print("\n✅ Toutes les instances sont réalisables pour tous les algorithmes.")