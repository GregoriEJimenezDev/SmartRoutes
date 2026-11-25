"""SmartRoutes: consola de gestión de rutas no dirigidas."""
from __future__ import annotations
import os, shutil
from dataclasses import dataclass
from enum import Enum
from collections import deque
import heapq

class InvalidLocationError(ValueError): pass
class DuplicateEdgeError(ValueError): pass
class InactiveNodeError(ValueError): pass
class EdgeNotFoundError(ValueError): pass

class LocationState(Enum):
    ACTIVE = "Activo"
    INACTIVE = "Inactivo"

@dataclass(frozen=True)
class Location:
    id: int
    name: str
    state: LocationState = LocationState.ACTIVE

@dataclass(frozen=True)
class Edge:
    origin: int
    destination: int
    weight: float

class LocationFactory:
    """Crea identificadores secuenciales que no se reutilizan."""
    def __init__(self, first_id: int = 1): self._next_id = first_id
    def create(self, name: str) -> Location:
        """Time Complexity: O(1)."""
        name = str(name).strip()
        if not name: raise InvalidLocationError("El nombre no puede estar vacío.")
        loc = Location(self._next_id, name)
        self._next_id += 1
        return loc

class EdgeFactory:
    """Valida y construye rutas."""
    def create(self, origin: int, destination: int, weight: object) -> Edge:
        """Time Complexity: O(1)."""
        try: value = float(str(weight).strip())
        except (TypeError, ValueError): raise ValueError("El peso debe ser numérico.")
        if origin == destination: raise ValueError("No se permiten rutas hacia la misma ubicación.")
        if value <= 0: raise ValueError("El peso debe ser mayor que cero.")
        return Edge(origin, destination, value)

class Graph:
    """Fuente de verdad del grafo no dirigido."""
    def __init__(self):
        self.locations: dict[int, Location] = {}
        self.graph: dict[int, list[tuple[int, float]]] = {}
    def add_location(self, location: Location) -> None:
        """Time Complexity: O(1)."""
        if location.id in self.locations: raise InvalidLocationError("ID duplicado.")
        if location.state == LocationState.ACTIVE and any(x.name.casefold()==location.name.casefold() and x.state==LocationState.ACTIVE for x in self.locations.values()): raise InvalidLocationError("Ya existe una ubicación activa con ese nombre.")
        self.locations[location.id]=location; self.graph[location.id]=[]
    def edit_location(self, loc_id: int, name: str) -> None:
        """Time Complexity: O(V)."""
        old=self.get_location(loc_id); name=name.strip()
        if not name: raise InvalidLocationError("El nombre no puede estar vacío.")
        if old.state==LocationState.ACTIVE and any(x.id!=loc_id and x.state==LocationState.ACTIVE and x.name.casefold()==name.casefold() for x in self.locations.values()): raise InvalidLocationError("Nombre activo duplicado.")
        self.locations[loc_id]=Location(loc_id,name,old.state)
    def get_location(self, loc_id: int) -> Location:
        """Time Complexity: O(1)."""
        if loc_id not in self.locations: raise InvalidLocationError(f"No existe la ubicación {loc_id}.")
        return self.locations[loc_id]
    def get_locations(self) -> tuple[Location,...]:
        """Time Complexity: O(V log V)."""
        return tuple(self.locations[k] for k in sorted(self.locations))
    def get_neighbors(self, loc_id: int) -> tuple[tuple[int,float],...]:
        """Time Complexity: O(deg(V))."""
        self.get_location(loc_id); return tuple(self.graph[loc_id])
    def has_edge(self,a:int,b:int)->bool:
        """Time Complexity: O(deg(a))."""
        return any(n==b for n,_ in self.get_neighbors(a))
    def add_edge(self, edge: Edge) -> None:
        """Time Complexity: O(V + deg(a))."""
        a,b,w=edge.origin,edge.destination,edge.weight
        for x in (a,b):
            loc=self.get_location(x)
            if loc.state!=LocationState.ACTIVE: raise InactiveNodeError(f"La ubicación {x} está inactiva.")
        if a==b or w<=0: raise ValueError("Ruta inválida: se requiere origen y destino distintos y peso positivo.")
        if self.has_edge(a,b): raise DuplicateEdgeError("La ruta ya existe (A-B equivale a B-A).")
        self.graph[a].append((b,w)); self.graph[b].append((a,w))
    def update_edge(self,a:int,b:int,w:float)->None:
        """Time Complexity: O(deg(a) + deg(b))."""
        self.get_location(a); self.get_location(b)
        if w<=0: raise ValueError("El peso debe ser positivo.")
        if not self.has_edge(a,b): raise EdgeNotFoundError("La ruta no existe.")
        self.graph[a]=[(n,w if n==b else x) for n,x in self.graph[a]]; self.graph[b]=[(n,w if n==a else x) for n,x in self.graph[b]]
    def remove_edge(self,a:int,b:int)->None:
        """Time Complexity: O(deg(a) + deg(b))."""
        self.get_location(a); self.get_location(b)
        if not self.has_edge(a,b): raise EdgeNotFoundError("La ruta no existe.")
        self.graph[a]=[(n,w) for n,w in self.graph[a] if n!=b]; self.graph[b]=[(n,w) for n,w in self.graph[b] if n!=a]
    def inactivate_location(self,loc_id:int)->None:
        """Time Complexity: O(deg(V))."""
        loc=self.get_location(loc_id)
        if self.graph[loc_id]: raise InactiveNodeError("Elimine primero las rutas conectadas a esta ubicación.")
        self.locations[loc_id]=Location(loc.id,loc.name,LocationState.INACTIVE)
    def activate_location(self,loc_id:int)->None:
        """Time Complexity: O(V)."""
        loc=self.get_location(loc_id)
        if any(x.id!=loc_id and x.state==LocationState.ACTIVE and x.name.casefold()==loc.name.casefold() for x in self.locations.values()): raise InvalidLocationError("El nombre ya pertenece a otra ubicación activa.")
        self.locations[loc_id]=Location(loc.id,loc.name,LocationState.ACTIVE)

