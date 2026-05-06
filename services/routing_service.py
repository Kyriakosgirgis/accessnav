import math
import threading
import requests
import networkx as nx
from kivy.clock import Clock


# ------------------------------------------------------------------ #
#  Accessibility edge weights                                          #
# ------------------------------------------------------------------ #

WEIGHT = {
    "surface": {
        "asphalt":        1.0,
        "paved":          1.0,
        "concrete":       1.0,
        "paving_stones":  1.2,
        "sett":           1.4,
        "cobblestone":    2.0,
        "gravel":         2.5,
        "unpaved":        2.5,
        "grass":          3.0,
        "dirt":           3.0,
        "sand":           4.0,
    },
    "highway": {
        "footway":        1.0,
        "pedestrian":     1.0,
        "path":           1.2,
        "living_street":  1.2,
        "residential":    1.3,
        "service":        1.4,
        "tertiary":       1.5,
        "secondary":      1.7,
        "primary":        2.0,
        "steps":          9.0,
        "cycleway":       1.3,
    },
    "wheelchair": {
        "yes":        0.8,
        "designated": 0.8,
        "limited":    1.5,
        "no":         8.0,
    },
    "incline_threshold_pct": 6,
    "incline_penalty":       2.0,
}

BLOCKED_BARRIERS = {"bollard", "gate", "fence", "wall", "block"}
OVERPASS_URL     = "https://overpass-api.de/api/interpreter"
USER_AGENT       = "AccessNav/1.0 (accessible routing)"


# ------------------------------------------------------------------ #
#  RoutingService                                                      #
# ------------------------------------------------------------------ #

