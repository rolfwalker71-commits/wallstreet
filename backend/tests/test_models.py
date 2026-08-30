from app.models import AgentLog, Asset, Portfolio, Recommendation, Transaction


def test_model_tablenames() -> None:
    assert Asset.__tablename__ == "assets"
    assert Recommendation.__tablename__ == "recommendations"
    assert AgentLog.__tablename__ == "agent_logs"
    assert Portfolio.__tablename__ == "portfolios"
    assert Transaction.__tablename__ == "transactions"