import unittest

from services.wind_reference import get_all_locations, resolve_wind_params


class WindReferenceTests(unittest.TestCase):
    def test_locations_include_coordinates(self) -> None:
        data = get_all_locations()

        for province in data["provinces"]:
            for city in province["cities"]:
                self.assertIn("lat", city)
                self.assertIn("lng", city)
                self.assertIsNotNone(city["lat"])
                self.assertIsNotNone(city["lng"])

    def test_resolve_wind_params_exact_match(self) -> None:
        result = resolve_wind_params(
            province="北京市",
            city="北京市",
            code="110000",
            roughness="C",
            erection_height_hs_m=24.0,
        )

        self.assertEqual(result["matched_city"], "北京市")
        self.assertEqual(result["match_type"], "exact")
        self.assertIsNone(result["distance_km"])
        self.assertFalse(result["is_fallback"])

    def test_resolve_wind_params_nearby_same_province_match(self) -> None:
        result = resolve_wind_params(
            province="河北省",
            city="晋州市",
            code="130183",
            roughness="C",
            erection_height_hs_m=24.0,
        )

        self.assertEqual(result["matched_city"], "石家庄市")
        self.assertEqual(result["match_type"], "nearby_same_province")
        self.assertIsNotNone(result["distance_km"])
        self.assertGreater(float(result["distance_km"]), 0.0)
        self.assertTrue(result["is_fallback"])

    def test_manual_coordinate_city_can_still_resolve(self) -> None:
        result = resolve_wind_params(
            province="湖南省",
            city="津市市",
            code="430781",
            roughness="C",
            erection_height_hs_m=24.0,
        )

        self.assertEqual(result["matched_city"], "常德市")
        self.assertEqual(result["match_type"], "nearby_same_province")
        self.assertIsNotNone(result["distance_km"])
        self.assertGreater(float(result["distance_km"]), 0.0)


if __name__ == "__main__":
    unittest.main()
