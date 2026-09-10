"""
Partner Routing Engine service using Haversine Distance algorithm.
"""

import math
from app.models.partner import ChannelPartner

CITY_COORDINATE_MAP = {
    "thiruvananthapuram": (8.5241, 76.9366),
    "trivandrum": (8.5241, 76.9366),
    "kerala": (8.5241, 76.9366),
    "kochi": (9.9312, 76.2673),
    "ernakulam": (9.9312, 76.2673),
    "kozhikode": (11.2588, 75.7804),
    "calicut": (11.2588, 75.7804),
    "delhi": (28.6139, 77.2090),
    "new delhi": (28.6139, 77.2090),
    "noida": (28.5355, 77.3910),
    "mumbai": (19.0760, 72.8777),
    "bengaluru": (12.9716, 77.5946),
    "bangalore": (12.9716, 77.5946),
    "chennai": (13.0827, 80.2707),
    "hyderabad": (17.3850, 78.4867),
}


def resolve_location_coordinates(location: dict | str | None) -> tuple[float, float]:
    """
    Resolves a location dict or string into (latitude, longitude) coordinates.
    Matches major cities/states in India or defaults to Thiruvananthapuram (8.5241, 76.9366).
    """
    if not location:
        return (8.5241, 76.9366)

    loc_str = ""
    if isinstance(location, dict):
        loc_str = " ".join(str(v) for v in location.values() if v).lower()
    elif isinstance(location, str):
        loc_str = location.lower()

    for city_key, coords in CITY_COORDINATE_MAP.items():
        if city_key in loc_str:
            return coords

    # Default fallback to Thiruvananthapuram
    return (8.5241, 76.9366)


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great-circle distance between two geographical points on Earth
    (given in decimal degrees) using the Haversine formula.

    Returns distance in kilometers.
    """
    R = 6371.0  # Earth's mean radius in kilometers

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))

    return R * c


async def find_nearest_partners(
    latitude: float,
    longitude: float,
    scheme_id: str | None = None,
    limit: int = 3,
) -> list[dict]:
    """
    Query MongoDB for channel partners, calculate Haversine distance,
    and return the closest partners compatible with the scheme.
    """
    # Fetch all registered channel partners
    partners = await ChannelPartner.find_all().to_list()

    matched_partners = []
    for p in partners:
        # Check scheme compatibility if specified
        if scheme_id and p.compatible_schemes:
            if scheme_id not in p.compatible_schemes and "ALL" not in p.compatible_schemes:
                continue

        dist_km = haversine_distance(latitude, longitude, p.latitude, p.longitude)
        partner_dict = p.model_dump(mode="json", exclude={"id"})
        partner_dict["distance_km"] = round(dist_km, 2)
        partner_dict["distance_formatted"] = f"{round(dist_km, 1)} km away"
        matched_partners.append(partner_dict)

    # Sort by distance ascending
    matched_partners.sort(key=lambda x: x["distance_km"])
    return matched_partners[:limit]
