import os
import time
import pandas as pd
from instance_reader import read_instance
from initialisation import Initialisation


# ==================== LOAD INSTANCES AUTOMATIQUEMENT ====================

def load_instances_from_folder(folder="instances"):
    instances = {}

    for file in os.listdir(folder):
        if not file.endswith(".txt"):
            continue

        name = file.replace(".txt", "")  # ex: R101

        # Déterminer la famille
        if name.startswith("RC"):
            famille = name[:3]   # RC1, RC2
        else:
            famille = name[:2]   # C1, R1, etc.

        if famille not in instances:
            instances[famille] = []

        instances[famille].append(name)

    # Trier les instances
    for famille in instances:
        instances[famille].sort()

    return instances


# ==================== TEST PHASE 1 ====================

def test_phase1():
    """Test des 3 méthodes d'initialisation"""

    # 🔥 Chargement dynamique
    instances = load_instances_from_folder("instances")

    results = []

    for famille, instances_list in instances.items():
        print(f"\n=== Test famille {famille} ===")

        for instance_name in instances_list:
            filename = f"instances/{instance_name}.txt"

            if not os.path.exists(filename):
                print(f"  {instance_name} non trouvé")
                continue

            print(f"  Instance {instance_name}...")
            data = read_instance(filename)
            init = Initialisation(data)

            # ==================== NN ====================
            start = time.time()
            sol_nn = init.nearest_neighbor_randomise()
            time_nn = time.time() - start

            cost_nn = sol_nn.total_cost() if sol_nn else float('inf')
            vehicles_nn = sol_nn.nb_vehicles() if sol_nn else 0
            feasible_nn = sol_nn.is_feasible() if sol_nn else False

            # ==================== SOLOMON ====================
            start = time.time()
            sol_sol = init.solomon_randomise()
            time_sol = time.time() - start

            cost_sol = sol_sol.total_cost() if sol_sol else float('inf')
            vehicles_sol = sol_sol.nb_vehicles() if sol_sol else 0
            feasible_sol = sol_sol.is_feasible() if sol_sol else False

            

            # ==================== STOCKAGE ====================
            results.append({
                'Famille': famille,
                'Instance': instance_name,

                'NN_Cost': cost_nn,
                'NN_Vehicles': vehicles_nn,
                'NN_Time': time_nn,
                'NN_Feasible': feasible_nn,

                'Solomon_Cost': cost_sol,
                'Solomon_Vehicles': vehicles_sol,
                'Solomon_Time': time_sol,
                'Solomon_Feasible': feasible_sol,

              
            })

    # ==================== DATAFRAME ====================
    df = pd.DataFrame(results)

    # ==================== SUMMARY ====================
    summary = []

    for famille in instances.keys():
        fam_df = df[df['Famille'] == famille]

        if fam_df.empty:
            continue

        # ===== BEST INSTANCES =====
        best_nn_idx = fam_df['NN_Cost'].idxmin()
        best_sol_idx = fam_df['Solomon_Cost'].idxmin()
        

        summary.append({
            'Famille': famille,

            # NN
            'NN_Cost_Avg': fam_df['NN_Cost'].mean(),
            'NN_Cost_Best': fam_df['NN_Cost'].min(),
            'NN_Best_Instance': fam_df.loc[best_nn_idx, 'Instance'],
            'NN_Vehicles_Avg': fam_df['NN_Vehicles'].mean(),

            # Solomon
            'Solomon_Cost_Avg': fam_df['Solomon_Cost'].mean(),
            'Solomon_Cost_Best': fam_df['Solomon_Cost'].min(),
            'Solomon_Best_Instance': fam_df.loc[best_sol_idx, 'Instance'],
            'Solomon_Vehicles_Avg': fam_df['Solomon_Vehicles'].mean(),

        })

    df_summary = pd.DataFrame(summary)

    # ==================== SAUVEGARDE ====================
    os.makedirs('results', exist_ok=True)

    df.to_excel('results/phase1_detailed.xlsx', index=False)
    df_summary.to_excel('results/phase1_summary.xlsx', index=False)

    # ==================== AFFICHAGE ====================
    print("\n=== RÉSULTATS PHASE 1 ===")
    print(df_summary.to_string(index=False))

    return df, df_summary