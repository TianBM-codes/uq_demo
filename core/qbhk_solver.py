from dataclasses import dataclass, replace

import numpy as np


@dataclass
class QbhkParams:
    E: float = 2.0e9
    L1: float = 0.2
    L2: float = 0.6
    rho: float = 7850.0
    d: float = 0.02
    g: float = 9.81
    m_crank: float = 1.0
    m_slider: float = 0.5
    omega: float = np.pi
    F: float = -10.0
    T: float = 1.0
    dt: float = 0.01
    Ne: int = 4
    alpha_m: float = 0.2
    alpha_f: float = 0.4
    tol: float = 1e-6
    max_iter: int = 15

    def with_updates(self, **updates):
        return replace(self, **updates)


def solve_qbhk(params=None):
    p = params if isinstance(params, QbhkParams) else QbhkParams(**(params or {}))
    _validate_params(p)

    area = np.pi * (p.d / 2.0) ** 2
    inertia = np.pi * p.d ** 4 / 64.0
    node_count = p.Ne + 1
    element_length = p.L2 / p.Ne
    step_count = int(np.floor(p.T / p.dt))

    gamma = 0.5 + p.alpha_f - p.alpha_m
    beta = 0.25 * (1.0 + p.alpha_f - p.alpha_m) ** 2
    ancf_start = 3
    ancf_dof = 4 * node_count
    nq = 3 + ancf_dof

    q = np.zeros((nq, step_count + 1))
    qd = np.zeros_like(q)
    qdd = np.zeros_like(q)

    q[0, 0] = p.L1
    q[1, 0] = 0.0
    q[2, 0] = p.L1 + p.L2
    for i in range(node_count):
        xi = i * element_length
        idx = ancf_start + 4 * i
        q[idx, 0] = p.L1 + xi
        q[idx + 1, 0] = 0.0
        q[idx + 2, 0] = 1.0
        q[idx + 3, 0] = 0.0

    xB_dot0 = 0.0
    yB_dot0 = p.L1 * p.omega
    qd[0, 0] = xB_dot0
    qd[1, 0] = yB_dot0
    qd[2, 0] = 0.0
    for i in range(node_count):
        xi = i * element_length
        idx = ancf_start + 4 * i
        ratio = xi / p.L2
        qd[idx, 0] = (1.0 - ratio) * xB_dot0
        qd[idx + 1, 0] = (1.0 - ratio) * yB_dot0
        qd[idx + 2, 0] = -xB_dot0 / p.L2
        qd[idx + 3, 0] = -yB_dot0 / p.L2

    mass, gravity = _mass_and_gravity(p, area, nq, ancf_start, element_length)
    phi, phi_q = _constraints(q[:, 0], p.L1, 0.0, nq, p.Ne, ancf_start)
    constraint_acc0 = np.zeros(phi.shape[0])
    constraint_acc0[0] = -p.L1 * p.omega ** 2
    aug = _augmented_matrix(mass, phi_q)
    rhs = np.concatenate([gravity, constraint_acc0])
    acc_lambda = np.linalg.solve(aug, rhs)
    qdd[:, 0] = acc_lambda[:nq]
    lambdas = np.zeros((phi.shape[0], step_count + 1))
    lambdas[:, 0] = acc_lambda[nq:]

    converged = np.ones(step_count, dtype=bool)
    iterations = np.zeros(step_count, dtype=int)
    residual_norm = np.zeros(step_count)

    for step in range(step_count):
        time = (step + 1) * p.dt
        q_pred = q[:, step] + p.dt * qd[:, step] + p.dt ** 2 * (0.5 - beta) * qdd[:, step]
        qd_pred = qd[:, step] + p.dt * (1.0 - gamma) * qdd[:, step]

        q_iter = q_pred.copy()
        lambda_iter = np.zeros(lambdas.shape[0])
        residual = None
        qd_iter = qd_pred.copy()
        qdd_iter = np.zeros(nq)
        is_converged = False

        for iteration in range(1, p.max_iter + 1):
            qdd_iter = (q_iter - q_pred) / (beta * p.dt ** 2)
            qd_iter = qd_pred + gamma * p.dt * qdd_iter

            elastic = _elastic_force(q_iter, p.E, area, inertia, p.Ne, element_length, nq, ancf_start)
            phi, phi_q = _constraints(q_iter, p.L1, p.omega * time, nq, p.Ne, ancf_start)

            total_force = gravity - elastic
            total_force[2] += p.F
            residual_1 = mass @ qdd_iter + phi_q.T @ lambda_iter - total_force
            residual = np.concatenate([residual_1, phi])

            norm = float(np.linalg.norm(residual))
            if norm < p.tol:
                is_converged = True
                break

            tangent = _tangent_stiffness_fd(q_iter, p.E, area, inertia, p.Ne, element_length, nq, ancf_start)
            system = _augmented_matrix(mass / (beta * p.dt ** 2) + tangent, phi_q)
            delta = np.linalg.solve(system, -residual)
            q_iter += delta[:nq]
            lambda_iter += delta[nq:]

        converged[step] = is_converged
        iterations[step] = iteration
        residual_norm[step] = float(np.linalg.norm(residual)) if residual is not None else np.nan
        q[:, step + 1] = q_iter
        qd[:, step + 1] = qd_iter
        qdd[:, step + 1] = qdd_iter
        lambdas[:, step + 1] = lambda_iter

    t = np.arange(step_count + 1) * p.dt
    node_x = np.zeros((node_count, step_count + 1))
    node_y = np.zeros_like(node_x)
    for i in range(node_count):
        idx = ancf_start + 4 * i
        node_x[i, :] = q[idx, :]
        node_y[i, :] = q[idx + 1, :]

    slider_x = q[2, :]
    slider_v = qd[2, :]
    slider_a = qdd[2, :]
    return {
        "t": t,
        "q": q,
        "qd": qd,
        "qdd": qdd,
        "lambda": lambdas,
        "slider": {"x": slider_x, "v": slider_v, "a": slider_a},
        "crank_tip": {"x": q[0, :], "y": q[1, :]},
        "ancf": {"node_x": node_x, "node_y": node_y, "Ne": p.Ne, "Nn": node_count},
        "convergence": {
            "converged": converged,
            "iterations": iterations,
            "residual_norm": residual_norm,
            "all_converged": bool(np.all(converged)),
        },
        "summary": {
            "max_abs_x": float(np.max(np.abs(slider_x))),
            "max_abs_v": float(np.max(np.abs(slider_v))),
            "max_abs_a": float(np.max(np.abs(slider_a))),
            "final_x": float(slider_x[-1]),
        },
        "parameters": p,
    }