class RoutingService:
    """
    Builds an accessibility-weighted directed graph from OSM walkway
    data and exposes A* pathfinding for wheelchair-friendly routing.

    Usage:
        svc = RoutingService()
        svc.build_graph(
            lat=34.7071, lon=33.0226, radius=800,
            on_ready=lambda: svc.find_route(origin, dest, on_route=...),
            on_error=lambda msg: print(msg),
        )
    """

    def __init__(self):
        self.graph    = None
        self._cancel  = False
        self._session = requests.Session()

    # ------------------------------------------------------------------ #
    #  Public API                                                          #
    # ------------------------------------------------------------------ #

    def build_graph(self, lat, lon, radius=800,
                    on_ready=None, on_error=None):
        """
        Fetch OSM walkway data around (lat, lon) within radius metres
        and build the routing graph on a background thread.

        on_ready()        — called on the main thread when graph is built
        on_error(message) — called on the main thread if fetch fails
        """
        self._cancel = False
        threading.Thread(
            target=self._fetch_and_build,
            args=(lat, lon, radius, on_ready, on_error),
            daemon=True,
        ).start()

    def find_route(self, origin, destination,
                   on_route=None, on_error=None):
        """
        Find the most accessible route from origin to destination.

        origin/destination : (lat, lon) tuples
        on_route(result)   : called with a result dict on the main thread
        on_error(message)  : called if no route found
        """
        if self.graph is None:
            self._deliver_error(on_error, "Graph not built yet.")
            return

        threading.Thread(
            target=self._run_astar,
            args=(origin, destination, on_route, on_error),
            daemon=True,
        ).start()

    def cancel(self):
        self._cancel = True

    # ------------------------------------------------------------------ #
    #  Graph building                                                      #
    # ------------------------------------------------------------------ #

    def _fetch_and_build(self, lat, lon, radius, on_ready, on_error):
        try:
            print(f"[RoutingService] Fetching OSM data — "
                  f"centre: {lat},{lon} radius: {radius}m")

            elements = self._fetch_osm(lat, lon, radius)

            if self._cancel:
                return

            print(f"[RoutingService] Received {len(elements)} elements")

            self.graph = self._build_graph(elements)

            print(f"[RoutingService] Graph ready — "
                  f"{self.graph.number_of_nodes()} nodes, "
                  f"{self.graph.number_of_edges()} edges")

            if on_ready and not self._cancel:
                Clock.schedule_once(lambda dt: on_ready(), 0)

        except requests.exceptions.ConnectionError:
            self._deliver_error(on_error, "No internet connection.")
        except requests.exceptions.Timeout:
            self._deliver_error(on_error, "OSM request timed out.")
        except Exception as e:
            self._deliver_error(on_error, f"Graph build error: {e}")

    def _fetch_osm(self, lat, lon, radius):
        """Fetch all walkable ways and their nodes from Overpass."""
        query = f"""
[out:json][timeout:30];
(
  way["highway"~"^(footway|pedestrian|path|steps|living_street|residential|service|tertiary|secondary|primary|cycleway)$"]
     (around:{radius},{lat},{lon});
  way["foot"!="no"]
     (around:{radius},{lat},{lon});
);
out body;
>;
out skel qt;
"""
        response = self._session.post(
            OVERPASS_URL,
            data={"data": query},
            headers={"User-Agent": USER_AGENT},
            timeout=30,
        )
        response.raise_for_status()
        return response.json().get("elements", [])

    def _build_graph(self, elements):
        """
        Convert raw OSM elements into a weighted directed graph.

        Nodes  : OSM node IDs stored with lat/lon attributes
        Edges  : consecutive node pairs in each way
        Weight : accessibility cost (lower = more accessible)
        """
        G     = nx.DiGraph()
        nodes = {}
        ways  = []

        # ── Pass 1 — collect nodes ─────────────────────────── #
        for el in elements:
            if el["type"] == "node":
                nodes[el["id"]] = {
                    "lat": el["lat"],
                    "lon": el["lon"],
                }

        # ── Pass 2 — collect ways ──────────────────────────── #
        for el in elements:
            if el["type"] != "way":
                continue
            tags     = el.get("tags", {})
            node_ids = el.get("nodes", [])
            if len(node_ids) < 2:
                continue
            ways.append({"tags": tags, "nodes": node_ids})

        # ── Pass 3 — add graph nodes ───────────────────────── #
        for nid, attrs in nodes.items():
            G.add_node(nid, lat=attrs["lat"], lon=attrs["lon"])

        # ── Pass 4 — add edges ─────────────────────────────── #
        for way in ways:
            tags     = way["tags"]
            node_ids = way["nodes"]
            weight   = self._edge_weight(tags)

            for i in range(len(node_ids) - 1):
                u = node_ids[i]
                v = node_ids[i + 1]

                if u not in nodes or v not in nodes:
                    continue

                dist = haversine(
                    nodes[u]["lat"], nodes[u]["lon"],
                    nodes[v]["lat"], nodes[v]["lon"],
                )

                cost   = dist * weight
                oneway = tags.get("oneway") == "yes"

                G.add_edge(u, v, weight=cost, distance=dist,
                           accessibility=weight)
                if not oneway:
                    G.add_edge(v, u, weight=cost, distance=dist,
                               accessibility=weight)

        # ── Pass 5 — keep only the largest connected component #
        # Removes isolated path fragments that cause "no path"  #
        # errors for valid origin/destination pairs.             #
        if G.number_of_nodes() == 0:
            return G

        largest     = max(nx.weakly_connected_components(G), key=len)
        pruned      = G.subgraph(largest).copy()
        removed     = G.number_of_nodes() - pruned.number_of_nodes()

        print(f"[RoutingService] Largest component: "
              f"{pruned.number_of_nodes()} nodes, "
              f"{pruned.number_of_edges()} edges "
              f"(removed {removed} isolated nodes)")

        return pruned

    def _edge_weight(self, tags):
        """
        Compute an accessibility multiplier for an OSM way.
        1.0 = perfectly accessible, higher = less accessible.
        """
        w = 1.0

        highway = tags.get("highway", "footway")
        w *= WEIGHT["highway"].get(highway, 1.5)

        # Steps are so heavily penalised no further factors apply
        if highway == "steps":
            return w

        # Surface quality
        surface = tags.get("surface", "")
        w *= WEIGHT["surface"].get(surface, 1.0)

        # Explicit wheelchair tag
        wheelchair = tags.get("wheelchair", "")
        if wheelchair in WEIGHT["wheelchair"]:
            w *= WEIGHT["wheelchair"][wheelchair]

        # Incline penalty
        incline_raw = tags.get("incline", "").replace("%", "").strip()
        try:
            if abs(float(incline_raw)) > WEIGHT["incline_threshold_pct"]:
                w *= WEIGHT["incline_penalty"]
        except ValueError:
            pass

        # Barrier penalty
        if tags.get("barrier", "") in BLOCKED_BARRIERS:
            w *= 10.0

        # Kerb / tactile paving bonus
        if tags.get("kerb") in ("lowered", "flush"):
            w *= 0.9
        if tags.get("tactile_paving") == "yes":
            w *= 0.95

        # Narrow path penalty (wheelchair needs >= 0.9m)
        width_raw = tags.get("width", "").replace("m", "").strip()
        try:
            if float(width_raw) < 0.9:
                w *= 5.0
        except ValueError:
            pass

        return max(w, 0.5)

    # ------------------------------------------------------------------ #
    #  A* pathfinding                                                      #
    # ------------------------------------------------------------------ #

    def _run_astar(self, origin, destination, on_route, on_error):
        try:
            origin_node = self._nearest_node(origin[0], origin[1])
            dest_node   = self._nearest_node(destination[0], destination[1])

            if origin_node is None or dest_node is None:
                self._deliver_error(
                    on_error, "Could not find a nearby walkable path."
                )
                return

            print(f"[RoutingService] A* from node {origin_node} "
                  f"to node {dest_node}")

            path = nx.astar_path(
                self.graph,
                source=origin_node,
                target=dest_node,
                heuristic=self._heuristic,
                weight="weight",
            )

            result = self._build_result(path, origin, destination)

            print(f"[RoutingService] Route found — "
                  f"{len(result['waypoints'])} waypoints, "
                  f"{result['distance_m']:.0f}m, "
                  f"score: {result['accessibility_score']}")

            if on_route and not self._cancel:
                Clock.schedule_once(lambda dt: on_route(result), 0)

        except nx.NetworkXNoPath:
            self._deliver_error(
                on_error,
                "No accessible route found between these points. "
                "Try a closer destination."
            )
        except nx.NodeNotFound:
            self._deliver_error(on_error, "Route nodes not found in graph.")
        except Exception as e:
            self._deliver_error(on_error, f"Routing error: {e}")

    def _nearest_node(self, lat, lon):
        """
        Return the graph node ID closest to (lat, lon).
        Only searches within the largest connected component
        since the graph has already been pruned.
        """
        best_id   = None
        best_dist = float("inf")

        for nid, data in self.graph.nodes(data=True):
            d = haversine(lat, lon, data["lat"], data["lon"])
            if d < best_dist:
                best_dist = d
                best_id   = nid

        if best_dist > 150:
            print(f"[RoutingService] Warning — nearest node is "
                  f"{best_dist:.0f}m away")

        return best_id

    def _heuristic(self, u, v):
        """
        A* heuristic — straight-line haversine distance.
        Admissible because real cost >= straight-line distance.
        """
        u_data = self.graph.nodes[u]
        v_data = self.graph.nodes[v]
        return haversine(
            u_data["lat"], u_data["lon"],
            v_data["lat"], v_data["lon"],
        )

    def _build_result(self, node_path, origin, destination):
        """
        Convert a node ID path into a result dict:
        {
            waypoints:           [(lat, lon), ...]
            distance_m:          float
            eta_minutes:         float
            accessibility_score: float  (0-1, higher = more accessible)
            edges:               [edge_data_dict, ...]
        }
        """
        waypoints  = [origin]
        total_dist = 0.0
        total_cost = 0.0
        edges      = []

        for i in range(len(node_path) - 1):
            u    = node_path[i]
            v    = node_path[i + 1]
            data = self.graph[u][v]

            node_data = self.graph.nodes[v]
            waypoints.append((node_data["lat"], node_data["lon"]))

            total_dist += data.get("distance", 0)
            total_cost += data.get("weight",   0)
            edges.append(data)

        waypoints.append(destination)

        # Score: ratio of raw distance to weighted cost
        # 1.0 = perfectly accessible, lower = barriers or rough surfaces
        if total_cost > 0:
            score = min(total_dist / total_cost, 1.0)
        else:
            score = 1.0

        # Wheelchair walking speed ~60m/min
        eta = total_dist / 60.0

        return {
            "waypoints":           waypoints,
            "distance_m":          total_dist,
            "eta_minutes":         eta,
            "accessibility_score": round(score, 2),
            "edges":               edges,
        }

    # ------------------------------------------------------------------ #
    #  Helpers                                                             #
    # ------------------------------------------------------------------ #

    def _deliver_error(self, on_error, message):
        print(f"[RoutingService] {message}")
        if on_error and not self._cancel:
            Clock.schedule_once(lambda dt: on_error(message), 0)


# ------------------------------------------------------------------ #
#  Haversine distance in metres                                        #
# ------------------------------------------------------------------ #

def haversine(lat1, lon1, lat2, lon2):
    R    = 6_371_000
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a    = (math.sin(dphi / 2) ** 2
            + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))