class GraphAlgorithms:
    """Recorridos y cálculos del grafo sin interacción de consola."""
    def __init__(self, graph: Graph): self.graph=graph
    def _active(self, i:int)->bool: return self.graph.get_location(i).state==LocationState.ACTIVE
    def bfs(self,start:int)->list[int]:
        """Time Complexity: O(V + E)."""
        if not self._active(start): raise InvalidLocationError("El inicio no está activo.")
        seen={start}; q=deque([start]); out=[]
        while q:
            v=q.popleft(); out.append(v)
            for n,_ in self.graph.get_neighbors(v):
                if n not in seen and self._active(n): seen.add(n); q.append(n)
        return out
    def dfs(self,start:int)->list[int]:
        """Time Complexity: O(V + E)."""
        if not self._active(start): raise InvalidLocationError("El inicio no está activo.")
        seen=set(); stack=[start]; out=[]
        while stack:
            v=stack.pop()
            if v in seen: continue
            seen.add(v); out.append(v)
            stack.extend(n for n,_ in reversed(self.graph.get_neighbors(v)) if n not in seen and self._active(n))
        return out
    def dijkstra(self,start:int,end:int)->tuple[list[int],float]:
        """Time Complexity: O((V + E) log V)."""
        if not self._active(start) or not self._active(end): raise InvalidLocationError("Origen y destino deben estar activos.")
        dist={start:0.0}; prev={}; heap=[(0.0,start)]
        while heap:
            cost,v=heapq.heappop(heap)
            if cost!=dist.get(v): continue
            if v==end: break
            for n,w in self.graph.get_neighbors(v):
                if self._active(n) and cost+w<dist.get(n,float('inf')): dist[n]=cost+w; prev[n]=v; heapq.heappush(heap,(cost+w,n))
        if end not in dist: return [],float('inf')
        path=[end]
        while path[-1]!=start: path.append(prev[path[-1]])
        return list(reversed(path)),dist[end]
    def connected(self,a:int,b:int)->bool:
        """Time Complexity: O(V + E)."""
        self.graph.get_location(a); self.graph.get_location(b)
        if not self._active(a) or not self._active(b): return False
        return b in self.bfs(a)
    def connected_components(self)->list[list[int]]:
        """Time Complexity: O(V + E)."""
        unseen={x.id for x in self.graph.get_locations() if x.state==LocationState.ACTIVE}; comps=[]
        while unseen:
            start=min(unseen); comp=self.bfs(start); comps.append(comp); unseen.difference_update(comp)
        return comps
    def metrics(self)->dict:
        """Time Complexity: O(V + E)."""
        active=[x for x in self.graph.get_locations() if x.state==LocationState.ACTIVE]; deg={x.id:sum(self._active(n) for n,_ in self.graph.get_neighbors(x.id)) for x in active}; edges=sum(deg.values())//2
        return {'total_nodes':len(self.graph.locations),'total_edges':edges,'components':len(self.connected_components()),'active_nodes':len(active),'inactive_nodes':len(self.graph.locations)-len(active),'isolated_nodes':sum(v==0 for v in deg.values()),'max_degree_node':max(deg,key=deg.get) if deg else None,'min_degree_node':min(deg,key=deg.get) if deg else None,'max_degree':max(deg.values(),default=0),'min_degree':min(deg.values(),default=0),'avg_degree':2*edges/len(active) if active else 0.0,'empty':not active}