def _validate_params(p):
    positive = ["E", "L1", "L2", "rho", "d", "m_slider", "T", "dt"]
    for name in positive:
        if getattr(p, name) <= 0:
            raise ValueError(f"{name} must be positive")
    if p.g < 0:
        raise ValueError("g must be non-negative")
    if int(p.Ne) < 1:
        raise ValueError("Ne must be at least 1")


def _shape(x, length):
    xi = x / length
    s1 = 1.0 - 3.0 * xi ** 2 + 2.0 * xi ** 3
    s2 = length * (xi - 2.0 * xi ** 2 + xi ** 3)
    s3 = 3.0 * xi ** 2 - 2.0 * xi ** 3
    s4 = length * (-xi ** 2 + xi ** 3)
    matrix = np.zeros((2, 8))
    matrix[0, [0, 2, 4, 6]] = [s1, s2, s3, s4]
    matrix[1, [1, 3, 5, 7]] = [s1, s2, s3, s4]
    return matrix


def _shape_deriv(x, length):
    xi = x / length
    dxi = 1.0 / length
    ds1 = (-6.0 * xi + 6.0 * xi ** 2) * dxi
    ds2 = length * (1.0 - 4.0 * xi + 3.0 * xi ** 2) * dxi
    ds3 = (6.0 * xi - 6.0 * xi ** 2) * dxi
    ds4 = length * (-2.0 * xi + 3.0 * xi ** 2) * dxi
    matrix = np.zeros((2, 8))
    matrix[0, [0, 2, 4, 6]] = [ds1, ds2, ds3, ds4]
    matrix[1, [1, 3, 5, 7]] = [ds1, ds2, ds3, ds4]
    return matrix


