import math
import time

class InitialisationPolaireVRPTW:
    def __init__(self, fichier):
        self.fichier = fichier
        self.clients = []
        self.depot = None
        self.nb_vehicules_max = 0
        self.capacite = 0
        self.distance = []
        self.alpha = 1000
        self._charger_donnees()
        self._calculer_distances()
    
    def _charger_donnees(self):
        """Charge les données du fichier C101.txt"""
        with open(self.fichier, 'r') as f:
            lignes = f.readlines()
        
        i = 0
        while i < len(lignes):
            ligne = lignes[i].strip()
            if ligne.startswith('VEHICLE'):
                i += 2
                data = lignes[i].strip().split()
                self.nb_vehicules_max = int(data[0])
                self.capacite = int(data[1])
            elif ligne.startswith('CUSTOMER'):
                i += 3
                while i < len(lignes) and lignes[i].strip():
                    data = lignes[i].strip().split()
                    if len(data) >= 7:
                        client = {
                            'id': int(data[0]),
                            'x': float(data[1]),
                            'y': float(data[2]),
                            'demande': float(data[3]),
                            'debut': float(data[4]),
                            'fin': float(data[5]),
                            'service': float(data[6])
                        }
                        if client['id'] == 0:
                            self.depot = client
                        else:
                            self.clients.append(client)
                    i += 1
            i += 1
    
    def _calculer_distances(self):
        """Calcule la matrice des distances"""
        tous = [self.depot] + self.clients
        n = len(tous)
        self.distance = [[0.0] * n for _ in range(n)]
        
        for i in range(n):
            for j in range(n):
                if i != j:
                    dx = tous[i]['x'] - tous[j]['x']
                    dy = tous[i]['y'] - tous[j]['y']
                    self.distance[i][j] = math.sqrt(dx*dx + dy*dy)
    
    def verifier_route(self, route):
        if route[0] != 0 or route[-1] != 0:
            return False

        charge = 0
        temps = self.depot['debut']
        current = 0  # on commence au dépôt

        for client_id in route[1:-1]:

            client = self.clients[client_id - 1]

            # capacité
            charge += client['demande']
            if charge > self.capacite:
                return False

            # déplacement
            trajet = self.distance[current][client_id]
            arrivee = temps + trajet

            # fenêtre
            if arrivee > client['fin']:
                return False

            # attente si nécessaire
            arrivee = max(arrivee, client['debut'])

            # mise à jour temps
            temps = arrivee + client['service']
            current = client_id

        # retour dépôt
        retour = temps + self.distance[current][0]
        if retour > self.depot['fin']:
            return False

        return True
    
    def verifier_solution(self, solution):
        """Vérifie si une solution complète est réalisable"""
        visites = set()
        
        for route in solution:
            if not self.verifier_route(route):
                return False
            
            for c in route[1:-1]:
                if c == 0:  # Ignorer les dépôts
                    continue
                if c in visites:
                    return False
                visites.add(c)
        
        return len(visites) == len(self.clients)
    
    def calculer_distance_route(self, route):
        """Calcule la distance totale d'une route"""
        dist = 0.0
        for i in range(1, len(route)):
            if route[i-1] == route[i]:  # Éviter les distances nulles
                continue
            dist += self.distance[route[i-1]][route[i]]
        return dist
    
    def calculer_cout(self, solution):
        """Calcule le coût total d'une solution"""
        nb_vehicules = len(solution)
        distance_totale = sum(self.calculer_distance_route(r) for r in solution)
        return self.alpha * nb_vehicules + distance_totale
    
    def generer_solution_initiale(self):

        clients_restants = set(range(1, len(self.clients)+1))
        solution = []

        while clients_restants:

            # --- choisir seed = client le plus urgent ---
            seed = min(clients_restants,
                    key=lambda c: self.clients[c-1]['fin'])

            route = [0, seed, 0]
            clients_restants.remove(seed)

            # essayer d'insérer d'autres clients
            amelioration = True

            while amelioration:
                amelioration = False
                meilleur_client = None
                meilleure_position = None
                meilleur_delta = float('inf')

                for c in clients_restants:

                    for pos in range(1, len(route)):

                        nouvelle_route = route[:]
                        nouvelle_route.insert(pos, c)

                        if not self.verifier_route(nouvelle_route):
                            continue

                        ancien_cout = self.calculer_distance_route(route)
                        nouveau_cout = self.calculer_distance_route(nouvelle_route)
                        delta = nouveau_cout - ancien_cout

                        if delta < meilleur_delta:
                            meilleur_delta = delta
                            meilleur_client = c
                            meilleure_position = pos

                if meilleur_client is not None:
                    route.insert(meilleure_position, meilleur_client)
                    clients_restants.remove(meilleur_client)
                    amelioration = True

            solution.append(route)

        return solution
    
    def fusionner_routes(self, solution):
        """Fusionne des routes pour respecter le nombre max de véhicules"""
        while len(solution) > self.nb_vehicules_max:
            # Trouver deux routes à fusionner
            meilleure_fusion = None
            meilleur_gain = float('inf')
            
            for i in range(len(solution)):
                for j in range(i+1, len(solution)):
                    # Essayer de fusionner route i et j
                    fusion = solution[i][:-1] + solution[j][1:]
                    
                    if self.verifier_route(fusion):
                        gain = self.calculer_distance_route(fusion) - (
                            self.calculer_distance_route(solution[i]) + 
                            self.calculer_distance_route(solution[j])
                        )
                        if gain < meilleur_gain:
                            meilleur_gain = gain
                            meilleure_fusion = (i, j, fusion)
            
            if meilleure_fusion:
                i, j, fusion = meilleure_fusion
                # Remplacer les deux routes par la fusion
                solution = [solution[k] for k in range(len(solution)) if k not in [i, j]]
                solution.append(fusion)
            else:
                # Impossible de fusionner plus
                break
        
        return solution
    
    def afficher_resultats(self, solution):
        """Affiche la solution et ses caractéristiques"""
        print(f"\n{'='*60}")
        print(f"SOLUTION INITIALE PAR REGROUPEMENT POLAIRE")
        print(f"{'='*60}")
        print(f"Nombre de véhicules utilisés : {len(solution)} / {self.nb_vehicules_max}")
        
        distance_totale = 0
        for i, route in enumerate(solution):
            if len(route) <= 2:  # Route vide
                continue
            dist = self.calculer_distance_route(route)
            distance_totale += dist
            clients = [str(c) for c in route[1:-1] if c != 0]
            if clients:
                print(f"Route {i+1}: 0 → {' → '.join(clients)} → 0")
                print(f"         Distance: {dist:.2f}")
        
        cout = self.calculer_cout(solution)
        print(f"\nDistance totale: {distance_totale:.2f}")
        print(f"Coût total: {cout:.2f}")
        
        if self.verifier_solution(solution):
            print("✓ Solution réalisable")
        else:
            print("✗ Solution non réalisable")
            # Diagnostic
            self.diagnostiquer_solution(solution)
    
    def diagnostiquer_solution(self, solution):
        """Diagnostique pourquoi une solution n'est pas réalisable"""
        print("\nDiagnostic:")
        visites = set()
        for i, route in enumerate(solution):
            if not self.verifier_route(route):
                print(f"  Route {i+1} non réalisable")
            for c in route[1:-1]:
                if c != 0:
                    if c in visites:
                        print(f"  Client {c} visité multiple fois")
                    visites.add(c)
        
        if len(visites) != len(self.clients):
            print(f"  Clients manquants: {set(range(1,len(self.clients)+1)) - visites}")

