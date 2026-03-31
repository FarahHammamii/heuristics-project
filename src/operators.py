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
        """Déplace un client (relocate) vers la meilleure position possible (inter ou intra-route)"""
        new_sol = solution.copy()  # Utilise ta classe Solution avec .copy()
        
        if not new_sol.routes:
            return new_sol
        
        # 1. Sélection aléatoire d'une route et d'un client
        route_idx = random.randint(0, len(new_sol.routes) - 1)
        route = new_sol.routes[route_idx]
        
        if len(route) <= 2:  # Seulement dépôt + dépôt
            return new_sol
        
        pos = random.randint(1, len(route) - 2)  # pas les dépôts
        client = route[pos]
        
        # Retirer temporairement le client
        new_sol.routes[route_idx] = route[:pos] + route[pos + 1:]
        
        # 2. Chercher la meilleure position d'insertion (toutes routes)
        best_delta = float('inf')
        best_route_idx = -1
        best_pos = -1
        
        for r_idx, r in enumerate(new_sol.routes):
            for q in range(1, len(r)):  # positions d'insertion possibles
                # Éviter d'insérer au même endroit (même route)
                if r_idx == route_idx and q == pos:
                    continue
                
                delta = self._insertion_delta(r, client, q)
                
                if delta < best_delta:
                    test_route = r[:q] + [client] + r[q:]
                    if self._is_route_feasible(test_route):
                        best_delta = delta
                        best_route_idx = r_idx
                        best_pos = q
        
        # 3. Appliquer le meilleur mouvement si trouvé
        if best_route_idx != -1:
            # Insérer
            route_j = new_sol.routes[best_route_idx]
            route_j.insert(best_pos, client)
            new_sol.routes[best_route_idx] = route_j
            
            # Nettoyer les routes vides (seulement [0,0])
            new_sol.routes = [r for r in new_sol.routes if len(r) > 2]
        else:
            # Aucun mouvement valide → on remet le client à sa place originale
            new_sol.routes[route_idx] = route  # restauration
        
        return new_sol



    # ==================== OR-OPT  ====================
    def or_opt(self, solution, segment_size=1):
        """Or-Opt : déplace un segment de 1, 2 ou 3 clients consécutifs (meilleure amélioration)"""
        if segment_size not in (1, 2, 3):
            segment_size = 1
        
        new_sol = solution.copy()
        best_delta = float('inf')      # On cherche le delta le plus négatif (meilleure amélioration)
        best_move = None
        
        for i, route_i in enumerate(new_sol.routes):
            for p in range(1, len(route_i) - segment_size):  # position de début du segment
                segment = route_i[p : p + segment_size]
                avant_i = route_i[p - 1]
                apres_i = route_i[p + segment_size]
                
                # Coût du retrait du segment
                delta_retrait = (self.dist[avant_i][apres_i] -
                                self.dist[avant_i][segment[0]] -
                                self.dist[segment[-1]][apres_i])
                
                for j, route_j in enumerate(new_sol.routes):
                    for q in range(1, len(route_j)):  # position d'insertion
                        # Éviter insertion dans le segment retiré (même route)
                        if i == j and q > p - 1 and q < p + segment_size + 1:
                            continue
                        
                        avant_j = route_j[q - 1]
                        apres_j = route_j[q]
                        
                        # Coût de l'insertion
                        delta_insertion = (self.dist[avant_j][segment[0]] +
                                        self.dist[segment[-1]][apres_j] -
                                        self.dist[avant_j][apres_j])
                        
                        delta_total = delta_retrait + delta_insertion
                        
                        if delta_total < best_delta:  # meilleur delta (plus négatif = mieux)
                            # Tests de faisabilité
                            route_i_test = route_i[:p] + route_i[p + segment_size:]
                            route_j_test = route_j[:q] + segment + route_j[q:]
                            
                            if (self._is_route_feasible(route_i_test) and
                                self._is_route_feasible(route_j_test)):
                                best_delta = delta_total
                                best_move = (i, p, j, q, segment, delta_total)
        
        # Appliquer le meilleur mouvement trouvé
        if best_move and best_delta < 0:  # On n'applique que si amélioration (ou on peut assouplir dans SA)
            i, p, j, q, segment, _ = best_move
            # Retirer le segment de route_i
            route_i = new_sol.routes[i]
            new_sol.routes[i] = route_i[:p] + route_i[p + len(segment):]
            
            # Insérer dans route_j
            route_j = new_sol.routes[j]
            new_sol.routes[j] = route_j[:q] + segment + route_j[q:]
            
            # Nettoyer routes vides
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
        """Échange deux clients - cherche la meilleure paire à échanger"""
        new_sol = solution.copy()
        
        if len(new_sol.routes) < 2:
            return new_sol
        
        best_delta = float('inf')
        best_move = None
        
        # Chercher la meilleure paire à échanger
        for i, route_i in enumerate(new_sol.routes):
            if len(route_i) <= 2:  # route vide ou juste dépôt
                continue
                
            for pos_i in range(1, len(route_i)-1):  # pour chaque client dans route_i
                client_i = route_i[pos_i]
                
                for j, route_j in enumerate(new_sol.routes):
                    if j == i:  # même route, on pourrait aussi autoriser mais c'est plus complexe
                        continue
                        
                    if len(route_j) <= 2:
                        continue
                        
                    for pos_j in range(1, len(route_j)-1):  # pour chaque client dans route_j
                        client_j = route_j[pos_j]
                        
                        # Calculer le delta si on échange
                        # Avant: ... client_i ... et ... client_j ...
                        # Après: ... client_j ... et ... client_i ...
                        
                        # Coût avant
                        before_i_left = route_i[pos_i-1]
                        before_i_right = route_i[pos_i+1] if pos_i+1 < len(route_i) else 0
                        before_j_left = route_j[pos_j-1]
                        before_j_right = route_j[pos_j+1] if pos_j+1 < len(route_j) else 0
                        
                        cost_before = (self.dist[before_i_left][client_i] + 
                                    self.dist[client_i][before_i_right] +
                                    self.dist[before_j_left][client_j] + 
                                    self.dist[client_j][before_j_right])
                        
                        # Coût après
                        cost_after = (self.dist[before_i_left][client_j] + 
                                    self.dist[client_j][before_i_right] +
                                    self.dist[before_j_left][client_i] + 
                                    self.dist[client_i][before_j_right])
                        
                        delta = cost_after - cost_before
                        
                        if delta < best_delta:
                            # Vérifier faisabilité
                            new_route_i = route_i[:pos_i] + [client_j] + route_i[pos_i+1:]
                            new_route_j = route_j[:pos_j] + [client_i] + route_j[pos_j+1:]
                            
                            if (self._is_route_feasible(new_route_i) and 
                                self._is_route_feasible(new_route_j)):
                                best_delta = delta
                                best_move = (i, pos_i, j, pos_j, client_i, client_j)
        
        # Appliquer le meilleur mouvement
        if best_move and best_delta < 0:  # seulement si amélioration
            i, pos_i, j, pos_j, client_i, client_j = best_move
            route_i = new_sol.routes[i]
            route_j = new_sol.routes[j]
            
            new_route_i = route_i[:pos_i] + [client_j] + route_i[pos_i+1:]
            new_route_j = route_j[:pos_j] + [client_i] + route_j[pos_j+1:]
            
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