import math
import random
import string
from decimal import Decimal

EARTH_RADIUS_MILES = Decimal("3958.8")

BASE_RATE_PER_MILE = Decimal("1.85")
WEIGHT_RATE_PER_KG = Decimal("0.15")
PACKAGE_TYPE_MULTIPLIER = {
    "standard_freight": Decimal("1.0"),
    "oversized_equipment": Decimal("1.4"),
    "small_parcel": Decimal("0.8"),
    "liquid_bulk": Decimal("1.25"),
}


def haversine_miles(lat1, lng1, lat2, lng2) -> Decimal:
    lat1, lng1, lat2, lng2 = map(float, (lat1, lng1, lat2, lng2))
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lng2 - lng1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    return (Decimal(str(c)) * EARTH_RADIUS_MILES).quantize(Decimal("0.01"))


def estimate_market_price(distance_miles: Decimal, weight_kg: Decimal, package_type: str) -> Decimal:
    multiplier = PACKAGE_TYPE_MULTIPLIER.get(package_type, Decimal("1.0"))
    price = (distance_miles * BASE_RATE_PER_MILE + weight_kg * WEIGHT_RATE_PER_KG) * multiplier
    return price.quantize(Decimal("0.01"))


def generate_otp() -> str:
    return "".join(random.choices(string.digits, k=4))
