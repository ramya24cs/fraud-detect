import math
import unittest

from ml.src.feedback.training_data_builder import (
    FEATURES,
    build_training_data,
)


def make_record(label="CONFIRMED_FRAUD"):
    return {
        "transaction_id": "TX-001",
        "label": label,
        "features": {
            feature: 100.0 + index
            for index, feature in enumerate(FEATURES)
        },
    }


class TestTrainingDataBuilder(unittest.TestCase):
    def test_confirmed_fraud_is_included(self):
        result = build_training_data([make_record("CONFIRMED_FRAUD")])

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].label, 1)
        self.assertEqual(result[0].transaction_id, "TX-001")

    def test_confirmed_genuine_is_included(self):
        result = build_training_data([make_record("CONFIRMED_GENUINE")])

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].label, 0)

    def test_disputed_and_inconclusive_are_excluded(self):
        records = [
            make_record("DISPUTED"),
            make_record("INCONCLUSIVE"),
        ]

        self.assertEqual(build_training_data(records), [])

    def test_invalid_label_is_excluded(self):
        self.assertEqual(build_training_data([make_record("UNKNOWN")]), [])

    def test_missing_features_are_excluded(self):
        record = make_record()
        record["features"].pop("V14")

        self.assertEqual(build_training_data([record]), [])

    def test_non_dictionary_features_are_excluded(self):
        record = make_record()
        record["features"] = []

        self.assertEqual(build_training_data([record]), [])

    def test_feature_order_is_preserved(self):
        result = build_training_data([make_record("CONFIRMED_FRAUD")])

        self.assertEqual(list(result[0].features.keys()), FEATURES)
        self.assertEqual(len(result[0].features), 30)

    def test_missing_transaction_id_is_handled(self):
        record = make_record()
        del record["transaction_id"]

        self.assertEqual(build_training_data([record]), [])

    def test_invalid_numeric_feature_is_handled(self):
        record = make_record()
        record["features"]["V14"] = "not-a-number"

        self.assertEqual(build_training_data([record]), [])

    def test_non_finite_features_are_excluded(self):
        for value in [float("nan"), float("inf"), float("-inf")]:
            with self.subTest(value=value):
                record = make_record()
                record["features"]["V14"] = value

                result = build_training_data([record])

                self.assertEqual(result, [])
                if result:
                    self.assertTrue(
                        all(
                            math.isfinite(v)
                            for v in result[0].features.values()
                        )
                    )

    def test_duplicate_transaction_ids_with_conflicting_labels_are_excluded(self):
        first_record = make_record("CONFIRMED_FRAUD")
        second_record = make_record("CONFIRMED_GENUINE")
        second_record["features"]["Amount"] = 999.0

        result = build_training_data([first_record, second_record])

        self.assertEqual(result, [])

    def test_transaction_ids_are_normalized_before_conflict_detection(self):
        first_record = make_record("CONFIRMED_FRAUD")
        second_record = make_record("CONFIRMED_GENUINE")
        second_record["transaction_id"] = " TX-001 "

        result = build_training_data([first_record, second_record])

        self.assertEqual(result, [])

    def test_duplicate_transaction_ids_with_same_label_are_included_once(self):
        first_record = make_record("CONFIRMED_FRAUD")
        second_record = make_record("CONFIRMED_FRAUD")
        second_record["features"]["Amount"] = 999.0

        result = build_training_data([first_record, second_record])

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].label, 1)
        self.assertEqual(result[0].features["Amount"], 129.0)
    def test_boolean_features_are_excluded(self):
        record = make_record()
        record["features"]["V14"] = True

        result = build_training_data([record])

        self.assertEqual(result, [])


if __name__ == "__main__":
    unittest.main()
