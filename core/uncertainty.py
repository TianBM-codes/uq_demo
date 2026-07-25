import math

from .distribution import Distribution


def propagate_uncertainty(input_dist: Distribution, node_std: float) -> Distribution:
    out_variance = input_dist.variance + node_std ** 2
    out_std = math.sqrt(out_variance) if out_variance > 0 else 0.0
    return Distribution(mean=input_dist.mean, std=out_std, name=input_dist.name)


def cascade_propagate(stages):
    results = []
    current_dist = Distribution(mean=0.0, std=stages[0][1], name=stages[0][0])

    for i, (name, std) in enumerate(stages):
        if i == 0:
            out_dist = Distribution(mean=current_dist.mean, std=current_dist.std, name=name)
            results.append((name, None, out_dist))
        else:
            in_dist = Distribution(mean=current_dist.mean, std=current_dist.std, name=stages[i - 1][0])
            out_dist = propagate_uncertainty(current_dist, std)
            out_dist.name = name
            results.append((name, in_dist, out_dist))
            current_dist = out_dist

    return results


def hierarchical_propagate(levels):
    results = []
    current_dist = Distribution(mean=0.0, std=levels[0][1], name=levels[0][0])

    for i, (name, std, amplification) in enumerate(levels):
        if i == 0:
            out_dist = Distribution(mean=current_dist.mean, std=current_dist.std, name=name)
            results.append((name, None, out_dist))
        else:
            in_dist = Distribution(mean=current_dist.mean, std=current_dist.std, name=levels[i - 1][0])
            amplified_std = current_dist.std * amplification
            combined_var = amplified_std ** 2 + std ** 2
            out_std = math.sqrt(combined_var) if combined_var > 0 else 0.0
            out_dist = Distribution(mean=current_dist.mean, std=out_std, name=name)
            results.append((name, in_dist, out_dist))
            current_dist = out_dist

    return results
