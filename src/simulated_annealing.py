import random
import math
import copy
from solution import Solution
from operators import Operators

class SimulatedAnnealing:
    """Recuit simulé complet"""
    
    def __init__(self, data, operators):
        self.data = data
        self.operators = operators
        self.n = data['n']
    
    def estimate_t0(self, solution, taux_accept=0.8, nb_samples=100):
        """Estime la température initiale"""
        deltas = []
        
        for _ in range(nb_samples):
            voisin = self.operators.relocate(solution)
            delta = voisin.total_cost() - solution.total_cost()
            if delta > 0:
                deltas.append(delta)
        
        if not deltas:
            return 100.0
        
        delta_moy = sum(deltas) / len(deltas)
        return -delta_moy / math.log(taux_accept)
    
    def run(self, solution_initiale, alpha_cool=0.95, 
            iter_par_palier=None, use_adaptive_weights=True,
            use_route_merge=True, use_auto_t0=True):
        """Exécute le recuit simulé"""
        
        # Paramètres
        if iter_par_palier is None:
            iter_par_palier = 100 * self.n
        
        if use_auto_t0:
            T0 = self.estimate_t0(solution_initiale)
        else:
            T0 = 100.0
        
        T_fin = 0.01
        
        # Initialisation
        solution_courante = solution_initiale.copy()
        meilleure_solution = solution_initiale.copy()
        T = T0
        
        # Poids adaptatifs
        operators_list = ['or_opt_1', 'or_opt_2', 'or_opt_3', 'relocate', 'swap']
        if use_adaptive_weights:
            poids = [1.0] * len(operators_list)
            scores = [0] * len(operators_list)
            utilisations = [0] * len(operators_list)
        else:
            poids = [1.0] * len(operators_list)
        
        segment = 0
        
        while T > T_fin:
            for it in range(iter_par_palier):
                # Sélection opérateur
                if use_adaptive_weights:
                    op = random.choices(range(len(operators_list)), weights=poids)[0]
                    utilisations[op] += 1
                else:
                    op = random.randint(0, len(operators_list)-1)
                
                # Générer voisin
                nouvelle_sol = self._apply_operator(solution_courante, operators_list[op])
                
                # Évaluation
                delta_E = nouvelle_sol.total_cost() - solution_courante.total_cost()
                
                # Décision d'acceptation
                if delta_E < 0:
                    solution_courante = nouvelle_sol
                    if use_adaptive_weights:
                        scores[op] += 3
                    
                    if nouvelle_sol.total_cost() < meilleure_solution.total_cost():
                        meilleure_solution = nouvelle_sol.copy()
                        if use_adaptive_weights:
                            scores[op] += 2
                else:
                    if random.random() < math.exp(-delta_E / T):
                        solution_courante = nouvelle_sol
                        if use_adaptive_weights:
                            scores[op] += 1
            
            # Refroidissement
            T *= alpha_cool
            segment += 1
            
            # Mise à jour poids adaptatifs
            if use_adaptive_weights and segment % 10 == 0:
                for op in range(len(operators_list)):
                    if utilisations[op] > 0:
                        avg_score = scores[op] / utilisations[op]
                        poids[op] = 0.6 * poids[op] + 0.4 * avg_score
                    scores[op] = 0
                    utilisations[op] = 0
            
            # Route Merge tardif
            if use_route_merge and T < 0.5 * T0:
                solution_courante = self.operators.route_merge(solution_courante)
        
        return meilleure_solution
    
    def _apply_operator(self, solution, operator_name):
        """Applique un opérateur"""
        if operator_name == 'or_opt_1':
            return self.operators.or_opt(solution, segment_size=1)
        elif operator_name == 'or_opt_2':
            return self.operators.or_opt(solution, segment_size=2)
        elif operator_name == 'or_opt_3':
            return self.operators.or_opt(solution, segment_size=3)
        elif operator_name == 'relocate':
            return self.operators.relocate(solution)
        elif operator_name == 'swap':
            return self.operators.swap(solution)
        else:
            return solution