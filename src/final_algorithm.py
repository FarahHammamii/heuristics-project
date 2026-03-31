"""
RECUIT SIMULÉ COMPLET - VRPTW
Configuration finale:
- Initialisation: Solomon Randomisé
- Opérateur: Relocate uniquement
- Refroidissement: α_cool = 0.90, T0 = 100, T_fin = 5.0
- Itérations: 500 par palier
"""

import time
import random
import math
from instance_reader import read_instance
from initialisation import Initialisation
from operators import Operators
from solution import Solution


class SimulatedAnnealingFinal:
    """Recuit simulé simplifié avec Relocate uniquement"""
    
    def __init__(self, data, operators):
        self.data = data
        self.operators = operators
        self.n = data['n']
    
    def run(self, solution_initiale, alpha_cool=0.90, 
            iter_par_palier=500, T0=100.0, T_fin=5.0,
            verbose=True):
        """
        Exécute le recuit simulé avec Relocate uniquement
        
        Paramètres:
        - solution_initiale: solution de départ
        - alpha_cool: facteur de refroidissement (0.90)
        - iter_par_palier: nombre d'itérations par palier (500)
        - T0: température initiale (100)
        - T_fin: température finale (5.0)
        - verbose: afficher la progression
        """
        
        # Initialisation
        solution_courante = solution_initiale.copy()
        meilleure_solution = solution_initiale.copy()
        meilleur_coût = solution_initiale.total_cost()
        T = T0
        
        palier = 0
        nb_ameliorations_total = 0
        nb_acceptances_total = 0
        
        if verbose:
            print(f"\n  Début du recuit simulé")
            print(f"  T0 = {T0}, T_fin = {T_fin}, α_cool = {alpha_cool}")
            print(f"  iter_par_palier = {iter_par_palier}")
            print(f"  Coût initial: {solution_initiale.total_cost():.2f}")
            print(f"  Nb véhicules initial: {solution_initiale.nb_vehicles()}")
            print()
        
        start_time = time.time()
        
        while T > T_fin:
            palier += 1
            nb_ameliorations_palier = 0
            nb_acceptances_palier = 0
            
            for _ in range(iter_par_palier):
                # Appliquer Relocate
                nouvelle = self.operators.relocate(solution_courante)
                
                # Vérifier si la solution a changé
                if (nouvelle.total_cost() == solution_courante.total_cost() and 
                    nouvelle.nb_vehicles() == solution_courante.nb_vehicles()):
                    continue
                
                delta = nouvelle.total_cost() - solution_courante.total_cost()
                
                # Décision d'acceptation (Metropolis)
                if delta < 0:
                    # Amélioration → acceptée
                    solution_courante = nouvelle
                    nb_ameliorations_palier += 1
                    nb_ameliorations_total += 1
                    
                    if nouvelle.total_cost() < meilleur_coût:
                        meilleure_solution = nouvelle.copy()
                        meilleur_coût = nouvelle.total_cost()
                else:
                    # Dégradation → acceptée avec probabilité
                    if random.random() < math.exp(-delta / T):
                        solution_courante = nouvelle
                        nb_acceptances_palier += 1
                        nb_acceptances_total += 1
            
            # Refroidissement
            T *= alpha_cool
            
            # Affichage progression
            if verbose and palier % 5 == 0:
                print(f"    Palier {palier}: T={T:.2f}, "
                      f"meilleur coût={meilleur_coût:.2f}, "
                      f"véhicules={meilleure_solution.nb_vehicles()}, "
                      f"amelio={nb_ameliorations_palier}, "
                      f"accept={nb_acceptances_palier}")
        
        elapsed = time.time() - start_time
        
        if verbose:
            print()
            print(f"  Recuit terminé en {elapsed:.2f}s")
            print(f"  Total améliorations: {nb_ameliorations_total}")
            print(f"  Total acceptations: {nb_acceptances_total}")
            print(f"  Nombre de paliers: {palier}")
        
        return meilleure_solution, elapsed, nb_ameliorations_total, nb_acceptances_total


