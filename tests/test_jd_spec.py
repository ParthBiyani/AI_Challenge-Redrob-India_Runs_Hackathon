from redrob_ranker.jd_spec import JDSpec


def test_loads_experience_band():
    spec = JDSpec.load()
    band = spec.experience_band
    assert band["min"] == 5
    assert band["max"] == 9
    assert band["ideal_min"] <= band["ideal_max"]


def test_must_haves_present():
    spec = JDSpec.load()
    assert "embeddings_retrieval" in spec.must_haves
    assert "evaluation_frameworks" in spec.must_haves


def test_company_lists():
    spec = JDSpec.load()
    assert "infosys" in spec.consulting_companies
    assert "swiggy" in spec.product_companies
    assert spec.consulting_companies.isdisjoint(spec.product_companies)


def test_disqualifiers_cover_key_rules():
    spec = JDSpec.load()
    for name in ("research_only_no_production", "consulting_only_career", "cv_speech_robotics_only"):
        assert name in spec.disqualifiers
