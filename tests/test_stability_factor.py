import unittest

from calculators.exterior_scaffold import ExteriorScaffoldCalculator
from schemas import CalculationCheckRequest


class StabilityFactorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.calculator = ExteriorScaffoldCalculator()
        self.calculator.request_data = CalculationCheckRequest()

    def test_q355_exact_lookup(self) -> None:
        phi = self.calculator._get_stability_factor(146.0, "Q355")
        self.assertAlmostEqual(phi, 0.221, places=3)

    def test_q355_linear_interpolation(self) -> None:
        phi = self.calculator._get_stability_factor(146.5, "Q355")
        self.assertAlmostEqual(phi, 0.2185, places=4)

    def test_q235_normalized_lookup_points(self) -> None:
        phi_at_13 = self.calculator._get_stability_factor(13.0, "Q235")
        phi_at_163 = self.calculator._get_stability_factor(163.0, "Q235")
        self.assertAlmostEqual(phi_at_13, 0.966, places=3)
        self.assertAlmostEqual(phi_at_163, 0.145, places=3)

    def test_q235_linear_interpolation(self) -> None:
        phi = self.calculator._get_stability_factor(163.5, "Q235")
        self.assertAlmostEqual(phi, 0.1435, places=4)

    def test_vertical_standard_uses_q235_material_properties(self) -> None:
        request = CalculationCheckRequest()
        request.material_load_params.vertical_tube_spec = "Q235_PHI48X3_25"
        self.calculator.request_data = request

        result = self.calculator._check_vertical_standard()

        self.assertEqual(result["steel_grade"], "Q235")
        self.assertEqual(result["allowable_stress_n_mm2"], 205.0)
        self.assertAlmostEqual(
            result["phi"],
            self.calculator._get_stability_factor(result["lambda_val"], "Q235"),
            places=9,
        )

    def test_vertical_standard_uses_selected_q355_tube_section(self) -> None:
        request = CalculationCheckRequest()
        request.material_load_params.vertical_tube_spec = "Q355_PHI48X3_0"
        self.calculator.request_data = request

        result = self.calculator._check_vertical_standard()

        self.assertEqual(result["steel_grade"], "Q355")
        self.assertEqual(result["area_mm2"], 424.0)
        self.assertEqual(result["allowable_stress_n_mm2"], 300.0)

    def test_wall_tie_slip_resistance_matches_fastener_type(self) -> None:
        request = CalculationCheckRequest()
        request.wall_tie_params.fastener_connection_type = "DOUBLE"
        self.calculator.request_data = request
        double_result = self.calculator._check_wall_tie()

        request.wall_tie_params.fastener_connection_type = "SINGLE"
        self.calculator.request_data = request
        single_result = self.calculator._check_wall_tie()

        self.assertEqual(double_result["slip_resistance_kn"], 16.0)
        self.assertEqual(single_result["slip_resistance_kn"], 8.0)


if __name__ == "__main__":
    unittest.main()