def executer_recuit_complet(filename, verbose=True):
    """
    Exécute le recuit simulé complet sur une instance
    
    Paramètres:
    - filename: chemin du fichier instance
    - verbose: afficher les détails
    
    Retourne:
    - solution: solution finale
    - metrics: dictionnaire avec métriques
    """
    
    print("="*60)
    print(f"RECUIT SIMULÉ COMPLET - VRPTW")
    print(f"Instance: {filename}")
    print("="*60)
    
    # 1. Lecture de l'instance
    print("\n[1] Lecture de l'instance...")
    data = read_instance(filename)
    print(f"    Clients: {data['n']-1} (dépôt inclus)")
    print(f"    Capacité des véhicules: {data['capacity']}")
    print(f"    Nombre max de véhicules: {data['nb_vehicles']}")
    
    # 2. Initialisation avec Solomon Randomisé
    print("\n[2] Initialisation avec Solomon Randomisé...")
    init = Initialisation(data)
    start_init = time.time()
    sol_init = init.solomon_randomise(p_urgents=0.3)
    time_init = time.time() - start_init
    
    if sol_init is None:
        print("    ERREUR: Aucune solution initiale trouvée!")
        return None, None
    
    print(f"    Coût initial: {sol_init.total_cost():.2f}")
    print(f"    Nb véhicules: {sol_init.nb_vehicles()}")
    print(f"    Distance: {sol_init.total_distance():.2f}")
    print(f"    Temps initialisation: {time_init:.2f}s")
    
    # 3. Configuration du recuit simulé
    print("\n[3] Lancement du recuit simulé...")
    operators = Operators(data)
    sa = SimulatedAnnealingFinal(data, operators)
    
    # Paramètres finaux
    T0 = 100.0
    T_fin = 5.0
    alpha_cool = 0.90
    iter_par_palier = 500
    
    print(f"    T0 = {T0}")
    print(f"    T_fin = {T_fin}")
    print(f"    α_cool = {alpha_cool}")
    print(f"    Itérations par palier = {iter_par_palier}")
    
    # 4. Exécution
    sol_final, time_sa, nb_amelio, nb_accept = sa.run(
        sol_init,
        alpha_cool=alpha_cool,
        iter_par_palier=iter_par_palier,
        T0=T0,
        T_fin=T_fin,
        verbose=verbose
    )
    
    # 5. Résultats finaux
    print("\n[4] Résultats finaux")
    print("-"*40)
    print(f"  Coût final: {sol_final.total_cost():.2f}")
    print(f"  Nb véhicules final: {sol_final.nb_vehicles()}")
    print(f"  Distance finale: {sol_final.total_distance():.2f}")
    print(f"  Faisabilité: {sol_final.is_feasible()}")
    print(f"  Temps total: {time_init + time_sa:.2f}s")
    print(f"    - Initialisation: {time_init:.2f}s")
    print(f"    - Recuit simulé: {time_sa:.2f}s")
    
    # Calcul de l'amélioration
    cost_init = sol_init.total_cost()
    cost_final = sol_final.total_cost()
    improvement = ((cost_init - cost_final) / cost_init) * 100
    print(f"\n  Amélioration: {improvement:.2f}%")
    
    # Affichage des routes
    print("\n[5] Détail des routes")
    print("-"*40)
    for i, route in enumerate(sol_final.routes):
        print(f"  Route {i+1}: {route}")
        dist = sol_final.route_distance(route)
        print(f"    Distance: {dist:.2f}, Clients: {len(route)-2}")
    
    metrics = {
        'instance': filename,
        'cost_initial': cost_init,
        'cost_final': cost_final,
        'improvement': improvement,
        'nb_vehicles_initial': sol_init.nb_vehicles(),
        'nb_vehicles_final': sol_final.nb_vehicles(),
        'distance_initial': sol_init.total_distance(),
        'distance_final': sol_final.total_distance(),
        'time_init': time_init,
        'time_sa': time_sa,
        'time_total': time_init + time_sa,
        'nb_ameliorations': nb_amelio,
        'nb_acceptations': nb_accept,
        'feasible': sol_final.is_feasible()
    }
    
    return sol_final, metrics


def afficher_metriques(metrics):
    """Affiche un résumé des métriques"""
    print("\n" + "="*60)
    print("RÉSUMÉ DES MÉTRIQUES")
    print("="*60)
    print(f"  Instance: {metrics['instance']}")
    print(f"  Coût initial: {metrics['cost_initial']:.2f}")
    print(f"  Coût final: {metrics['cost_final']:.2f}")
    print(f"  Amélioration: {metrics['improvement']:.2f}%")
    print(f"  Véhicules: {metrics['nb_vehicles_initial']} → {metrics['nb_vehicles_final']}")
    print(f"  Distance: {metrics['distance_initial']:.2f} → {metrics['distance_final']:.2f}")
    print(f"  Temps: {metrics['time_total']:.2f}s")
    print(f"  Améliorations acceptées: {metrics['nb_ameliorations']}")
    print(f"  Dégradations acceptées: {metrics['nb_acceptations']}")
    print(f"  Faisable: {metrics['feasible']}")


if __name__ == "__main__":
    # Choisir une instance à tester
    # Tu peux changer ici le nom du fichier
    instance_file = "instances/C101.txt"
    
    # Exécuter le recuit simulé complet
    solution, metriques = executer_recuit_complet(instance_file, verbose=True)
    
    if solution:
        afficher_metriques(metriques)
        
        # Option: sauvegarder la solution dans un fichier
        with open("results/solution_finale.txt", "w") as f:
            f.write(f"Instance: {metriques['instance']}\n")
            f.write(f"Coût final: {metriques['cost_final']:.2f}\n")
            f.write(f"Nb véhicules: {metriques['nb_vehicles_final']}\n")
            f.write(f"Distance: {metriques['distance_final']:.2f}\n")
            f.write(f"Temps: {metriques['time_total']:.2f}s\n\n")
            f.write("Routes:\n")
            for i, route in enumerate(solution.routes):
                f.write(f"Route {i+1}: {route}\n")
        print("\nSolution sauvegardée dans results/solution_finale.txt")