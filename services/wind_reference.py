from __future__ import annotations

import json
import math
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal


BASE_DIR = Path(__file__).resolve().parent.parent
WIND_REFERENCE_PATH = BASE_DIR / "data" / "wind_reference.json"

MUZ_HEIGHTS_M = [
    5.0,
    10.0,
    15.0,
    20.0,
    30.0,
    40.0,
    50.0,
    60.0,
    70.0,
    80.0,
    90.0,
    100.0,
    150.0,
    200.0,
    250.0,
    300.0,
    350.0,
    400.0,
    450.0,
    500.0,
    550.0,
]

MUZ_TABLE = {
    "A": [
        1.09,
        1.28,
        1.42,
        1.52,
        1.67,
        1.79,
        1.89,
        1.97,
        2.05,
        2.12,
        2.18,
        2.23,
        2.46,
        2.64,
        2.78,
        2.91,
        2.91,
        2.91,
        2.91,
        2.91,
        2.91,
    ],
    "B": [
        1.00,
        1.00,
        1.13,
        1.23,
        1.39,
        1.52,
        1.62,
        1.71,
        1.79,
        1.87,
        1.93,
        2.00,
        2.25,
        2.46,
        2.63,
        2.77,
        2.91,
        2.91,
        2.91,
        2.91,
        2.91,
    ],
    "C": [
        0.65,
        0.65,
        0.65,
        0.74,
        0.88,
        1.00,
        1.10,
        1.20,
        1.28,
        1.36,
        1.43,
        1.50,
        1.79,
        2.03,
        2.24,
        2.43,
        2.60,
        2.76,
        2.91,
        2.91,
        2.91,
    ],
    "D": [
        0.51,
        0.51,
        0.51,
        0.51,
        0.51,
        0.60,
        0.69,
        0.77,
        0.84,
        0.91,
        0.98,
        1.04,
        1.33,
        1.58,
        1.81,
        2.02,
        2.22,
        2.40,
        2.58,
        2.74,
        2.91,
    ],
}

MATCH_TYPE_EXACT = "exact"
MATCH_TYPE_FUZZY = "fuzzy"
MATCH_TYPE_NEARBY_SAME_PROVINCE = "nearby_same_province"
MATCH_TYPE_NEARBY_NATIONAL = "nearby_national"
MatchType = Literal[
    "exact",
    "fuzzy",
    "nearby_same_province",
    "nearby_national",
]

NAME_SUFFIXES = (
    "特别行政区",
    "维吾尔自治区",
    "壮族自治区",
    "回族自治区",
    "自治区",
    "自治州",
    "自治县",
    "自治旗",
    "地区",
    "盟",
    "省",
    "市",
    "县",
    "区",
    "旗",
)


@dataclass(frozen=True)
class WindReferenceMatch:
    province_name: str
    province_code: str
    city_name: str
    city_code: str
    station_name: str
    altitude_m: float
    w0_10yr_kn_m2: float
    lat: float | None
    lng: float | None
    matched_city: str
    match_type: MatchType
    distance_km: float | None

    @property
    def is_fallback(self) -> bool:
        return self.match_type != MATCH_TYPE_EXACT


def _normalize_name(name: str | None) -> str:
    if name is None:
        return ""
    return "".join(str(name).split()).strip()


def _normalize_code(code: str | None) -> str | None:
    if code is None:
        return None
    normalized = str(code).strip()
    return normalized or None


def _build_aliases(name: str | None) -> list[str]:
    normalized = _normalize_name(name)
    if not normalized:
        return []

    aliases = [normalized]
    for suffix in NAME_SUFFIXES:
        if normalized.endswith(suffix) and len(normalized) > len(suffix):
            alias = normalized[: -len(suffix)]
            if alias not in aliases:
                aliases.append(alias)
    return aliases


def _entry_aliases(entry: dict[str, Any]) -> list[str]:
    aliases: list[str] = []
    for source in (
        entry["city"].get("name"),
        entry["city"].get("station_name"),
    ):
        for alias in _build_aliases(source):
            if alias not in aliases:
                aliases.append(alias)
    return aliases


def _has_reference_data(entry: dict[str, Any]) -> bool:
    city_item = entry["city"]
    return (
        city_item.get("altitude_m") is not None
        and city_item.get("w0_10yr_kn_m2") is not None
    )


def _has_coordinates(entry: dict[str, Any]) -> bool:
    city_item = entry["city"]
    return city_item.get("lat") is not None and city_item.get("lng") is not None


def _entry_coordinates(entry: dict[str, Any]) -> tuple[float, float] | None:
    if not _has_coordinates(entry):
        return None
    city_item = entry["city"]
    return float(city_item["lat"]), float(city_item["lng"])


