import requests
from kivy.clock import Clock


class OSMService:
    """
    Fetch accessibility features (ramps, elevators, barriers) 
    from Overpass API and return them as POI markers.
    """

    OVERPASS_URL = "https://overpass-api.de/api/interpreter"

    # Feature types and their display colors
    FEATURES = {
        "ramp": {
            "color": (0.11, 0.62, 0.46, 1),  # Green
            "query_tags": "wheelchair=yes OR ramp=yes",
        },
        "elevator": {
            "color": (0.22, 0.47, 0.87, 1),  # Blue
            "query_tags": "elevator=yes",
        },
        "barrier": {
            "color": (0.89, 0.35, 0.19, 1),  # Orange/Red
            "query_tags": "barrier=yes OR barrier=wall OR barrier=fence",
        },
    }

    def __init__(self):
        self._session = requests.Session()
        self._session.timeout = 10
        self._cancel = False

    def fetch_accessibility_features(
        self, 
        bbox,  # (min_lon, min_lat, max_lon, max_lat)
        on_results=None,
        on_error=None
    ):
        """
        Fetch accessibility features from Overpass API.
        
        bbox: (min_lon, min_lat, max_lon, max_lat) tuple
        Callbacks:
            on_results(features_list) — list of dicts with lat, lon, type, tags
            on_error(message) — error message
        """
        self._cancel = False
        
        # Run fetch directly (will block briefly, but OSM API is fast)
        # This ensures logs appear in console
        self._do_fetch(bbox, on_results, on_error)

    def _do_fetch(self, bbox, on_results, on_error):
        """Actual fetch logic run on worker thread."""
        try:
            min_lon, min_lat, max_lon, max_lat = bbox
            
            print(f"[OSMService] Bbox coordinates: {min_lat},{min_lon},{max_lat},{max_lon}")
            
            # Try a working Overpass query format
            query = f"""
[out:json];
(
  node["wheelchair"="yes"]({min_lat},{min_lon},{max_lat},{max_lon});
  way["wheelchair"="yes"]({min_lat},{min_lon},{max_lat},{max_lon});
  node["ramp"]({min_lat},{min_lon},{max_lat},{max_lon});
  way["ramp"]({min_lat},{min_lon},{max_lat},{max_lon});
  node["elevator"]({min_lat},{min_lon},{max_lat},{max_lon});
  way["elevator"]({min_lat},{min_lon},{max_lat},{max_lon});
  node["barrier"]({min_lat},{min_lon},{max_lat},{max_lon});
  way["barrier"]({min_lat},{min_lon},{max_lat},{max_lon});
);
out center;
""".strip()
            
            print(f"[OSMService] Trying Overpass query...")
            
            response = self._session.post(
                self.OVERPASS_URL,
                data=query,
                headers={'Content-Type': 'text/plain'},
                timeout=15
            )
            response.raise_for_status()
            
            print(f"[OSMService] Response status: {response.status_code}")
            
            if self._cancel:
                print("[OSMService] Fetch cancelled")
                return
            
            data = response.json()
            print(f"[OSMService] Response elements: {len(data.get('elements', []))}")
            
            features = self._parse_features(data)
            
            print(f"[OSMService] Found {len(features)} accessibility features")
            
            # Always add sample data for now to ensure markers are visible
            if len(features) == 0:
                print("[OSMService] Adding sample data for demonstration")
                center_lat = (min_lat + max_lat) / 2
                center_lon = (min_lon + max_lon) / 2
                
                sample_features = [
                    {
                        "lat": center_lat + 0.001,
                        "lon": center_lon + 0.001,
                        "type": "ramp",
                        "name": "Sample Ramp",
                        "tags": {"wheelchair": "yes"}
                    },
                    {
                        "lat": center_lat - 0.001,
                        "lon": center_lon - 0.001,
                        "type": "elevator",
                        "name": "Sample Elevator",
                        "tags": {"elevator": "yes"}
                    },
                    {
                        "lat": center_lat + 0.001,
                        "lon": center_lon - 0.001,
                        "type": "barrier",
                        "name": "Sample Barrier",
                        "tags": {"barrier": "wall"}
                    }
                ]
                features.extend(sample_features)
                print(f"[OSMService] Total features: {len(features)} (including samples)")
            
            if on_results:
                Clock.schedule_once(
                    lambda dt: on_results(features),
                    0
                )
            
        except Exception as e:
            msg = f"OSM fetch error: {str(e)}"
            print(f"[OSMService] {msg}")
            import traceback
            traceback.print_exc()
            if on_error:
                Clock.schedule_once(lambda dt: on_error(msg), 0)

    def _parse_features(self, data):
        """Parse Overpass API response and categorize features."""
        features = []
        
        if "elements" not in data:
            print("[OSMService] No elements in response")
            return features
        
        print(f"[OSMService] Parsing {len(data['elements'])} elements from API")
        
        for element in data["elements"]:
            if element.get("type") not in ("node", "way"):
                continue
            
            # Get coordinates (center for ways, direct for nodes)
            if "center" in element:
                lat, lon = element["center"]["lat"], element["center"]["lon"]
            elif element.get("type") == "node":
                lat, lon = element.get("lat"), element.get("lon")
            else:
                continue
            
            if lat is None or lon is None:
                continue
            
            # Determine feature type
            tags = element.get("tags", {})
            feature_type = self._classify_feature(tags)
            
            if feature_type:
                feature = {
                    "lat": lat,
                    "lon": lon,
                    "type": feature_type,
                    "name": tags.get("name", f"{feature_type.title()} {len(features)+1}"),
                    "tags": tags,
                }
                features.append(feature)
                print(f"[OSMService] Found {feature_type} at {lat:.5f}, {lon:.5f}")
        
        return features

    def _classify_feature(self, tags):
        """
        Classify a feature by checking its tags.
        Returns: 'ramp', 'elevator', 'barrier', or None
        """
        # Check for ramps
        if tags.get("wheelchair") == "yes" or tags.get("ramp") == "yes":
            return "ramp"
        
        # Check for elevators
        if tags.get("elevator") == "yes":
            return "elevator"
        
        # Check for barriers
        barrier = tags.get("barrier")
        if barrier in ("yes", "wall", "fence", "hedge"):
            return "barrier"
        
        return None

    def cancel(self):
        """Cancel ongoing fetch."""
        self._cancel = True