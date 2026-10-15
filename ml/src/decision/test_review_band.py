from ml.src.decision.review_band import ReviewBand


def test_review_band_contains():
    band = ReviewBand(
        lower=0.02,
        upper=0.98,
    )

    assert band.contains(0.02)
    assert band.contains(0.50)
    assert not band.contains(0.98)
    assert not band.contains(0.01)


def test_review_band_capacity():
    band = ReviewBand(
        lower=0.02,
        upper=0.98,
        capacity=100,
    )

    assert band.capacity == 100


if __name__ == "__main__":
    test_review_band_contains()
    test_review_band_capacity()
    print("ReviewBand tests passed")