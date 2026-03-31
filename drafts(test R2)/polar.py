import math
import numpy as np
from typing import List, Tuple, Dict

class VRPTWInitializer:
    def __init__(self, filename):
        self.filename = filename
        self.nb_vehicles = 0
        self.capacity = 0
        self.customers = []
        self.depot = None
        self.distance_matrix = []
        self.load_data()
        self.compute_distances()
    
    def load_data(self):
        """Charge les données du fichier C101.txt"""
        with open(self.filename, 'r') as f:
            lines = f.readlines()
        
        # Parser le fichier
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if line.startswith('VEHICLE'):
                i += 2  # Skip header
                vehicle_line = lines[i].strip().split()
                self.nb_vehicles = int(vehicle_line[0])
                self.capacity = int(vehicle_line[1])
            elif line.startswith('CUSTOMER'):
                i += 3  # Skip headers
                while i < len(lines) and lines[i].strip():
                    data = lines[i].strip().split()
                    if len(data) >= 7:
                        cust = {
                            'id': int(data[0]),
                            'x': float(data[1]),
                            'y': float(data[2]),
                            'demand': float(data[3]),
                            'ready_time': float(data[4]),
                            'due_date': float(data[5]),
                            'service': float(data[6])
                        }
                        if cust['id'] == 0:
                            self.depot = cust
                        else:
                            self.customers.append(cust)
                    i += 1
            i += 1
    
    def compute_distances(self):
        """Calcule la matrice des distances"""
        all_points = [self.depot] + self.customers
        n = len(all_points)
        self.distance_matrix = [[0.0] * n for _ in range(n)]
        
        for i in range(n):
            for j in range(n):
                if i != j:
                    dx = all_points[i]['x'] - all_points[j]['x']
                    dy = all_points[i]['y'] - all_points[j]['y']
                    self.distance_matrix[i][j] = math.sqrt(dx*dx + dy*dy)
    
    def get_customer_index(self, cust_id):
        """Retourne l'index dans la matrice (0 = dépôt)"""
        return cust_id  # Les IDs correspondent aux indices
    
    def verifier_route(self, route):

        if route[0] != 0 or route[-1] != 0:
            return False

        charge = 0
        temps = self.depot['ready_time']
        current = 0

        for client_id in route[1:-1]:

            client = self.customers[client_id - 1]

            # capacité
            charge += client['demand']
            if charge > self.capacity:
                return False

            # déplacement
            trajet = self.distance_matrix[current][client_id]
            arrivee = temps + trajet

            # fenêtre de temps
            if arrivee > client['due_date']:
                return False

            # attente
            arrivee = max(arrivee, client['ready_time'])

            temps = arrivee + client['service']
            current = client_id

        # retour dépôt
        retour = temps + self.distance_matrix[current][0]
        if retour > self.depot['due_date']:
            return False

        return True
    
    def calculer_distance_route(self, route: List[int]) -> float:
        """Calcule la distance totale d'une route"""
        distance = 0.0
        for i in range(1, len(route)):
            distance += self.distance_matrix[route[i-1]][route[i]]
        return distance
    
    def calculer_cout(self, solution: List[List[int]]) -> float:
        """Calcule le coût total d'une solution"""
        nb_vehicules = len(solution)
        distance_totale = sum(self.calculer_distance_route(r) for r in solution)
        alpha = 1000
        return alpha * nb_vehicules + distance_totale
    
    def initialisation_polaire(self):
        """
        Algorithme innovant d'initialisation par regroupement polaire
        Complexité O(n log n)
        """
        n = len(self.customers)
        
        # Étape 1: Calcul des angles polaires
        angles = []
        for i, cust in enumerate(self.customers):
            dx = cust['x'] - self.depot['x']
            dy = cust['y'] - self.depot['y']
            angle = math.atan2(dy, dx)
            if angle < 0:
                angle += 2 * math.pi
            angles.append((angle, i+1))  # i+1 = ID client
        
        # Trier par angle
        angles.sort(key=lambda x: x[0])
        clients_par_angle = [c[1] for c in angles]
        
        # Étape 2: Regroupement en clusters polaires
        demande_totale = sum(c['demand'] for c in self.customers)
        k_estime = max(1, math.ceil(demande_totale / (0.8 * self.capacity)))
        k_estime = min(k_estime, self.nb_vehicles)
        
        taille_groupe = n / k_estime
        clusters = [[] for _ in range(k_estime)]
        
        for i, client_id in enumerate(clients_par_angle):
            idx_cluster = min(int(i / taille_groupe), k_estime - 1)
            clusters[idx_cluster].append(client_id)
        
        # Étape 3: Tri dans chaque cluster par fenêtre de temps
        for cluster in clusters:
            # Trier par ready_time
            cluster.sort(key=lambda c: self.customers[c-1]['ready_time'])
            
            # Optimisation: plus proche voisin local
            cluster = self.optimiser_ordre_cluster(cluster)
        
        # Étape 4: Construction des routes
        solution = []
        
        for cluster in clusters:
            if not cluster:
                continue
                
            route = [0]
            charge_actuelle = 0
            temps_actuel = self.depot['ready_time']
            
            for client_id in cluster:
                # Essayer d'ajouter le client
                route_test = route + [client_id, 0]
                
                if self.verifier_route(route_test):
                    route.insert(-1, client_id)  # Ajouter avant le dernier 0
                    client = self.customers[client_id - 1]
                    charge_actuelle += client['demand']
                    
                    # Mettre à jour temps
                    trajet = self.distance_matrix[route[-3] if len(route) > 2 else 0][client_id]
                    arrivee = temps_actuel + trajet
                    if arrivee < client['ready_time']:
                        arrivee = client['ready_time']
                    temps_actuel = arrivee + client['service']
                else:
                    # Nouvelle route
                    if len(route) > 1:
                        route.append(0)
                        solution.append(route)
                    
                    route = [0, client_id]
                    client = self.customers[client_id - 1]
                    charge_actuelle = client['demand']
                    
                    trajet = self.distance_matrix[0][client_id]
                    arrivee = trajet
                    if arrivee < client['ready_time']:
                        arrivee = client['ready_time']
                    temps_actuel = arrivee + client['service']
            
            # Fermer la dernière route du cluster
            if len(route) > 1:
                route.append(0)
                solution.append(route)
        
        # Étape 5: Optimisation locale simple
        solution = self.optimiser_routes(solution)
        
        return solution
    
    def optimiser_ordre_cluster(self, cluster):
        """Optimise l'ordre des clients dans un cluster"""
        if len(cluster) <= 2:
            return cluster
        
        # Version plus proche voisin dans le cluster
        ordre_nn = [cluster[0]]
        non_places = set(cluster[1:])
        courant = cluster[0]
        
        while non_places:
            # Trouver le plus proche
            prochain = min(non_places, 
                          key=lambda c: self.distance_matrix[courant][c])
            ordre_nn.append(prochain)
            non_places.remove(prochain)
            courant = prochain
        
        return ordre_nn
    
    def optimiser_routes(self, solution):
        """Optimisation locale simple"""
        for i in range(len(solution)):
            route = solution[i]
            if len(route) <= 3:
                continue
            
            amelioration = True
            while amelioration:
                amelioration = False
                for j in range(1, len(route)-2):
                    for k in range(j+1, len(route)-1):
                        # Échanger
                        nouvelle_route = route[:]
                        nouvelle_route[j], nouvelle_route[k] = nouvelle_route[k], nouvelle_route[j]
                        
                        if self.verifier_route(nouvelle_route):
                            if (self.calculer_distance_route(nouvelle_route) < 
                                self.calculer_distance_route(route)):
                                route = nouvelle_route
                                amelioration = True
                                break
                    if amelioration:
                        break
            solution[i] = route
        
        return solution
    
    def afficher_solution(self, solution):
        """Affiche la solution de façon lisible"""
        print(f"\n{'='*60}")
        print(f"SOLUTION GÉNÉRÉE - {len(solution)} véhicules utilisés")
        print(f"{'='*60}")
        
        total_distance = 0
        for i, route in enumerate(solution):
            dist = self.calculer_distance_route(route)
            total_distance += dist
            clients = [str(c) for c in route[1:-1]]
            print(f"Route {i+1}: 0 → {' → '.join(clients)} → 0")
            print(f"         Distance: {dist:.2f}")
        
        cout = self.calculer_cout(solution)
        print(f"\nDistance totale: {total_distance:.2f}")
        print(f"Coût total (α=1000): {cout:.2f}")
        
        # Vérification
        if self.verifier_solution(solution):
            print("✓ Solution réalisable")
        else:
            print("✗ Solution non réalisable!")
    
    def verifier_solution(self, solution):
        """Vérifie une solution complète"""
        clients_visites = set()
        
        for route in solution:
            if not self.verifier_route(route):
                return False
            
            for c in route[1:-1]:
                if c in clients_visites:
                    return False
                clients_visites.add(c)
        
        return len(clients_visites) == len(self.customers)


# Utilisation
if __name__ == "__main__":
    initializer = VRPTWInitializer("C101.txt")
    solution = initializer.initialisation_polaire()
    initializer.afficher_solution(solution)
    
    # Comparaison avec méthode aléatoire simple
    print("\n" + "="*60)
    print("COMPARAISON AVEC MÉTHODE ALÉATOIRE")
    print("="*60)
    
    import random
    random_solution = []
    clients = list(range(1, len(initializer.customers)+1))
    random.shuffle(clients)
    
    route = [0]
    for c in clients:
        route_test = route + [c, 0]
        if initializer.verifier_route(route_test):
            route.insert(-1, c)
        else:
            route.append(0)
            random_solution.append(route)
            route = [0, c]
    route.append(0)
    random_solution.append(route)
    
    print("Solution aléatoire:")
    print(f"  Véhicules: {len(random_solution)}")
    print(f"  Coût: {initializer.calculer_cout(random_solution):.2f}")
    print(f"Solution polaire:")
    print(f"  Véhicules: {len(solution)}")
    print(f"  Coût: {initializer.calculer_cout(solution):.2f}")