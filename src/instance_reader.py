import math

def read_instance(filename):
    """Lit un fichier Solomon (VRPTW) et retourne les données structurées"""

    with open(filename, 'r') as f:
        lines = [line.strip() for line in f if line.strip()]

    # ==================== VEHICLE ====================
    nb_vehicles = None
    capacity = None

    for i, line in enumerate(lines):
        # Cherche la ligne "NUMBER CAPACITY"
        if 'NUMBER' in line and 'CAPACITY' in line:
            try:
                values = lines[i + 1].split()
                nb_vehicles = int(values[0])
                capacity = int(values[1])
            except (IndexError, ValueError):
                raise ValueError(f"Erreur lecture section VEHICLE dans {filename}")
            break

    if nb_vehicles is None or capacity is None:
        raise ValueError(f"Impossible de lire VEHICLE dans {filename}")

    # ==================== CUSTOMERS ====================
    customers = []
    customer_start = None

    for i, line in enumerate(lines):
        if 'CUST' in line and 'NO' in line:
            customer_start = i + 1
            break

    if customer_start is None:
        raise ValueError(f"Section clients introuvable dans {filename}")

    for i in range(customer_start, len(lines)):
        parts = lines[i].split()

        # Vérifie ligne valide
        if len(parts) < 7:
            continue

        try:
            cust_no = int(parts[0])
            x = float(parts[1])
            y = float(parts[2])
            demand = float(parts[3])
            ready_time = float(parts[4])
            due_date = float(parts[5])
            service_time = float(parts[6])
        except ValueError:
            continue  # ignore lignes corrompues

        customers.append({
            'id': cust_no,
            'x': x,
            'y': y,
            'demand': demand,
            'ready_time': ready_time,
            'due_date': due_date,
            'service_time': service_time
        })

    if not customers:
        raise ValueError(f"Aucun client lu dans {filename}")

    # ==================== DISTANCE MATRIX ====================
    n = len(customers)
    dist = [[0.0] * n for _ in range(n)]

    for i in range(n):
        for j in range(n):
            dx = customers[i]['x'] - customers[j]['x']
            dy = customers[i]['y'] - customers[j]['y']
            dist[i][j] = math.hypot(dx, dy)  # plus propre que sqrt(dx²+dy²)

    # ==================== RETURN ====================
    return {
        'nb_vehicles': nb_vehicles,
        'capacity': capacity,
        'customers': customers,
        'distance': dist,
        'n': n
    }