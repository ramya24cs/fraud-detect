import math
import unittest
from unittest.mock import patch

from ml.src.decision.cost_matrix import CostMatrix, Decision
from ml.src.decision.decision_engine import evaluate_transaction


def make_transaction():
    return {
        "Time": 1000,
        **{f"V{i}": 0.1 for i in range(1, 29)},
        "Amount": 150.0,
    }


class TestDecisionEngine(unittest.TestCase):
    def setUp(self):
        self.cost_matrix = CostMatrix(5, 20, 1000, 10, 2)
        self.transaction = make_transaction()

    @patch("ml.src.decision.decision_engine.explain_transaction")
    @patch("ml.src.decision.decision_engine.predict_fraud")
    def test_valid_transaction(self, predict_mock, explain_mock):
        predict_mock.return_value = 0.01
        explain_mock.return_value = [
            {"feature": "V14", "impact": 0.5}
        ]

        result = evaluate_transaction(
            self.transaction,
            self.cost_matrix,
        )

        self.assertEqual(result["decision"], "REVIEW")
        self.assertEqual(result["model_version"], "xgb-cost-v1")
        self.assertEqual(len(result["explanation"]), 1)
        self.assertTrue(math.isfinite(result["expected_cost"]))

    @patch("ml.src.decision.decision_engine.explain_transaction")
    @patch("ml.src.decision.decision_engine.predict_fraud")
    def test_all_three_decisions(self, predict_mock, explain_mock):
        explain_mock.return_value = []

        test_cases = [
            (0.001, Decision.APPROVE),
            (0.50, Decision.REVIEW),
            (0.99, Decision.BLOCK),
        ]

        for probability, expected in test_cases:
            with self.subTest(probability=probability):
                predict_mock.return_value = probability

                result = evaluate_transaction(
                    self.transaction,
                    self.cost_matrix,
                )

                self.assertEqual(result["decision"], expected.value)

    def test_missing_features_rejected(self):
        with self.assertRaisesRegex(
            ValueError,
            "Missing transaction features",
        ):
            evaluate_transaction(
                {},
                self.cost_matrix,
            )

    def test_non_dictionary_rejected(self):
        with self.assertRaisesRegex(
            ValueError,
            "transaction must be a dictionary",
        ):
            evaluate_transaction(
                [],
                self.cost_matrix,
            )

    def test_invalid_numeric_values_rejected(self):
        invalid_values = [
            float("nan"),
            float("inf"),
            float("-inf"),
            True,
            "hello",
        ]

        for value in invalid_values:
            with self.subTest(value=value):
                transaction = make_transaction()
                transaction["V14"] = value

                with self.assertRaises(ValueError):
                    evaluate_transaction(
                        transaction,
                        self.cost_matrix,
                    )

    def test_original_transaction_unchanged(self):
        transaction = make_transaction()
        transaction["Amount"] = "150.0"
        original = transaction.copy()

        with patch(
            "ml.src.decision.decision_engine.predict_fraud",
            return_value=0.01,
        ), patch(
            "ml.src.decision.decision_engine.explain_transaction",
            return_value=[],
        ):
            evaluate_transaction(
                transaction,
                self.cost_matrix,
            )

        self.assertEqual(transaction, original)

    def test_cost_matrix_selects_action_independently_of_risk_tier(self):
        self.assertEqual(
            self.cost_matrix.select_decision(0.35),
            Decision.REVIEW,
        )
        self.assertEqual(
            self.cost_matrix.select_decision(0.80),
            Decision.BLOCK,
        )

    def test_approved_cost_matrix_never_blocks_with_current_costs(self):
        from ml.src.decision.defaults import approved_cost_matrix

        costs = approved_cost_matrix()
        self.assertEqual(costs.select_decision(0.99), Decision.REVIEW)


if __name__ == "__main__":
    unittest.main()