def _haversine_km(
    lat1: float,
    lng1: float,
    lat2: float,
    lng2: float,
) -> float:
    radius_km = 6371.0
    lat1_rad = math.radians(lat1)
    lng1_rad = math.radians(lng1)
    lat2_rad = math.radians(lat2)
    lng2_rad = math.radians(lng2)
    delta_lat = lat2_rad - lat1_rad
    delta_lng = lng2_rad - lng1_rad

    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1_rad)
        * math.cos(lat2_rad)
        * math.sin(delta_lng / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return radius_km * c


def _entry_to_match(
    entry: dict[str, Any],
    *,
    match_type: MatchType,
    distance_km: float | None,
) -> WindReferenceMatch:
    province_item = entry["province"]
    city_item = entry["city"]
    return WindReferenceMatch(
        province_name=str(province_item["name"]),
        province_code=str(province_item["code"]),
        city_name=str(city_item["name"]),
        city_code=str(city_item["code"]),
        station_name=str(city_item.get("station_name") or city_item["name"]),
        altitude_m=float(city_item["altitude_m"]),
        w0_10yr_kn_m2=float(city_item["w0_10yr_kn_m2"]),
        lat=float(city_item["lat"]) if city_item.get("lat") is not None else None,
        lng=float(city_item["lng"]) if city_item.get("lng") is not None else None,
        matched_city=str(city_item["name"]),
        match_type=match_type,
        distance_km=distance_km,
    )


@lru_cache(maxsize=1)
def _load_wind_reference() -> dict[str, Any]:
    with WIND_REFERENCE_PATH.open("r", encoding="utf-8") as fp:
        return json.load(fp)


@lru_cache(maxsize=1)
def _build_indexes() -> dict[str, Any]:
    data = _load_wind_reference()

    province_alias_index: dict[str, dict[str, Any]] = {}
    province_by_code: dict[str, dict[str, Any]] = {}
    province_entries_index: dict[str, list[dict[str, Any]]] = {}
    city_entries_by_code: dict[str, list[dict[str, Any]]] = {}
    all_entries_with_data_and_coords: list[dict[str, Any]] = []

    for province_item in data.get("provinces", []):
        province_code = str(province_item["code"])
        province_by_code[province_code] = province_item

        for alias in _build_aliases(province_item["name"]):
            province_alias_index[alias] = province_item

        entries: list[dict[str, Any]] = []
        for city_item in province_item.get("cities", []):
            entry = {
                "province": province_item,
                "city": city_item,
            }
            entries.append(entry)

            city_code = str(city_item["code"])
            city_entries_by_code.setdefault(city_code, []).append(entry)

            if _has_reference_data(entry) and _has_coordinates(entry):
                all_entries_with_data_and_coords.append(entry)

        province_entries_index[province_code] = entries

    return {
        "province_alias_index": province_alias_index,
        "province_by_code": province_by_code,
        "province_entries_index": province_entries_index,
        "city_entries_by_code": city_entries_by_code,
        "all_entries_with_data_and_coords": all_entries_with_data_and_coords,
    }


def _find_province(province: str) -> dict[str, Any]:
    target = _normalize_name(province)
    province_item = _build_indexes()["province_alias_index"].get(target)
    if province_item is None:
        raise ValueError(f"Province reference data not found: {province}")
    return province_item


def _fuzzy_score(target: str, alias: str) -> tuple[int, int, int] | None:
    if not target or not alias:
        return None

    if target == alias:
        return (10_000, 0, len(alias))

    if target in alias or alias in target:
        overlap = min(len(target), len(alias))
        gap = abs(len(target) - len(alias))
        return (overlap * 100, -gap, len(alias))

    return None


def _find_entry_by_code(
    entries: list[dict[str, Any]],
    code: str | None,
) -> dict[str, Any] | None:
    normalized_code = _normalize_code(code)
    if normalized_code is None:
        return None

    for entry in entries:
        if str(entry["city"]["code"]) == normalized_code:
            return entry
    return None


def _find_exact_entry_by_name(
    entries: list[dict[str, Any]],
    city: str,
) -> dict[str, Any] | None:
    target = _normalize_name(city)
    if not target:
        return None

    for entry in entries:
        if target in _entry_aliases(entry):
            return entry
    return None


def _find_fuzzy_entry_by_name(
    entries: list[dict[str, Any]],
    city: str,
    *,
    require_data: bool,
) -> dict[str, Any] | None:
    target = _normalize_name(city)
    if not target:
        return None

    best_entry: dict[str, Any] | None = None
    best_score: tuple[int, int, int] | None = None

    for entry in entries:
        if require_data and not _has_reference_data(entry):
            continue

        alias_scores = [
            score
            for alias in _entry_aliases(entry)
            if (score := _fuzzy_score(target, alias)) is not None
        ]
        if not alias_scores:
            continue

        candidate_score = max(alias_scores)
        if best_score is None or candidate_score > best_score:
            best_entry = entry
            best_score = candidate_score

    return best_entry


def _find_nearest_entry(
    entries: list[dict[str, Any]],
    *,
    target_entry: dict[str, Any],
) -> tuple[dict[str, Any], float] | None:
    target_coords = _entry_coordinates(target_entry)
    if target_coords is None:
        return None

    target_lat, target_lng = target_coords
    target_code = str(target_entry["city"]["code"])
    best_entry: dict[str, Any] | None = None
    best_distance: float | None = None

    for entry in entries:
        if not _has_reference_data(entry) or not _has_coordinates(entry):
            continue
        if str(entry["city"]["code"]) == target_code:
            continue

        entry_lat, entry_lng = _entry_coordinates(entry) or (None, None)
        if entry_lat is None or entry_lng is None:
            continue

        distance_km = _haversine_km(target_lat, target_lng, entry_lat, entry_lng)
        if best_distance is None or distance_km < best_distance:
            best_entry = entry
            best_distance = distance_km

    if best_entry is None or best_distance is None:
        return None

    return best_entry, best_distance


def get_all_locations() -> dict[str, Any]:
    """Return the full province/city cascade dataset."""

    return _load_wind_reference()


def resolve_wind_reference(
    *,
    province: str,
    city: str,
    code: str | None = None,
) -> WindReferenceMatch:
    indexes = _build_indexes()
    province_item = _find_province(province)
    province_code = str(province_item["code"])
    province_entries = indexes["province_entries_index"].get(province_code, [])

    if not province_entries:
        raise ValueError(f"City reference data not found: {province} / {city}")

    target_entry = _find_entry_by_code(province_entries, code)
    target_match_type: MatchType | None = None

    if target_entry is not None:
        target_match_type = MATCH_TYPE_EXACT
    else:
        target_entry = _find_exact_entry_by_name(province_entries, city)
        if target_entry is not None:
            target_match_type = MATCH_TYPE_EXACT
        else:
            target_entry = _find_fuzzy_entry_by_name(
                province_entries,
                city,
                require_data=False,
            )
            if target_entry is not None:
                target_match_type = MATCH_TYPE_FUZZY

    if target_entry is None or target_match_type is None:
        raise ValueError(f"City reference data not found: {province} / {city}")

    if _has_reference_data(target_entry):
        return _entry_to_match(
            target_entry,
            match_type=target_match_type,
            distance_km=None,
        )

    same_province_nearest = _find_nearest_entry(
        province_entries,
        target_entry=target_entry,
    )
    if same_province_nearest is not None:
        entry, distance_km = same_province_nearest
        return _entry_to_match(
            entry,
            match_type=MATCH_TYPE_NEARBY_SAME_PROVINCE,
            distance_km=distance_km,
        )

    national_nearest = _find_nearest_entry(
        indexes["all_entries_with_data_and_coords"],
        target_entry=target_entry,
    )
    if national_nearest is not None:
        entry, distance_km = national_nearest
        return _entry_to_match(
            entry,
            match_type=MATCH_TYPE_NEARBY_NATIONAL,
            distance_km=distance_km,
        )

    raise ValueError(
        f"Wind reference data not available for {province} / {city}, and no nearby "
        "city with valid wind parameters could be found."
    )


def get_wind_pressure(province: str, city: str, code: str | None = None) -> float:
    match = resolve_wind_reference(province=province, city=city, code=code)
    return match.w0_10yr_kn_m2


def get_city_altitude(province: str, city: str, code: str | None = None) -> float:
    match = resolve_wind_reference(province=province, city=city, code=code)
    return match.altitude_m


def get_wind_height_factor(roughness: str, height_m: float) -> float:
    roughness_key = roughness.strip().upper()
    if roughness_key not in MUZ_TABLE:
        raise ValueError(f"Unsupported terrain roughness category: {roughness}")
    if height_m <= 0:
        raise ValueError("Effective height must be greater than 0.")

    values = MUZ_TABLE[roughness_key]
    if height_m <= MUZ_HEIGHTS_M[0]:
        return values[0]
    if height_m >= MUZ_HEIGHTS_M[-1]:
        return values[-1]

    for index in range(len(MUZ_HEIGHTS_M) - 1):
        lower_h = MUZ_HEIGHTS_M[index]
        upper_h = MUZ_HEIGHTS_M[index + 1]
        if lower_h <= height_m <= upper_h:
            lower_v = values[index]
            upper_v = values[index + 1]
            ratio = (height_m - lower_h) / (upper_h - lower_h)
            return lower_v + (upper_v - lower_v) * ratio

    return values[-1]


def resolve_wind_params(
    *,
    province: str,
    city: str,
    roughness: str,
    erection_height_hs_m: float,
    code: str | None = None,
) -> dict[str, float | bool | str | None]:
    match = resolve_wind_reference(province=province, city=city, code=code)
    effective_height_m = erection_height_hs_m + match.altitude_m
    wind_height_factor_muz = get_wind_height_factor(roughness, effective_height_m)

    return {
        "w0_kn_m2": match.w0_10yr_kn_m2,
        "altitude_m": match.altitude_m,
        "effective_height_m": effective_height_m,
        "wind_height_factor_muz": wind_height_factor_muz,
        "matched_city": match.matched_city,
        "match_type": match.match_type,
        "distance_km": match.distance_km,
        "is_fallback": match.is_fallback,
    }
