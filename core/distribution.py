import math
import random


class Distribution:
    def __init__(self, mean=0.0, std=1.0, name="X"):
        self.mean = mean
        self.std = std
        self.name = name

    @property
    def variance(self):
        return self.std ** 2

    def sample(self, n=1000):
        random.seed(42)
        samples = []
        for _ in range(n):
            u1 = random.random()
            u2 = random.random()
            z = math.sqrt(-2 * math.log(u1)) * math.cos(2 * math.pi * u2)
            samples.append(self.mean + z * self.std)
        return samples

    def __repr__(self):
        return f"{self.name} ~ N(mean={self.mean:.3f}, std={self.std:.3f})"
