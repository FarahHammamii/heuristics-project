import time
import pandas as pd
from instance_reader import read_instance
from initialisation import Initialisation
from operators import Operators
from simulated_annealing import SimulatedAnnealing

def test_phase3():
    """Test des valeurs de α_cool"""
    
    test_instances = {
        'C1': 'C101',
        'R1': 'R101',
        'RC1': 'RC101'
    }
    
    alpha_values = [0.90, 0.95, 0.99]
    
    results = []
    
    for famille, instance_name in test_instances.items():
        print(f"\n=== Test famille {famille} ===")
        
        filename = f"instances/{instance_name}.txt"
        data = read_instance(filename)
        init = Initialisation(data)
        operators = Operators(data)
        
        # Solution initiale
        sol_init = init.solomon_randomise()
        
        for alpha in alpha_values:
            print(f"  Test α = {alpha}...")
            
            sa = SimulatedAnnealing(data, operators)
            
            start = time.time()
            sol_final = sa.run(sol_init, alpha_cool=alpha, 
                              use_adaptive_weights=False,
                              use_route_merge=False,
                              use_auto_t0=True)
            elapsed = time.time() - start
            
            results.append({
                'Famille': famille,
                'alpha': alpha,
                'Cost_final': sol_final.total_cost(),
                'Nb_vehicles': sol_final.nb_vehicles(),
                'Distance': sol_final.total_distance(),
                'Temps_s': elapsed
            })
    
    df = pd.DataFrame(results)
    df.to_excel('results/phase3_results.xlsx', index=False)
    
    print("\n=== RÉSULTATS PHASE 3 ===")
    print(df.to_string())
    
    return df