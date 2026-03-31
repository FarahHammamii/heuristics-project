import time
import pandas as pd
from instance_reader import read_instance
from initialisation import Initialisation
from operators import Operators
from simulated_annealing import SimulatedAnnealing

def test_phase4():
    """Test des différentes configurations"""
    
    test_instances = {
        'C1': 'C101',
        'R1': 'R101',
        'RC1': 'RC101'
    }
    
    configurations = [
        {'name': 'A (Simple)', 'auto_t0': False, 'adaptive_weights': False, 'route_merge': False},
        {'name': 'B (+poids)', 'auto_t0': False, 'adaptive_weights': True, 'route_merge': False},
        {'name': 'C (+merge)', 'auto_t0': False, 'adaptive_weights': True, 'route_merge': True},
        {'name': 'D (Complet)', 'auto_t0': True, 'adaptive_weights': True, 'route_merge': True}
    ]
    
    results = []
    
    for famille, instance_name in test_instances.items():
        print(f"\n=== Test famille {famille} ===")
        
        filename = f"instances/{instance_name}.txt"
        data = read_instance(filename)
        init = Initialisation(data)
        operators = Operators(data)
        
        # Solution initiale
        sol_init = init.solomon_randomise()
        
        for config in configurations:
            print(f"  Test {config['name']}...")
            
            sa = SimulatedAnnealing(data, operators)
            
            costs = []
            times = []
            vehicles = []
            
            # 5 runs pour robustesse
            for run in range(5):
                start = time.time()
                sol_final = sa.run(sol_init,
                                  alpha_cool=0.95,
                                  use_auto_t0=config['auto_t0'],
                                  use_adaptive_weights=config['adaptive_weights'],
                                  use_route_merge=config['route_merge'])
                elapsed = time.time() - start
                
                costs.append(sol_final.total_cost())
                times.append(elapsed)
                vehicles.append(sol_final.nb_vehicles())
            
            results.append({
                'Famille': famille,
                'Config': config['name'],
                'Cost_moyen': sum(costs)/len(costs),
                'Cost_meilleur': min(costs),
                'Nb_vehicles_moyen': sum(vehicles)/len(vehicles),
                'Temps_moyen_s': sum(times)/len(times),
                'Ecart_type': (sum((c - sum(costs)/len(costs))**2 for c in costs)/len(costs))**0.5
            })
    
    df = pd.DataFrame(results)
    df.to_excel('results/phase4_results.xlsx', index=False)
    
    print("\n=== RÉSULTATS PHASE 4 ===")
    print(df.to_string())
    
    return df