import random
import copy
from solution import Solution

class Operators:
    """Classe contenant tous les opérateurs de voisinage"""
    
    def __init__(self, data):
        self.data = data
        self.dist = data['distance']
    
    # ==================== RELOCATE ====================
    
    def relocate(self, solution):
        """Déplace un client vers la meilleure position"""
        new_sol = solution.copy()
        
        if len(new_sol.routes) == 0:
            return new_sol
        
        # Choisir route aléatoire
        route_idx = random.randint(0, len(new_sol.routes)-1)
        route = new_sol.routes[route_idx]
        
        if len(route) <= 2:
            return new_sol
        
        # Choisir client aléatoire (pas le dépôt)
        pos = random.randint(1, len(route)-2)
        client = route[pos]
        
        # Retirer le client
        new_route = route[:pos] + route[pos+1:]
        new_sol.routes[route_idx] = new_route
        
        # Trouver meilleure insertion
        best_cost = float('inf')
        best_route_idx = -1
        best_pos = -1
        
        for r_idx, route_j in enumerate(new_sol.routes):
            for q in range(1, len(route_j)):
                # Calculer delta
                delta = self._insertion_delta(route_j, client, q)
                
                if delta < best_cost:
                    # Vérifier faisabilité
                    test_route = route_j[:q] + [client] + route_j[q:]
                    if self._is_route_feasible(test_route):
                        best_cost = delta
                        best_route_idx = r_idx
                        best_pos = q
        
        if best_route_idx != -1:
            # Insérer à la meilleure position
            route_j = new_sol.routes[best_route_idx]
            route_j.insert(best_pos, client)
            new_sol.routes[best_route_idx] = route_j
            
            # Supprimer route vide
            new_sol.routes = [r for r in new_sol.routes if len(r) > 2]
        
        return new_sol
    
    # ==================== OR-OPT ====================
    
    def or_opt(self, solution, segment_size=1):
        """Déplace un segment de taille 1, 2 ou 3"""
        new_sol = solution.copy()
        best_delta = 0
        best_move = None
        
        for i, route_i in enumerate(new_sol.routes):
            for p in range(1, len(route_i) - segment_size - 1):
                # Extraire segment
                segment = route_i[p:p+segment_size]
                avant_i = route_i[p-1]
                apres_i = route_i[p+segment_size]
                
                # Coût de retrait
                delta_retrait = (self.dist[avant_i][apres_i] - 
                                self.dist[avant_i][segment[0]] - 
                                self.dist[segment[-1]][apres_i])
                
                for j, route_j in enumerate(new_sol.routes):
                    for q in range(1, len(route_j)):
                        # Éviter insertion dans le trou
                        if i == j and (q >= p and q <= p+segment_size):
                            continue
                        
                        avant_j = route_j[q-1]
                        apres_j = route_j[q]
                        
                        # Coût d'insertion
                        delta_insertion = (self.dist[avant_j][segment[0]] + 
                                          self.dist[segment[-1]][apres_j] - 
                                          self.dist[avant_j][apres_j])
                        
                        delta_total = delta_retrait + delta_insertion
                        
                        if delta_total < best_delta:
                            # Vérifier faisabilité
                            route_j_test = route_j[:q] + segment + route_j[q:]
                            route_i_test = route_i[:p] + route_i[p+segment_size:]
                            
                            if (self._is_route_feasible(route_j_test) and 
                                self._is_route_feasible(route_i_test)):
                                best_delta = delta_total
                                best_move = (i, p, j, q, segment)
        
        if best_move:
            i, p, j, q, segment = best_move
            # Appliquer le mouvement
            route_i = new_sol.routes[i]
            route_j = new_sol.routes[j]
            
            # Retirer segment
            new_route_i = route_i[:p] + route_i[p+len(segment):]
            
            # Insérer segment
            new_route_j = route_j[:q] + segment + route_j[q:]
            
            new_sol.routes[i] = new_route_i
            new_sol.routes[j] = new_route_j
            
            # Supprimer routes vides
            new_sol.routes = [r for r in new_sol.routes if len(r) > 2]
        
        return new_sol
    
    # ==================== ROUTE MERGE ====================
    
    def route_merge(self, solution):
        """Fusionne deux routes"""
        new_sol = solution.copy()
        
        # Trier par longueur croissante
        new_sol.routes.sort(key=len)
        
        for i in range(len(new_sol.routes)):
            for j in range(i+1, len(new_sol.routes)):
                route_i = new_sol.routes[i]
                route_j = new_sol.routes[j]
                
                # Essayer les 4 combinaisons
                combos = [
                    route_i[:-1] + route_j[1:],  # i + j
                    route_j[:-1] + route_i[1:],  # j + i
                    route_i[:-1] + route_j[::-1][1:],  # i + reverse(j)
                    route_i[::-1][:-1] + route_j[1:],  # reverse(i) + j
                ]
                
                for combo in combos:
                    test_route = [0] + combo + [0]
                    if self._is_route_feasible(test_route):
                        # Fusion réussie
                        new_sol.routes.pop(j)
                        new_sol.routes.pop(i)
                        new_sol.routes.append(test_route)
                        return new_sol
        
        return new_sol
    
    # ==================== SWAP ====================
    
    def swap(self, solution):
        """Échange deux clients entre routes"""
        new_sol = solution.copy()
        
        if len(new_sol.routes) < 2:
            return new_sol
        
        # Choisir deux routes
        i, j = random.sample(range(len(new_sol.routes)), 2)
        route_i = new_sol.routes[i]
        route_j = new_sol.routes[j]
        
        if len(route_i) <= 2 or len(route_j) <= 2:
            return new_sol
        
        # Choisir deux clients
        pos_i = random.randint(1, len(route_i)-2)
        pos_j = random.randint(1, len(route_j)-2)
        
        client_i = route_i[pos_i]
        client_j = route_j[pos_j]
        
        # Échanger
        new_route_i = route_i[:pos_i] + [client_j] + route_i[pos_i+1:]
        new_route_j = route_j[:pos_j] + [client_i] + route_j[pos_j+1:]
        
        if self._is_route_feasible(new_route_i) and self._is_route_feasible(new_route_j):
            new_sol.routes[i] = new_route_i
            new_sol.routes[j] = new_route_j
        
        return new_sol
    
    # ==================== FONCTIONS UTILITAIRES ====================
    
    def _insertion_delta(self, route, client, pos):
        """Calcule delta pour insertion d'un client"""
        i = route[pos-1]
        j = route[pos]
        return self.dist[i][client] + self.dist[client][j] - self.dist[i][j]
    
    def _is_route_feasible(self, route):
        """Vérifie faisabilité d'une route"""
        if len(route) < 2 or route[0] != 0 or route[-1] != 0:
            return False
        
        capacity = 0
        time = self.data['customers'][0]['ready_time']
        
        for idx in range(1, len(route)):
            curr = route[idx]
            prev = route[idx-1]
            
            capacity += self.data['customers'][curr]['demand']
            if capacity > self.data['capacity']:
                return False
            
            time += self.dist[prev][curr]
            
            if time > self.data['customers'][curr]['due_date']:
                return False
            if time < self.data['customers'][curr]['ready_time']:
                time = self.data['customers'][curr]['ready_time']
            
            time += self.data['customers'][curr]['service_time']
        
        time += self.dist[route[-2]][0]
        if time > self.data['customers'][0]['due_date']:
            return False
        
        return True