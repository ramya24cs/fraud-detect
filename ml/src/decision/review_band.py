from dataclasses import dataclass


@dataclass(frozen=True)
class ReviewBand:
    lower: float
    upper: float
    capacity: int | None = None

    def __post_init__(self):
        if not 0.0 <= self.lower <= 1.0:
            raise ValueError("lower must be between 0 and 1")

        if not 0.0 <= self.upper <= 1.0:
            raise ValueError("upper must be between 0 and 1")

        if self.lower >= self.upper:
            raise ValueError("lower must be lower than upper")

        if self.capacity is not None and self.capacity < 0:
            raise ValueError("capacity must be non-negative")

    def contains(self, fraud_probability: float) -> bool:
        if not 0.0 <= fraud_probability <= 1.0:
            raise ValueError("fraud_probability must be between 0 and 1")

        return self.lower <= fraud_probability < self.upper