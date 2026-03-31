import random
import math
from solution import Solution


class SimulatedAnnealing:
    """Recuit simulé simplifié (uniquement relocate)"""
    
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
            iter_par_palier=None, use_auto_t0=True,
            use_route_merge=False):
        """
        Exécute le recuit simulé avec UNIQUEMENT relocate
        
        Paramètres:
        - solution_initiale: solution de départ
        - alpha_cool: facteur de refroidissement (ex: 0.90, 0.95, 0.99)
        - iter_par_palier: nombre d'itérations par palier (None = auto)
        - use_auto_t0: True = estimation auto, False = T0=100
        - use_route_merge: True = fusionner les routes à la fin
        """
        
        # Paramètres
        if iter_par_palier is None:
            iter_par_palier = 50 * self.n  # Réduit pour tests rapides
        
        if use_auto_t0:
            T0 = self.estimate_t0(solution_initiale)
        else:
            T0 = 100.0
        
        T_fin = 5.0  # Température finale plus élevée pour arrêter plus tôt
        
        # Initialisation
        solution_courante = solution_initiale.copy()
        meilleure_solution = solution_initiale.copy()
        meilleur_coût = solution_initiale.total_cost()
        T = T0
        
        palier = 0
        
        while T > T_fin:
            palier += 1
            
            for _ in range(iter_par_palier):
                # UNIQUEMENT RELOCATE
                nouvelle = self.operators.relocate(solution_courante)
                
                # Vérifier si la solution a changé
                if nouvelle.total_cost() == solution_courante.total_cost() and \
                   nouvelle.nb_vehicles() == solution_courante.nb_vehicles():
                    continue
                
                delta = nouvelle.total_cost() - solution_courante.total_cost()
                
                # Décision d'acceptation (Metropolis)
                if delta < 0:
                    # Amélioration → toujours acceptée
                    solution_courante = nouvelle
                    
                    if nouvelle.total_cost() < meilleur_coût:
                        meilleure_solution = nouvelle.copy()
                        meilleur_coût = nouvelle.total_cost()
                else:
                    # Dégradation → acceptée avec probabilité exp(-delta/T)
                    if random.random() < math.exp(-delta / T):
                        solution_courante = nouvelle
            
            # Refroidissement
            T *= alpha_cool
            
            # Afficher progression (optionnel)
            # print(f"  Palier {palier}: T={T:.2f}, meilleur coût={meilleur_coût:.2f}")
        
        # Fusion des routes (optionnel)
        if use_route_merge:
            print("  Application de RouteMerge...")
            meilleure_solution = self.operators.route_merge(meilleure_solution)
        
        return meilleure_solution