class GraphBuilder:
    """Builder fluido para datos demostrativos."""
    def __init__(self): self.graph=Graph(); self.lf=LocationFactory(); self.ef=EdgeFactory()
    def add_location(self,name:str)->'GraphBuilder':
        """Time Complexity: O(V)."""
        self.graph.add_location(self.lf.create(name)); return self
    def add_edge(self,a:int,b:int,w:float)->'GraphBuilder':
        """Time Complexity: O(deg(a) + V)."""
        self.graph.add_edge(self.ef.create(a,b,w)); return self
    def build(self)->Graph:
        """Time Complexity: O(1)."""
        return self.graph

class Screen:
    """Único componente autorizado a interactuar con la terminal."""
    @staticmethod
    def width()->int:
        """Time Complexity: O(1)."""
        return shutil.get_terminal_size((80,24)).columns
    @classmethod
    def center(cls,text:str)->str:
        """Time Complexity: O(n)."""
        width=cls.width(); return '\n'.join(line.center(width) for line in str(text).splitlines())
    @classmethod
    def print_centered(cls,text:str)->None:
        """Time Complexity: O(n)."""
        print(cls.center(text))
    @classmethod
    def print_block(cls,lines)->None:
        """Time Complexity: O(n)."""
        rows=list(lines); w=max((len(str(x)) for x in rows),default=0); cls.print_centered('\n'.join(str(x).center(w) for x in rows))
    @classmethod
    def input_centered(cls,prompt:str)->str:
        """Time Complexity: O(n)."""
        pad=max(0,(cls.width()-len(prompt))//2); return input(' '*pad+prompt)
    @classmethod
    def clear(cls)->None:
        """Time Complexity: O(1)."""
        os.system('cls' if os.name=='nt' else 'clear')
    @classmethod
    def pause(cls)->None:
        """Time Complexity: O(1)."""
        cls.input_centered('Presione ENTER para continuar...')

def demo()->Graph:
    """Construye dos componentes y una ubicación aislada."""
    return (GraphBuilder().add_location('Santo Domingo').add_location('Santiago').add_location('San Pedro').add_location('La Vega').add_location('Barahona').add_location('Azua').add_location('Puerto Plata').add_location('Higüey').add_location('Bonao')
      .add_edge(1,2,155).add_edge(1,3,70).add_edge(2,4,125).add_edge(5,6,95).add_edge(6,8,140).build())

class ConsoleUI:
    """Interacción de consola; recibe dependencias por inyección."""
    def __init__(self,graph:Graph,algorithms:GraphAlgorithms): self.graph=graph; self.alg=algorithms; self.lf=LocationFactory(max(graph.locations, default=0)+1); self.ef=EdgeFactory()
    def ask_id(self,label:str)->int:
        """Time Complexity: O(1)."""
        while True:
            try: return int(Screen.input_centered(label))
            except ValueError: Screen.print_centered('Ingrese un ID entero válido.')
    def run(self)->None:
        """Time Complexity: O(1) por iteración de menú."""
        actions={'1':self.locations_menu,'2':self.routes_menu,'3':self.show_graph,'4':lambda:self.traverse('BFS',self.alg.bfs),'5':lambda:self.traverse('DFS',self.alg.dfs),'6':self.shortest,'7':self.connectivity,'8':self.components,'9':self.metrics,'10':self.status}
        while True:
            Screen.clear(); Screen.print_block(['═'*54,'                 SMARTROUTES','═'*54,'1) Mantenimiento de ubicaciones','2) Mantenimiento de rutas','3) Mostrar grafo','4) BFS: rutas disponibles','5) DFS: exploración','6) Dijkstra: ruta óptima','7) Verificar conectividad','8) Componentes conectados','9) Generar métricas','10) Ver estado del sistema','11) Salir','─'*54])
            choice=Screen.input_centered('Seleccione una opción: ').strip()
            if choice=='11': Screen.print_centered('Hasta pronto.'); return
            try:
                if choice in actions: actions[choice]()
                else: Screen.print_centered('Opción inválida.')
            except (ValueError,KeyError) as e: Screen.print_centered(f'Error: {e}')
            Screen.pause()
    def locations_menu(self)->None:
        """Time Complexity: O(V) en las operaciones de listado y búsqueda."""
        menu={'1':'Crear','2':'Buscar','3':'Editar','4':'Inactivar','5':'Activar','6':'Listar','7':'Volver'}
        while True:
            Screen.print_block(['UBICACIONES']+[f'{k}) {v}' for k,v in menu.items()]); c=Screen.input_centered('Opción: ').strip()
            if c=='7': return
            if c=='1': self.graph.add_location(self.lf.create(Screen.input_centered('Nombre: ')))
            elif c=='2': Screen.print_centered(str(self.graph.get_location(self.ask_id('ID: '))))
            elif c=='3': self.graph.edit_location(self.ask_id('ID: '),Screen.input_centered('Nuevo nombre: '))
            elif c=='4': self.graph.inactivate_location(self.ask_id('ID: '))
            elif c=='5': self.graph.activate_location(self.ask_id('ID: '))
            elif c=='6': Screen.print_block([f'{x.id} - {x.name} ({x.state.value})' for x in self.graph.get_locations()])
            else: Screen.print_centered('Opción inválida.')
    def routes_menu(self)->None:
        """Time Complexity: O(V + E) para el listado."""
        while True:
            Screen.print_block(['RUTAS','1) Crear','2) Buscar','3) Editar','4) Eliminar','5) Listar','6) Volver']); c=Screen.input_centered('Opción: ').strip()
            if c=='6': return
            if c in ('1','2','3','4'):
                a=self.ask_id('Origen: '); b=self.ask_id('Destino: ')
                if c=='1': self.graph.add_edge(self.ef.create(a,b,Screen.input_centered('Peso: ')))
                elif c=='2':
                    if not self.graph.has_edge(a,b): raise EdgeNotFoundError('La ruta no existe.')
                    Screen.print_centered(str(next(w for n,w in self.graph.get_neighbors(a) if n==b)))
                elif c=='3': self.graph.update_edge(a,b,float(Screen.input_centered('Nuevo peso: ')))
                else: self.graph.remove_edge(a,b)
            elif c=='5': Screen.print_block([f'{x.id} ↔ {n} ({w:g})' for x in self.graph.get_locations() for n,w in self.graph.get_neighbors(x.id) if x.id<n])
            else: Screen.print_centered('Opción inválida.')
    def show_graph(self)->None:
        """Time Complexity: O(V + E)."""
        rows=[]
        for x in self.graph.get_locations():
            rows.append(f'{x.id} - {x.name} ->')
            rows.extend(f'    vecino: {n} - {self.graph.get_location(n).name} ({w:g})' for n,w in self.graph.get_neighbors(x.id))
        Screen.print_block(rows or ['(grafo vacío)'])
    def traverse(self,label,fn)->None:
        """Time Complexity: O(V + E)."""
        start=self.ask_id('Ubicación inicial: '); Screen.print_centered(f'{label}: '+', '.join(f'{i} - {self.graph.get_location(i).name}' for i in fn(start)))
    def shortest(self)->None:
        """Time Complexity: O((V + E) log V)."""
        a=self.ask_id('Origen: '); b=self.ask_id('Destino: '); path,cost=self.alg.dijkstra(a,b)
        Screen.print_centered('The destination is not reachable from the origin.' if not path else f"{' → '.join(self.graph.get_location(i).name for i in path)} | costo: {cost:g}")
    def connectivity(self)->None:
        """Time Complexity: O(V + E)."""
        yes=self.alg.connected(self.ask_id('Origen: '),self.ask_id('Destino: ')); Screen.print_centered('Yes, a path exists between the selected locations.' if yes else 'No, the selected locations are not connected.')
    def components(self)->None:
        """Time Complexity: O(V + E)."""
        comps=self.alg.connected_components()
        msg=['The graph is empty. No components found.'] if not comps else ['The graph is fully connected. All locations belong to a single component.'] if len(comps)==1 else ['Connected Components:']+[f'{i}. '+', '.join(self.graph.get_location(v).name for v in c) for i,c in enumerate(comps,1)]
        Screen.print_block(msg)
    def metrics(self)->None:
        """Time Complexity: O(V + E)."""
        self._report(self.alg.metrics())
    def status(self)->None:
        """Time Complexity: O(V + E)."""
        self._report(self.alg.metrics())
    def _report(self,data:dict)->None:
        """Time Complexity: O(n)."""
        Screen.print_block([f'{k}: {v}' for k,v in data.items()])

def main()->None:
    """Time Complexity: O(1) para inicializar la aplicación."""
    graph=demo(); ConsoleUI(graph,GraphAlgorithms(graph)).run()

if __name__=='__main__': main()
