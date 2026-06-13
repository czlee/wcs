"""Unit tests for the Phase 3 divergence metrics.

These functions are the load-bearing core of the study, so they are pinned against
closed-form answers on tiny matrices (unanimous, fully reversed), an internal
algebraic identity (mean pairwise rho via W == direct scipy mean), and a fully
hand-computed worked example.
"""

import numpy as np
import pytest
from scipy.stats import spearmanr

import compute_metrics as cm


def make_doc(R):
    """Build a parsed-style doc from an m x n rank matrix (rows = judges)."""
    R = np.asarray(R)
    m, n = R.shape
    judges = [f"J{j}" for j in range(m)]
    competitors = [f"C{i}" for i in range(n)]
    rankings = {
        judges[j]: {competitors[i]: int(R[j, i]) for i in range(n)}
        for j in range(m)
    }
    return {"judges": judges, "competitors": competitors, "rankings": rankings}


# ---------------------------------------------------------------------------
# Closed-form anchors
# ---------------------------------------------------------------------------

def test_unanimous_panel_is_perfect_agreement():
    m, n = 4, 6
    R = np.tile(np.arange(1, n + 1), (m, 1))  # every judge identical
    out = cm.compute_metrics(make_doc(R))

    assert out["kendall_w"] == pytest.approx(1.0)
    assert out["mean_pairwise_rho"] == pytest.approx(1.0)
    assert out["mean_pairwise_tau"] == pytest.approx(1.0)
    assert out["tau_distance"] == pytest.approx(0.0)
    assert out["footrule_mean"] == pytest.approx(0.0)
    for col in ("overlap_at_3", "overlap_at_5", "jaccard_at_3", "jaccard_at_5"):
        assert out[col] == pytest.approx(1.0)
    for col in ("mean_abs_rank_dev_mean", "mean_abs_rank_dev_median", "sd_rank"):
        assert out[col] == pytest.approx(0.0)


def test_two_judges_fully_reversed():
    n = 5
    R = np.array([np.arange(1, n + 1), np.arange(n, 0, -1)])
    out = cm.compute_metrics(make_doc(R))

    assert out["mean_pairwise_rho"] == pytest.approx(-1.0)
    assert out["mean_pairwise_tau"] == pytest.approx(-1.0)
    assert out["tau_distance"] == pytest.approx(1.0)
    # W == (rho + 1) / 2 for m = 2; reversed => rho = -1 => W = 0.
    assert out["kendall_w"] == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# Algebraic identity: mean pairwise rho (via W) == direct scipy mean
# ---------------------------------------------------------------------------

def test_mean_pairwise_rho_matches_direct_spearman_mean():
    rng = np.random.default_rng(0)
    m, n = 5, 7
    R = np.array([rng.permutation(np.arange(1, n + 1)) for _ in range(m)])

    direct = np.mean([
        spearmanr(R[a], R[b]).statistic
        for a in range(m) for b in range(a + 1, m)
    ])
    assert cm.mean_pairwise_rho(R) == pytest.approx(direct)


# ---------------------------------------------------------------------------
# Fully worked example (m = 2, n = 4): A = 1,2,3,4 ; B = 1,2,4,3 (last two swapped)
# ---------------------------------------------------------------------------

def test_worked_example_two_judges_one_swap():
    R = np.array([[1, 2, 3, 4], [1, 2, 4, 3]])
    out = cm.compute_metrics(make_doc(R))

    # tau: 1 discordant of C(4,2)=6 pairs => tau = (5-1)/6 = 2/3.
    assert out["mean_pairwise_tau"] == pytest.approx(2 / 3)
    assert out["tau_distance"] == pytest.approx((1 - 2 / 3) / 2)
    # footrule: |Δ| = 0+0+1+1 = 2; max = floor(16/2) = 8 => 0.25.
    assert out["footrule_mean"] == pytest.approx(0.25)
    # Spearman rho = 1 - 6·2/(4·15) = 0.8.
    assert out["mean_pairwise_rho"] == pytest.approx(0.8)
    # top-3: A={C0,C1,C2}, B={C0,C1,C3} -> overlap 2/3, jaccard 2/4.
    assert out["overlap_at_3"] == pytest.approx(2 / 3)
    assert out["jaccard_at_3"] == pytest.approx(0.5)


# ---------------------------------------------------------------------------
# Top-N degeneracy (the approved "store literal 1.0 when N >= n" behaviour)
# ---------------------------------------------------------------------------

def test_top5_is_one_when_field_is_five_even_if_judges_disagree():
    n = 5
    R = np.array([[1, 2, 3, 4, 5], [5, 4, 3, 2, 1], [3, 1, 4, 5, 2]])
    out = cm.compute_metrics(make_doc(R))
    # Every judge's top-5 is the whole field => overlap/jaccard exactly 1.0.
    assert out["overlap_at_5"] == pytest.approx(1.0)
    assert out["jaccard_at_5"] == pytest.approx(1.0)


def test_top5_below_one_when_field_exceeds_five():
    # n = 6, two judges with different top-5 sets.
    R = np.array([[1, 2, 3, 4, 5, 6], [6, 1, 2, 3, 4, 5]])
    out = cm.compute_metrics(make_doc(R))
    assert out["overlap_at_5"] < 1.0
