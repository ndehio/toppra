import pytest
import numpy as np
import numpy.testing as npt
import cvxpy

import toppra
import toppra.constraint as constraint
from toppra.solverwrapper import cvxpyWrapper
from toppra.constants import TINY

@pytest.fixture(scope='class', params=['vel_accel'])
def pp_fixture(request):
    """ Velocity & Acceleration Path Constraint
    """
    dof = 6
    np.random.seed(1)  # Use the same randomly generated way pts
    way_pts = np.random.randn(4, dof) * 0.6
    N = 200
    pi = toppra.SplineInterpolator(np.linspace(0, 1, 4), way_pts)
    ss = np.linspace(0, 1, N + 1)
    # Velocity Constraint
    vlim_ = np.random.rand(dof) * 10 + 10
    vlim = np.vstack((-vlim_, vlim_)).T
    pc_vel = constraint.JointVelocityConstraint(vlim)
    # Acceleration Constraints
    alim_ = np.random.rand(dof) * 10 + 100
    alim = np.vstack((-alim_, alim_)).T
    pc_acc = constraint.JointAccelerationConstraint(alim)

    pcs = [pc_vel, pc_acc]
    yield pcs, pi, ss, vlim, alim

    print "\n [TearDown] Finish PP Fixture"

def test_basic_init(pp_fixture):
    constraints, path, path_discretization, vlim, alim = pp_fixture

    solver = cvxpyWrapper(constraints, path, path_discretization)

    i = 0
    # H = np.zeros((2, 2))
    H = np.eye(2)
    g = np.array([0, -1])
    xmin = -1
    xmax = 1
    xnext_min = 0
    xnext_max = 1

    result = solver.solve_stagewise_optim(i, H, g, xmin, xmax, xnext_min, xnext_max)

    # Compute actual result. This code "knows" the actual input constraints, so it is most likely
    # correct.
    ux = cvxpy.Variable(2)
    a, b, c, F, h, ubound, _ = solver.params[1]
    _, _, _, _, _, _, xbound = solver.params[0]
    cvxpy_constraints = [
        ux[0] <= ubound[i, 1],
        ux[0] >= ubound[i, 0],
        ux[1] <= xbound[i, 1],
        ux[1] >= xbound[i, 0],
        F[i] * (a[i] * ux[0] + b[i] * ux[1] + c[i]) <= h[i]
        ]
    objective = cvxpy.Minimize(cvxpy.quad_form(ux, H) * 0.5 + g * ux)
    problem = cvxpy.Problem(objective, cvxpy_constraints)
    problem.solve()
    actual = np.array(ux.value)

    # Assertion
    npt.assert_allclose(result, actual, atol=TINY)