# ==========================
# Exécution sur 3 instances
# ==========================
if __name__ == "__main__":

    import os

    print("\n" + "="*70)
    print("TEST GLOBAL DE L'HEURISTIQUE (TOUTES LES INSTANCES .txt)")
    print("="*70)

    # Récupérer tous les fichiers .txt du dossier courant
    fichiers = sorted([f for f in os.listdir(".") if f.endswith(".txt")])

    if not fichiers:
        print("Aucun fichier .txt trouvé dans le dossier.")
        exit()

    for fichier in fichiers:
        print("\n" + "-"*70)
        print(f"Instance : {fichier}")
        print("-"*70)

        try:
            init = InitialisationPolaireVRPTW(fichier)
            start = time.perf_counter()
            solution = init.generer_solution_initiale()
            end = time.perf_counter()
            duree_gluton = end - start

            nb_vehicules = len(solution)
            distance_totale = sum(init.calculer_distance_route(r) for r in solution)
            cout = init.calculer_cout(solution)
            faisable = init.verifier_solution(solution)

            print(f"Véhicules utilisés : {nb_vehicules} / {init.nb_vehicules_max}")
            print(f"Temps exécution : {duree_gluton:.4f} s")
            print(f"Distance totale    : {distance_totale:.2f}")
            print(f"Coût total         : {cout:.2f}")
            print(f"Solution réalisable: {faisable}")

   
            if not faisable:
                print("\n Instance NON réalisable détectée.")
                print("Arrêt immédiat des tests.")
                break

        except Exception as e:
            print(f"Erreur sur l'instance {fichier}: {e}")
            break

    else:
        print("\n✅ Toutes les instances sont réalisables.")