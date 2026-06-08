import pytest
from unittest.mock import MagicMock
from app.agents.crew import run_extraction
from app.agents.tasks import ExtractionResult

def test_run_extraction_pydantic_output(monkeypatch):
    # Giả lập kết quả trả về từ Crew.kickoff có thuộc tính pydantic
    mock_result = MagicMock()
    mock_result.pydantic = ExtractionResult(
        sentiment_score=0.85,
        entities=[
            {"name": "FPT", "type": "TICKER", "description": "Công ty Cổ phần FPT"},
            {"name": "Nguyễn Văn A", "type": "PERSON", "description": "Chủ tịch HĐQT"}
        ],
        relationships=[
            {"source": "Nguyễn Văn A", "target": "FPT", "relation_type": "LEADER_OF", "description": "Chủ tịch của FPT"}
        ]
    )
    
    from crewai import Crew
    monkeypatch.setattr(Crew, "kickoff", lambda self, inputs: mock_result)
    
    # Thực hiện gọi hàm run_extraction
    res = run_extraction(title="FPT công bố kết quả kinh doanh", content="Nguyễn Văn A báo cáo doanh thu tăng trưởng.")
    
    # Kiểm tra kết quả bóc tách
    assert res.sentiment_score == 0.85
    assert len(res.entities) == 2
    assert res.entities[0].name == "FPT"
    assert res.entities[0].type == "TICKER"
    assert res.relationships[0].relation_type == "LEADER_OF"

def test_run_extraction_json_dict_fallback(monkeypatch):
    # Giả lập kết quả trả về từ Crew.kickoff có thuộc tính json_dict thay vì pydantic
    mock_result = MagicMock()
    mock_result.pydantic = None
    mock_result.json_dict = {
        "sentiment_score": -0.5,
        "entities": [
            {"name": "VIC", "type": "TICKER", "description": "Tập đoàn Vingroup"}
        ],
        "relationships": []
    }
    
    from crewai import Crew
    monkeypatch.setattr(Crew, "kickoff", lambda self, inputs: mock_result)
    
    res = run_extraction(title="Tin tiêu cực", content=" VIC sụt giảm doanh số.")
    
    assert res.sentiment_score == -0.5
    assert len(res.entities) == 1
    assert res.entities[0].name == "VIC"
    assert len(res.relationships) == 0
