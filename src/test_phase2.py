import math
import random
import time
import pandas as pd
from instance_reader import read_instance
from initialisation import Initialisation
from operators import Operators


def test_phase2():
    """Test des opérateurs un par un (T fixe)"""
    
    test_instances = {
        'C1': 'C101',
        'R1': 'R101',
        'RC1': 'RC101'
    }
    
    operators_list = ['relocate', 'or_opt_1', 'or_opt_2', 'or_opt_3', 'swap']
    
    results = []
    
    for famille, instance_name in test_instances.items():
        print(f"\n=== Test famille {famille} ===")
        
        filename = f"instances/{instance_name}.txt"
        data = read_instance(filename)
        init = Initialisation(data)
        operators = Operators(data)
        
        # ===== UTILISER SOLOMON RANDOMISÉ (toujours faisable) =====
        sol_init = init.solomon_randomise()
        
        # Vérifier que la solution est valide
        if sol_init is None:
            print(f"  ERREUR: Solomon n'a pas produit de solution pour {famille}")
            continue
        
        cost_init = sol_init.total_cost()
        
        print(f"  Coût initial: {cost_init:.2f}")
        print(f"  Nb véhicules: {sol_init.nb_vehicles()}")
        print(f"  Faisable: {sol_init.is_feasible()}")
        
        # T0 FIXE pour les tests
        T_fixe = 100.0
        print(f"  T fixe: {T_fixe}")
        
        for op_name in operators_list:
            print(f"  Test {op_name}...", end=" ", flush=True)
            
            nb_iterations = 5000
            sol_courante = sol_init.copy()
            
            start = time.time()
            nb_improvements = 0
            nb_acceptances = 0
            nb_no_change = 0
            
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
                
                # Vérifier si la solution a vraiment changé
                if nouvelle.total_cost() == sol_courante.total_cost() and nouvelle.nb_vehicles() == sol_courante.nb_vehicles():
                    nb_no_change += 1
                    continue
                
                delta = nouvelle.total_cost() - sol_courante.total_cost()
                
                if delta < 0:
                    sol_courante = nouvelle
                    nb_improvements += 1
                elif random.random() < math.exp(-delta / T_fixe):
                    sol_courante = nouvelle
                    nb_acceptances += 1
            
            elapsed = time.time() - start
            
            # Éviter division par zéro
            if cost_init > 0:
                improvement = ((cost_init - sol_courante.total_cost()) / cost_init) * 100
            else:
                improvement = 0
            
            print(f"amélioration={improvement:.2f}%, imp={nb_improvements}, acc={nb_acceptances}, no_change={nb_no_change}, temps={elapsed:.2f}s")
            
            results.append({
                'Famille': famille,
                'Operateur': op_name,
                'Amelioration_%': improvement,
                'Nb_Ameliorations': nb_improvements,
                'Nb_Acceptances': nb_acceptances,
                'Nb_Sans_Changement': nb_no_change,
                'Taux_Amelioration_%': (nb_improvements / nb_iterations) * 100 if nb_iterations > 0 else 0,
                'Temps_s': elapsed,
                'Efficacite': improvement / elapsed if elapsed > 0 else 0
            })
    
    df = pd.DataFrame(results)
    df.to_excel('results/phase2_results.xlsx', index=False)
    
    print("\n=== RÉSULTATS PHASE 2 ===")
    print(df.to_string())
    
    return df


if __name__ == "__main__":
    test_phase2()