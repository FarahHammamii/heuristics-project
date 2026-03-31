import random
import math
from solution import Solution

class Initialisation:
    """Classe contenant les 3 méthodes d'initialisation"""
    
    def __init__(self, data):
        self.data = data
        self.n = data['n']
        self.dist = data['distance']
        self.cap = data['capacity']
        self.customers = data['customers']
    
    # ==================== MÉTHODE 1: NEAREST NEIGHBOR RANDOMISÉ ====================
    
    def nearest_neighbor_randomise(self, k_candidats=3, nb_restarts=5, alpha=1, beta=1):
        """Nearest Neighbor Randomisé"""
        best_solution = None
        best_cost = float('inf')
        
        for restart in range(nb_restarts):
            solution = self._build_nn_solution(k_candidats, alpha, beta)
            if solution and solution.is_feasible():
                cost = solution.total_cost()
                if cost < best_cost:
                    best_cost = cost
                    best_solution = solution
        
        return best_solution
    
    def _build_nn_solution(self, k_candidats, alpha, beta):
        """Construit une solution avec NN randomisé"""
        unvisited = set(range(1, self.n))
        routes = []
        
        while unvisited:
            route = [0]
            charge = 0
            time = self.customers[0]['ready_time']
            
            while True:
                position = route[-1]
                candidates = []
                
                for c in unvisited:
                    arrivee = time + self.dist[position][c]
                    
                    if (arrivee <= self.customers[c]['due_date'] and
                        charge + self.customers[c]['demand'] <= self.cap and
                        arrivee + self.customers[c]['service_time'] + self.dist[c][0] <= self.customers[0]['due_date']):
                        
                        score = (alpha * self.dist[position][c] + 
                                beta * max(0, self.customers[c]['ready_time'] - arrivee))
                        candidates.append((c, score))
                
                if not candidates:
                    break
                
                candidates.sort(key=lambda x: x[1])
                pool = candidates[:min(k_candidats, len(candidates))]
                
                if len(pool) == 1:
                    chosen = pool[0][0]
                else:
                    weights = [1.0/(c[1] + 1e-10) for c in pool]
                    total = sum(weights)
                    probs = [w/total for w in weights]
                    chosen = random.choices([c[0] for c in pool], weights=probs)[0]
                
                route.append(chosen)
                unvisited.remove(chosen)
                
                arrivee = time + self.dist[position][chosen]
                time = max(arrivee, self.customers[chosen]['ready_time']) + self.customers[chosen]['service_time']
                charge += self.customers[chosen]['demand']
            
            route.append(0)
            routes.append(route)
        
        return Solution(routes, self.data)
    
    # ==================== MÉTHODE 2: SOLOMON I1 RANDOMISÉ ====================
    
    def _verifier_route(self, route):
        """
        Vérifie la faisabilité d'une route - EXACTEMENT comme dans le test file
        """
        if route[0] != 0 or route[-1] != 0:
            return False
        
        charge = 0
        temps = self.customers[0]['ready_time']
        courant = 0
        
        for i in range(1, len(route)):
            client_id = route[i]
            
            if client_id == 0:  # Retour au dépôt
                trajet = self.dist[courant][0]
                temps += trajet
                if temps > self.customers[0]['due_date']:
                    return False
                continue
            
            client = self.customers[client_id]
            
            # Capacité
            charge += client['demand']
            if charge > self.cap:
                return False
            
            # Trajet
            trajet = self.dist[courant][client_id]
            temps += trajet
            
            # Fenêtre de temps
            if temps > client['due_date']:
                return False
            
            # Attente si nécessaire
            if temps < client['ready_time']:
                temps = client['ready_time']
            
            # Temps de service
            temps += client['service_time']
            courant = client_id
        
        return True
    
    def _calculer_temps_arrivee(self, route, index):
        """
        Calcule le temps d'arrivée à une position - EXACTEMENT comme dans le test file
        """
        temps = self.customers[0]['ready_time']
        courant = 0
        
        for k in range(1, index + 1):
            client_id = route[k]
            if client_id == 0:
                return temps + self.dist[courant][0]
            
            client = self.customers[client_id]
            dist = self.dist[courant][client_id]
            temps = max(temps + dist, client['ready_time'])
            
            if k < index:
                temps += client['service_time']
            
            courant = client_id
        
        return temps
    
    def solomon_randomise(self, p_urgents=0.3, k_best=3, max_retries=5):
        """
        Solomon I1 Randomisé - Génère uniquement des solutions faisables.

        Principe :
        1. Priorité aux clients urgents (p_urgents).
        2. α et β tirés aléatoirement pour chaque nouvelle route.
        3. Insertion basée sur coût distance supplémentaire (C1) + retard (C2).
        4. Choix aléatoire parmi les k meilleurs candidats.
        5. Garantie que la solution finale est faisable.
        """

        for attempt in range(max_retries):
            solution_routes = []
            non_visites = set(range(1, self.n))  # tous les clients sauf dépôt

            while non_visites:
                # Randomisation α et β pour cette route
                alpha = random.uniform(0.5, 1.5)
                beta = random.uniform(0.5, 1.5)

                # Sélection du germe parmi les clients urgents
                sorted_customers = sorted(non_visites, key=lambda c: self.customers[c]['due_date'])
                nb_urgents = max(1, int(p_urgents * len(non_visites)))
                germes_urgents = sorted_customers[:nb_urgents]

                # Filtrer uniquement les germes faisables
                feasible_germes = [c for c in germes_urgents
                                if Solution([[0, c, 0]], self.data).is_route_feasible([0, c, 0])]

                if not feasible_germes:
                    # Si aucun germe faisable parmi les urgents, choisir le plus urgent faisable
                    for c in sorted_customers:
                        if Solution([[0, c, 0]], self.data).is_route_feasible([0, c, 0]):
                            feasible_germes.append(c)
                            break

                if not feasible_germes:
                    # Aucun germe faisable → abandon de cette construction
                    break

                # Choisir aléatoirement un germe faisable
                germe = random.choice(feasible_germes)
                route = [0, germe, 0]
                non_visites.remove(germe)

                # Insertion séquentielle des autres clients
                while True:
                    candidates = []

                    for client in non_visites:
                        for pos in range(1, len(route)):
                            candidate_route = route[:pos] + [client] + route[pos:]

                            # Vérifie faisabilité avec Solution
                            if Solution([candidate_route], self.data).is_route_feasible(candidate_route):
                                i, j = route[pos - 1], route[pos]
                                # C1 : coût distance supplémentaire
                                C1 = self.dist[i][client] + self.dist[client][j] - self.dist[i][j]
                                # C2 : retard causé au client inséré et successeurs
                                t_before = self._calculer_temps_arrivee(route, pos)
                                t_after = self._calculer_temps_arrivee(candidate_route, pos + 1)
                                C2 = max(0, t_after - t_before)
                                total_cost = alpha * C1 + beta * C2
                                candidates.append((client, pos, candidate_route, total_cost))

                    if not candidates:
                        # Aucune insertion faisable → fin de la route
                        break

                    # Randomisation parmi les k meilleures candidates
                    candidates.sort(key=lambda x: x[3])
                    pool = candidates[:min(k_best, len(candidates))]
                    chosen_client, _, chosen_route, _ = random.choice(pool)

                    # Met à jour la route et supprime le client de non_visites
                    route = chosen_route
                    non_visites.remove(chosen_client)

                solution_routes.append(route)

            # Vérification finale de faisabilité
            sol = Solution(solution_routes, self.data)
            if sol.is_feasible():
                return sol

        # Si aucune solution faisable trouvée après max_retries
        return None

    # ==================== MÉTHODE 3: REGRET-2 ====================
    
    def regret_based_init(self, epsilon=0.1):
        """Regret-2 avec bruit"""
        unvisited = set(range(1, self.n))
        routes = []
        
        while unvisited:
            # Trouver le germe (client le plus urgent)
            feasible_germs = []
            for c in unvisited:
                route_test = [0, c, 0]
                if self._verifier_route(route_test):
                    feasible_germs.append(c)
            
            if not feasible_germs:
                germe = min(unvisited, key=lambda c: self.customers[c]['due_date'])
            else:
                germe = min(feasible_germs, key=lambda c: self.customers[c]['due_date'])
            
            route = [0, germe, 0]
            unvisited.remove(germe)
            
            improved = True
            while improved and unvisited:
                improved = False
                max_regret = -float('inf')
                best_client = None
                best_pos = -1
                best_route = None
                
                for u in unvisited:
                    insertions = []
                    
                    for p in range(1, len(route)):
                        route_test = route[:p] + [u] + route[p:]
                        if self._verifier_route(route_test):
                            i = route[p-1]
                            j = route[p]
                            cost = self.dist[i][u] + self.dist[u][j] - self.dist[i][j]
                            cost = cost * (1 + random.uniform(-epsilon, epsilon))
                            insertions.append((cost, p, route_test))
                    
                    if not insertions:
                        continue
                    
                    insertions.sort(key=lambda x: x[0])
                    
                    if len(insertions) >= 2:
                        regret = insertions[1][0] - insertions[0][0]
                    else:
                        regret = insertions[0][0]
                    
                    if regret > max_regret:
                        max_regret = regret
                        best_client = u
                        best_pos = insertions[0][1]
                        best_route = insertions[0][2]
                
                if best_client is not None:
                    route = best_route
                    unvisited.remove(best_client)
                    improved = True
            
            routes.append(route)
        
        return Solution(routes, self.data)
    
    def _check_insertion_feasible(self, route, client, pos):
        """Helper method"""
        route_test = route[:pos] + [client] + route[pos:]
        return self._verifier_route(route_test)
    
    def _insertion_cost(self, route, client, pos):
        """Helper method"""
        i = route[pos-1]
        j = route[pos] if pos < len(route) else 0
        return self.dist[i][client] + self.dist[client][j] - self.dist[i][j]