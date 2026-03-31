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

        # 🔴 VEHICLE LIMIT CONSTRAINT
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
        
        # All clients visited exactly once
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
        
        # 1. Vérification capacité
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
        
        # Si trop loin, ignore
        if distance_min > self.SEUIL_DISTANCE:
            return False
        
        # 3. Compatibilité temporelle basique
        if len(route) > 2:
            dernier = route[-2]
            if dernier != 0:
                temps_actuel = self.temps_fin_route(route[:-1])  # sans le dernier 0
                arrivee_estimee = temps_actuel + self.distance[dernier][client_id]
                
                # Marge de tolérance
                if arrivee_estimee > client['fin'] + self.MARGE_TEMPS:
                    return False
        
        return True
    
    def inserer_meilleur_endroit(self, route, client_id):
        """Teste quelques positions stratégiques O(1)"""
        
        meilleure_pos = -1
        meilleure_dist = float('inf')
        
        # Positions stratégiques à tester
        positions = [1]  # début
        
        if len(route) > 3:
            positions.append(len(route)//2)  # milieu
        
        positions.append(len(route)-1)  # fin
        
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
        """
        Algorithme en O(n log n)
        """
        n = len(self.clients)
        
        # ÉTAPE 1: TRI PAR URGENCE (O(n log n))
        clients_avec_fin = [(self.clients[i]['fin'], i+1) for i in range(n)]
        clients_avec_fin.sort()  # tri par fin croissant
        clients_tries = [c[1] for c in clients_avec_fin]
        
        # ÉTAPE 2: CONSTRUCTION (O(n))
        non_visites = set(clients_tries)
        solution = []
        
        while non_visites:
            # Prendre le client le plus urgent (premier dans l'ordre trié)
            seed = None
            for c in clients_tries:
                if c in non_visites:
                    seed = c
                    break
            
            if seed is None:
                break
            
            # Créer nouvelle route
            route = [0, seed, 0]
            non_visites.remove(seed)
            
            # Ajouter d'autres clients compatibles
            amelioration = True
            while amelioration and non_visites:
                amelioration = False
                
                # Parcourir les clients dans l'ordre trié
                for c in list(non_visites):  # copie pour éviter modification pendant itération
                    if self.peut_ajouter_rapide(route, c):
                        if self.inserer_meilleur_endroit(route, c):
                            non_visites.remove(c)
                            amelioration = True
                            break  # recommencer la boucle avec nouveau route
            
            solution.append(route)
        
        return solution
    
    def afficher_resultats(self, solution):
        """Affiche la solution et ses caractéristiques"""
        print(f"\n{'='*60}")
        print(f"SOLUTION RAPIDE O(n log n)")
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

# ==========================
# Exécution sur 3 instances
# ==========================
if __name__ == "__main__":

    fichiers = ["C101.txt", "R101.txt", "RC101.txt"]

    print("\n" + "="*70)
    print("TEST DE L'ALGORITHME RAPIDE O(n log n)")
    print("="*70)

    for fichier in fichiers:
        print("\n" + "-"*70)
        print(f"Instance : {fichier}")
        print("-"*70)

        init = InitialisationRapideVRPTW(fichier)
        solution = init.generer_solution_rapide()

        nb_vehicules = len(solution)
        distance_totale = sum(init.calculer_distance_route(r) for r in solution)
        cout = init.calculer_cout(solution)
        faisable = init.verifier_solution(solution)

        print(f"Véhicules utilisés : {nb_vehicules} / {init.nb_vehicules_max}")
        print(f"Distance totale    : {distance_totale:.2f}")
        print(f"Coût total         : {cout:.2f}")
        print(f"Solution réalisable: {faisable}")