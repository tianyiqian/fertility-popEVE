from fertility_popeve.utils.config import load_config


def test_config_loads_required_keys():
    cfg = load_config()
    assert cfg["project"]["name"] == "fertility_popEVE"
    assert "paths" in cfg
    assert "vep" in cfg
    assert "gp_training" in cfg


def test_config_paths_are_strings():
    cfg = load_config()
    for key in ("reference", "bed", "logs", "outputs"):
        assert isinstance(cfg["paths"][key], str), f"paths.{key} should be str"


def test_config_gp_training_defaults():
    cfg = load_config()
    gp = cfg["gp_training"]
    assert gp["epochs"] == 6000
    assert gp["min_candidates"] == 100
    assert gp["min_observed_variants"] == 10
    assert gp["training_frac"] == 1.0
