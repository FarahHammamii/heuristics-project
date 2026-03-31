import time
import pandas as pd
import random
import math
from instance_reader import read_instance
from initialisation import Initialisation
from operators import Operators
from simulated_annealing import SimulatedAnnealing


def test_phase4():
    """Test des configurations avec et sans fusion (uniquement relocate)"""
    
    test_instances = {
        'C1': 'C101',
        'R1': 'R101',
        'RC1': 'RC101'
    }
    
    # Configurations à tester (α=0.90, pas de poids adaptatifs)
    configurations = [
        {'name': 'A (Sans fusion)', 'use_route_merge': False},
        {'name': 'B (Avec fusion)', 'use_route_merge': True},
    ]
    
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
        
        for config in configurations:
            print(f"\n  --- Test {config['name']} ---")
            
            costs = []
            times = []
            vehicles = []
            
            # 3 runs pour robustesse
            for run in range(3):
                print(f"    Run {run+1}/3...", end=" ", flush=True)
                
                # Paramètres
                n = data['n']
                iter_par_palier = 500  # 500 itérations par palier
                alpha_cool = 0.90      # Meilleur trouvé en Phase 3
                
                sa = SimulatedAnnealing(data, operators)
                
                start = time.time()
                sol_final = sa.run(sol_init,
                                  alpha_cool=alpha_cool,
                                  iter_par_palier=iter_par_palier,
                                  use_auto_t0=False,      # T0 fixe = 100
                                  use_route_merge=config['use_route_merge'])
                elapsed = time.time() - start
                
                print(f"terminé en {elapsed:.2f}s, coût={sol_final.total_cost():.2f}")
                
                costs.append(sol_final.total_cost())
                times.append(elapsed)
                vehicles.append(sol_final.nb_vehicles())
            
            # Calculer les moyennes
            avg_cost = sum(costs) / len(costs)
            best_cost = min(costs)
            avg_vehicles = sum(vehicles) / len(vehicles)
            avg_time = sum(times) / len(times)
            
            # Calculer écart-type
            variance = sum((c - avg_cost) ** 2 for c in costs) / len(costs)
            std_dev = variance ** 0.5
            
            print(f"\n    Résultats {config['name']}:")
            print(f"      Coût moyen: {avg_cost:.2f}")
            print(f"      Coût meilleur: {best_cost:.2f}")
            print(f"      Nb véhicules moyen: {avg_vehicles:.1f}")
            print(f"      Temps moyen: {avg_time:.2f}s")
            
            results.append({
                'Famille': famille,
                'Config': config['name'],
                'Cost_moyen': avg_cost,
                'Cost_meilleur': best_cost,
                'Nb_vehicles_moyen': avg_vehicles,
                'Temps_moyen_s': avg_time,
                'Ecart_type': std_dev
            })
    
    df = pd.DataFrame(results)
    df.to_excel('results/phase4_results.xlsx', index=False)
    
    print("\n" + "="*50)
    print("RÉSULTATS PHASE 4")
    print("="*50)
    print(df.to_string())
    
    return df


if __name__ == "__main__":
    test_phase4()