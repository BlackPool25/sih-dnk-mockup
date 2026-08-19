from app.models import CountryRate, HsCode, Lane, ProductCategory


def test_models_map_existing_table_names() -> None:
    assert ProductCategory.__tablename__ == "product_categories"
    assert HsCode.__tablename__ == "hs_codes"
    assert CountryRate.__tablename__ == "country_rates"
    assert Lane.__tablename__ == "lanes"


def test_lane_model_exposes_shipping_columns() -> None:
    columns = Lane.__table__.columns

    assert "country_iso2" in columns
    assert "lane" in columns
    assert "first_slab_g" in columns
    assert "first_slab_rate_minor" in columns
    assert "addl_slab_g" in columns
    assert "addl_slab_rate_minor" in columns
    assert "weight_cap_g" in columns
    assert "volume_free" in columns
    assert "divisor" in columns
    assert "conflicts" in columns


def test_country_rate_model_exposes_rate_columns() -> None:
    columns = CountryRate.__table__.columns

    assert "country_iso2" in columns
    assert "hs6" in columns
    assert "rate_type" in columns
    assert "rate_pct" in columns
    assert "amount_minor" in columns
    assert "threshold_minor" in columns
    assert "currency" in columns
    assert "basis" in columns


def test_config_models_expose_provenance_columns() -> None:
    for model in (ProductCategory, HsCode, CountryRate, Lane):
        columns = model.__table__.columns

        assert "source_url" in columns
        assert "source_level" in columns
        assert "confidence" in columns
        assert "is_estimate" in columns
        assert "effective_from" in columns
        assert "effective_to" in columns
        assert "verified_at" in columns