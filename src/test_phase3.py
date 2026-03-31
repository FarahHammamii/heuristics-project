import time
import pandas as pd
import random
import math
from instance_reader import read_instance
from initialisation import Initialisation
from operators import Operators


def test_phase3():
    """Test des valeurs de α_cool (uniquement relocate)"""
    
    test_instances = {
        'C1': 'C101',
        'R1': 'R101',
        'RC1': 'RC101'
    }
    
    alpha_values = [0.90, 0.95, 0.99]
    
    results = []
    
    for famille, instance_name in test_instances.items():
        print(f"\n{'='*50}")
        print(f"Test famille {famille} - Instance {instance_name}")
        print(f"{'='*50}")
        
        filename = f"instances/{instance_name}.txt"
        data = read_instance(filename)
        init = Initialisation(data)
        operators = Operators(data)
        
        # Solution initiale (Solomon)
        sol_init = init.solomon_randomise()
        
        if sol_init is None:
            print(f"  ERREUR: Pas de solution pour {famille}")
            continue
        
        print(f"  Coût initial: {sol_init.total_cost():.2f}")
        print(f"  Nb véhicules: {sol_init.nb_vehicles()}")
        print(f"  Distance: {sol_init.total_distance():.2f}")
        
        for alpha in alpha_values:
            print(f"\n  --- Test α = {alpha} ---")
            
            # PARAMÈTRES RAPIDES
            n = data['n']
            iter_par_palier = 500  # 500 itérations par palier (rapide)
            nb_paliers_max = 30     # 30 paliers max
            
            T0 = 100.0
            T = T0
            T_fin = 5.0  # Arrêter quand T < 5
            
            solution_courante = sol_init.copy()
            meilleure_solution = sol_init.copy()
            meilleur_coût = sol_init.total_cost()
            
            start = time.time()
            
            palier = 0
            nb_acceptances_total = 0
            nb_ameliorations_total = 0
            
            while T > T_fin and palier < nb_paliers_max:
                palier += 1
                nb_ameliorations_palier = 0
                nb_acceptances_palier = 0
                
                for _ in range(iter_par_palier):
                    # UNIQUEMENT RELOCATE
                    nouvelle = operators.relocate(solution_courante)
                    
                    # Vérifier si la solution a changé
                    if nouvelle.total_cost() == solution_courante.total_cost() and nouvelle.nb_vehicles() == solution_courante.nb_vehicles():
                        continue
                    
                    delta = nouvelle.total_cost() - solution_courante.total_cost()
                    
                    if delta < 0:
                        # Amélioration
                        solution_courante = nouvelle
                        nb_ameliorations_palier += 1
                        nb_ameliorations_total += 1
                        
                        if nouvelle.total_cost() < meilleur_coût:
                            meilleure_solution = nouvelle.copy()
                            meilleur_coût = nouvelle.total_cost()
                    else:
                        # Dégradation: accepter avec probabilité
                        if random.random() < math.exp(-delta / T):
                            solution_courante = nouvelle
                            nb_acceptances_palier += 1
                            nb_acceptances_total += 1
                
                # Refroidissement
                T *= alpha
                
                # Afficher progression
                print(f"    Palier {palier}: T={T:.2f}, coût={solution_courante.total_cost():.2f}, "
                      f"amelio={nb_ameliorations_palier}, accept={nb_acceptances_palier}")
            
            elapsed = time.time() - start
            
            print(f"\n  Résultat α={alpha}:")
            print(f"    Coût final: {meilleure_solution.total_cost():.2f}")
            print(f"    Nb véhicules: {meilleure_solution.nb_vehicles()}")
            print(f"    Distance: {meilleure_solution.total_distance():.2f}")
            print(f"    Temps: {elapsed:.2f}s")
            print(f"    Total améliorations: {nb_ameliorations_total}")
            print(f"    Total acceptations: {nb_acceptances_total}")
            
            results.append({
                'Famille': famille,
                'alpha': alpha,
                'Cost_final': meilleure_solution.total_cost(),
                'Nb_vehicles': meilleure_solution.nb_vehicles(),
                'Distance': meilleure_solution.total_distance(),
                'Temps_s': elapsed,
                'Nb_ameliorations': nb_ameliorations_total,
                'Nb_acceptations': nb_acceptances_total
            })
    
    df = pd.DataFrame(results)
    df.to_excel('results/phase3_results.xlsx', index=False)
    
    print("\n" + "="*50)
    print("RÉSULTATS PHASE 3")
    print("="*50)
    print(df.to_string())
    
    return df


if __name__ == "__main__":
    test_phase3()