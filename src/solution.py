import copy

class Solution:
    """Représente une solution VRPTW"""
    
    def __init__(self, routes=None, data=None):
        self.routes = routes if routes else []
        self.data = data
        self._cost = None
        self._distance = None
    
    def copy(self):
        return Solution(copy.deepcopy(self.routes), self.data)
    
    def total_distance(self):
        if self._distance is None:
            self._distance = 0
            for route in self.routes:
                self._distance += self.route_distance(route)
        return self._distance
    
    def route_distance(self, route):
        d = 0
        for i in range(len(route)-1):
            d += self.data['distance'][route[i]][route[i+1]]
        return d
    
    def total_cost(self, alpha=1000):
        """Coût total avec pénalité"""
        return alpha * len(self.routes) + self.total_distance()
    
    def nb_vehicles(self):
        return len(self.routes)
    
    def is_feasible(self):
        """Vérifie si la solution est faisable"""
        for route in self.routes:
            if not self.is_route_feasible(route):
                return False
        return True
    
    def is_route_feasible(self, route):
        """Vérifie la faisabilité d'une route"""
        if len(route) < 2:
            return False
        if route[0] != 0 or route[-1] != 0:
            return False
        
        capacity = 0
        time = self.data['customers'][0]['ready_time']  # début dépôt
        
        for i in range(1, len(route)):
            curr = route[i]
            prev = route[i-1]
            
            # Capacité
            capacity += self.data['customers'][curr]['demand']
            if capacity > self.data['capacity']:
                return False
            
            # Temps de trajet
            travel = self.data['distance'][prev][curr]
            time += travel
            
            # Fenêtre de temps
            ready = self.data['customers'][curr]['ready_time']
            due = self.data['customers'][curr]['due_date']
            
            if time > due:
                return False
            
            if time < ready:
                time = ready
            
            # Temps de service
            time += self.data['customers'][curr]['service_time']
        
        # Retour au dépôt
        travel_back = self.data['distance'][route[-2]][0]
        time += travel_back
        
        depot_due = self.data['customers'][0]['due_date']
        if time > depot_due:
            return False
        
        return True