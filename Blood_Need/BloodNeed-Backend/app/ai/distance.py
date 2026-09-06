from math import radians
from math import sin
from math import cos
from math import sqrt
from math import atan2


def calculate_distance(
        lat1,
        lon1,
        lat2,
        lon2
):

    R = 6371

    dlat = radians(lat2 - lat1)

    dlon = radians(lon2 - lon1)

    a = (
        sin(dlat / 2) ** 2
        +
        cos(radians(lat1))
        *
        cos(radians(lat2))
        *
        sin(dlon / 2) ** 2
    )

    c = 2 * atan2(
        sqrt(a),
        sqrt(1 - a)
    )

    return round(
        R * c,
        2
    )