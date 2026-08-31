from app.services.title_search import fold_query, query_variants, score_hit, _skip_quote


def test_umlaut_variants_include_ae() -> None:
    variants = query_variants("Dätwyler")
    assert "Dätwyler" in variants
    assert "Daetwyler" in variants
    assert fold_query("Dätwyler") == "daetwyler"


def test_skip_fx_and_futures() -> None:
    assert _skip_quote("CURRENCY", "EURUSD=X")
    assert _skip_quote("FUTURE", "ES=F")
    assert _skip_quote("INDEX", "^SSMI")
    assert not _skip_quote("EQUITY", "DAE.SW")


def test_swiss_listing_ranks_higher() -> None:
    swiss = score_hit(
        symbol="DAE.SW",
        name="Dätwyler Holding AG",
        exchange="EBS",
        query="Dätwyler",
        swiss_buyable=True,
    )
    london = score_hit(
        symbol="0QNJ.IL",
        name="Dätwyler Holding AG",
        exchange="IOB",
        query="Dätwyler",
        swiss_buyable=True,
    )
    assert swiss > london