def _shape_second_deriv(x, length):
    xi = x / length
    dxi2 = (1.0 / length) ** 2
    dds1 = (-6.0 + 12.0 * xi) * dxi2
    dds2 = length * (-4.0 + 6.0 * xi) * dxi2
    dds3 = (6.0 - 12.0 * xi) * dxi2
    dds4 = length * (-2.0 + 6.0 * xi) * dxi2
    matrix = np.zeros((2, 8))
    matrix[0, [0, 2, 4, 6]] = [dds1, dds2, dds3, dds4]
    matrix[1, [1, 3, 5, 7]] = [dds1, dds2, dds3, dds4]
    return matrix


def _mass_and_gravity(p, area, nq, start, length):
    mass = np.zeros((nq, nq))
    gravity = np.zeros(nq)
    mass[0, 0] = 1e-3
    mass[1, 1] = 1e-3
    mass[2, 2] = p.m_slider
    points = [-0.7745966692, 0.0, 0.7745966692]
    weights = [0.5555555556, 0.8888888889, 0.5555555556]
    for element in range(p.Ne):
        idx = start + 4 * element
        elem = slice(idx, idx + 8)
        local_mass = np.zeros((8, 8))
        local_gravity = np.zeros(8)
        for point, weight in zip(points, weights):
            local_x = (point + 1.0) * length / 2.0
            local_w = weight * length / 2.0
            shape = _shape(local_x, length)
            local_mass += local_w * p.rho * area * (shape.T @ shape)
            local_gravity += local_w * p.rho * area * (shape.T @ np.array([0.0, -p.g]))
        mass[elem, elem] += local_mass
        gravity[elem] += local_gravity
    return mass, gravity


def _elastic_force(q, elastic_modulus, area, inertia, element_count, length, nq, start):
    force = np.zeros(nq)
    points = [-0.7745966692, 0.0, 0.7745966692]
    weights = [0.5555555556, 0.8888888889, 0.5555555556]
    for element in range(element_count):
        idx = start + 4 * element
        elem = slice(idx, idx + 8)
        qe = q[elem]
        local = np.zeros(8)
        for point, weight in zip(points, weights):
            local_x = (point + 1.0) * length / 2.0
            local_w = weight * length / 2.0
            sx = _shape_deriv(local_x, length)
            sxx = _shape_second_deriv(local_x, length)
            rx = sx @ qe
            rxx = sxx @ qe
            strain = 0.5 * (float(rx.T @ rx) - 1.0)
            axial = elastic_modulus * area * strain * (sx.T @ rx)
            bending = elastic_modulus * inertia * (sxx.T @ rxx)
            local += local_w * (axial + bending)
        force[elem] += local
    return force


def _tangent_stiffness_fd(q, elastic_modulus, area, inertia, element_count, length, nq, start):
    tangent = np.zeros((nq, nq))
    step = 1e-7
    base = _elastic_force(q, elastic_modulus, area, inertia, element_count, length, nq, start)
    for col in range(start, nq):
        perturbed = q.copy()
        perturbed[col] += step
        force = _elastic_force(perturbed, elastic_modulus, area, inertia, element_count, length, nq, start)
        tangent[:, col] = (force - base) / step
    return tangent


def _constraints(q, crank_length, theta, nq, element_count, start):
    phi = np.zeros(6)
    phi_q = np.zeros((6, nq))
    x_b = crank_length * np.cos(theta)
    y_b = crank_length * np.sin(theta)

    phi[0] = q[0] - x_b
    phi[1] = q[1] - y_b
    phi_q[0, 0] = 1.0
    phi_q[1, 1] = 1.0

    first = start
    phi[2] = q[first] - q[0]
    phi[3] = q[first + 1] - q[1]
    phi_q[2, first] = 1.0
    phi_q[2, 0] = -1.0
    phi_q[3, first + 1] = 1.0
    phi_q[3, 1] = -1.0

    end = start + 4 * element_count
    phi[4] = q[end] - q[2]
    phi[5] = q[end + 1]
    phi_q[4, end] = 1.0
    phi_q[4, 2] = -1.0
    phi_q[5, end + 1] = 1.0
    return phi, phi_q


def _augmented_matrix(dynamic_matrix, phi_q):
    top = np.hstack([dynamic_matrix, phi_q.T])
    bottom = np.hstack([phi_q, np.zeros((phi_q.shape[0], phi_q.shape[0]))])
    return np.vstack([top, bottom])
