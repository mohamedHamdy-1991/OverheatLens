"""Weather compatibility guard tests (S-08: TM59:2026 minimum = DSY1 2050s HIGH50)."""

from __future__ import annotations

from overheatlens.epw import check_tm59_2017_weather, check_tm59_2026_weather


def test_minimum_requirement_is_compatible():
    v = check_tm59_2026_weather("LEEDS_14_DSY1_2050s_HIGH50_CIBSE_v1.1.epw")
    assert v["status"] == "compatible"
    assert v["detected"] == {"dsy_type": "DSY1", "epoch": "2050s",
                             "percentile_label": "HIGH50"}


def test_more_extreme_dsy_is_research_only():
    v = check_tm59_2026_weather("LEEDS_14_DSY3_2050s_HIGH50_CIBSE_v1.1.epw")
    assert v["status"] == "research_only"
    assert "DSY3" in v["reason"]


def test_other_epoch_is_research_only():
    v = check_tm59_2026_weather("LEEDS_14_DSY1_2080s_HIGH50_CIBSE_v1.1.epw")
    assert v["status"] == "research_only"
    assert "2080s" in v["reason"]


def test_other_percentile_is_research_only():
    v = check_tm59_2026_weather("LEEDS_14_DSY1_2050s_HIGH10_CIBSE_v1.1.epw")
    assert v["status"] == "research_only"
    assert "HIGH10" in v["reason"]


def test_untraceable_filename_is_unknown():
    v = check_tm59_2026_weather("my_site_2023.epw")
    assert v["status"] == "unknown"
    assert "not machine-verifiable" in v["reason"]


def test_legacy_2026_style_tokens_without_v11_is_research_only():
    """A file carrying all three tokens but no v1.1 marker cannot be confirmed as
    the required CIBSE 2025 release."""
    v = check_tm59_2026_weather("LEEDS_DSY1_2050s_HIGH50.epw")
    assert v["status"] == "research_only"
    assert "v1.1" in v["reason"]


# ---- TM59:2017 requirement (S-02 §3.2: DSY1 2020s High50) ----------------------

def test_tm59_2017_minimum_legacy_naming():
    v = check_tm59_2017_weather("Leeds_DSY1_2020High50_.epw")
    assert v["status"] == "compatible"
    assert v["detected"]["dsy_type"] == "DSY1"
    assert v["detected"]["epoch"] == "2020s"
    assert v["detected"]["scenario_label"] == "HIGH"
    assert v["detected"]["percentile_label"] == "50"


def test_tm59_2017_future_epoch_research_only():
    v = check_tm59_2017_weather("Leeds_DSY1_2050High50_.epw")
    assert v["status"] == "research_only"
    assert "2050s" in v["reason"]


def test_tm59_2017_dsy3_research_only():
    v = check_tm59_2017_weather("Leeds_DSY3_2020High50_.epw")
    assert v["status"] == "research_only"
    assert "DSY3" in v["reason"]


def test_tm59_2017_other_percentile_research_only():
    v = check_tm59_2017_weather("Leeds_DSY1_2020High10_.epw")
    assert v["status"] == "research_only"
    assert "10" in v["reason"]


def test_tm59_2017_untraceable_unknown():
    v = check_tm59_2017_weather("my_site_2023.epw")
    assert v["status"] == "unknown"
