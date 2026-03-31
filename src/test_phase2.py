
import math
import random
import time
import pandas as pd
from instance_reader import read_instance
from initialisation import Initialisation
from operators import Operators
from simulated_annealing import SimulatedAnnealing


def test_phase2():
    """Test des opérateurs un par un (T fixe)"""
    
    # Choisir une instance représentative par famille
    test_instances = {
        'C1': 'C101',
        'R1': 'R101',
        'RC1': 'RC101'
    }
    
    # Opérateurs à tester
    operators_list = ['relocate', 'or_opt_1', 'or_opt_2', 'or_opt_3', 'swap']
    
    results = []
    
    for famille, instance_name in test_instances.items():
        print(f"\n=== Test famille {famille} ===")
        
        filename = f"instances/{instance_name}.txt"
        data = read_instance(filename)
        init = Initialisation(data)
        operators = Operators(data)
        
        # Solution initiale (Solomon)
        sol_init = init.solomon_randomise()
        cost_init = sol_init.total_cost()
        
        print(f"  Coût initial: {cost_init:.2f}")
        
        for op_name in operators_list:
            print(f"  Test {op_name}...")
            
            # Créer SA avec T fixe
            sa = SimulatedAnnealing(data, operators)
            T_fixe = sa.estimate_t0(sol_init)
            
            # Exécuter avec T fixe (pas de refroidissement)
            nb_iterations = 10000
            sol_courante = sol_init.copy()
            
            start = time.time()
            nb_improvements = 0
            
            for _ in range(nb_iterations):
                if op_name == 'relocate':
                    nouvelle = operators.relocate(sol_courante)
                elif op_name == 'or_opt_1':
                    nouvelle = operators.or_opt(sol_courante, 1)
                elif op_name == 'or_opt_2':
                    nouvelle = operators.or_opt(sol_courante, 2)
                elif op_name == 'or_opt_3':
                    nouvelle = operators.or_opt(sol_courante, 3)
                elif op_name == 'swap':
                    nouvelle = operators.swap(sol_courante)
                else:
                    continue
                
                delta = nouvelle.total_cost() - sol_courante.total_cost()
                
                if delta < 0:
                    sol_courante = nouvelle
                    nb_improvements += 1
                elif random.random() < math.exp(-delta / T_fixe):
                    sol_courante = nouvelle
            
            elapsed = time.time() - start
            
            improvement = ((cost_init - sol_courante.total_cost()) / cost_init) * 100
            
            results.append({
                'Famille': famille,
                'Operateur': op_name,
                'Amelioration_%': improvement,
                'Nb_Ameliorations': nb_improvements,
                'Taux_%': (nb_improvements / nb_iterations) * 100,
                'Temps_s': elapsed,
                'Efficacite': improvement / elapsed if elapsed > 0 else 0
            })
    
    df = pd.DataFrame(results)
    df.to_excel('results/phase2_results.xlsx', index=False)
    
    print("\n=== RÉSULTATS PHASE 2 ===")
    print(df.to_string())
    
    return df