"""
MCL (Markov Cluster Algorithm) implementation.

Drop-in replacement for the `markov-clustering` package, compatible with
both scipy.sparse csr_matrix (legacy) and csr_array (modern) APIs.

Usage:
    from mcl import run_mcl, get_clusters
    result = run_mcl(adjacency_matrix)
    clusters = get_clusters(result)
"""

import numpy as np
from scipy.sparse import csc_matrix, issparse


def _normalize(matrix):
    """Column-wise L1 normalization."""
    col_sums = np.asarray(matrix.sum(axis=0)).flatten()
    col_sums[col_sums == 0] = 1.0
    if issparse(matrix):
        from scipy.sparse import diags

        inv = diags(1.0 / col_sums)
        return matrix @ inv
    return matrix / col_sums


def _inflate(matrix, power):
    """Element-wise power + column normalization."""
    if issparse(matrix):
        return _normalize(matrix.power(power))
    return _normalize(np.power(matrix, power))


def _expand(matrix, power):
    """Matrix power (repeated multiplication)."""
    if issparse(matrix):
        result = matrix.copy()
        for _ in range(power - 1):
            result = result @ matrix
        return result
    return np.linalg.matrix_power(matrix, power)


def _add_self_loops(matrix, loop_value):
    """Set diagonal to loop_value."""
    if issparse(matrix):
        m = matrix.tolil()
        m.setdiag(loop_value)
        return m.tocsc()
    m = matrix.copy()
    np.fill_diagonal(m, loop_value)
    return m


def _prune(matrix, threshold):
    """Remove elements below threshold; keep column max."""
    if issparse(matrix):
        m = matrix.tocsc()
        pruned = m.copy()
        pruned.data[pruned.data < threshold] = 0
        pruned.eliminate_zeros()
        # keep max value in each column
        for col in range(m.shape[1]):
            col_data = m.getcol(col)
            if col_data.nnz > 0:
                max_val = col_data.max()
                max_row = col_data.argmax()
                pruned[max_row, col] = max_val
        return pruned
    pruned = matrix.copy()
    pruned[pruned < threshold] = 0
    num_cols = matrix.shape[1]
    row_indices = matrix.argmax(axis=0).reshape((num_cols,))
    col_indices = np.arange(num_cols)
    pruned[row_indices, col_indices] = matrix[row_indices, col_indices]
    return pruned


def _converged(matrix1, matrix2, rtol=1e-5, atol=1e-8):
    """Check if two matrices are approximately equal."""
    if issparse(matrix1):
        diff = abs(matrix1 - matrix2)
        return diff.max() <= atol + rtol * abs(matrix2).max()
    return np.allclose(matrix1, matrix2, rtol=rtol, atol=atol)


def run_mcl(
    matrix,
    expansion=2,
    inflation=2,
    loop_value=1,
    iterations=100,
    pruning_threshold=0.001,
    pruning_frequency=1,
    convergence_check_frequency=1,
):
    """
    Perform MCL on the given similarity/adjacency matrix.

    Parameters
    ----------
    matrix : scipy.sparse matrix/array or numpy ndarray
        The similarity matrix to cluster.
    expansion : int
        Cluster expansion factor (matrix power). Must be > 1.
    inflation : float
        Cluster inflation factor (element-wise power). Must be > 1.
    loop_value : float
        Value for self-loops added before iteration.
    iterations : int
        Maximum number of iterations.
    pruning_threshold : float
        Elements below this value are pruned.
    pruning_frequency : int
        Prune every N iterations.
    convergence_check_frequency : int
        Check convergence every N iterations.

    Returns
    -------
    scipy.sparse.csc_matrix or numpy ndarray
        The final MCL matrix.
    """
    # Convert csr_array to csc_matrix for consistent behavior
    if issparse(matrix):
        matrix = csc_matrix(matrix)

    if loop_value > 0:
        matrix = _add_self_loops(matrix, loop_value)

    matrix = _normalize(matrix)

    for i in range(iterations):
        last_mat = matrix.copy()

        matrix = _expand(matrix, expansion)
        matrix = _inflate(matrix, inflation)

        if pruning_threshold > 0 and i % pruning_frequency == pruning_frequency - 1:
            matrix = _prune(matrix, pruning_threshold)

        if i % convergence_check_frequency == convergence_check_frequency - 1:
            if _converged(matrix, last_mat):
                break

    return matrix


def get_clusters(matrix):
    """
    Extract clusters from the MCL result matrix.

    Parameters
    ----------
    matrix : scipy.sparse matrix or numpy ndarray
        The matrix produced by run_mcl.

    Returns
    -------
    list of tuples
        Each tuple contains the indices of nodes in one cluster.
    """
    if not issparse(matrix):
        matrix = csc_matrix(matrix)
    else:
        matrix = csc_matrix(matrix)

    attractors = matrix.diagonal().nonzero()[0]

    clusters = set()
    for attractor in attractors:
        cluster = tuple(matrix.getrow(attractor).nonzero()[1].tolist())
        clusters.add(cluster)

    return sorted(list(clusters))
