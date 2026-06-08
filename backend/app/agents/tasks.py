from pydantic import BaseModel, Field
from typing import List, Optional
from crewai import Task
from app.agents.agents import entity_extractor_agent, sentiment_analyst_agent

class ExtractedEntity(BaseModel):
    name: str = Field(description="Tên của thực thể (ví dụ: tên công ty, mã cổ phiếu, tên lãnh đạo, sự kiện vĩ mô...)")
    type: str = Field(description="Loại thực thể (ví dụ: COMPANY, TICKER, PERSON, MACRO, EVENT)")
    description: Optional[str] = Field(None, description="Mô tả tóm tắt vai trò hoặc thông tin về thực thể trong ngữ cảnh bài báo")

class ExtractedRelationship(BaseModel):
    source: str = Field(description="Tên thực thể bắt đầu mối quan hệ")
    target: str = Field(description="Tên thực thể kết thúc mối quan hệ")
    relation_type: str = Field(description="Loại quan hệ (ví dụ: LEADER_OF, ACQUIRES, PARTNER_OF, COMPETITOR_OF, INFLUENCES...)")
    description: Optional[str] = Field(None, description="Mô tả chi tiết hơn về mối quan hệ này")

class ExtractionResult(BaseModel):
    sentiment_score: float = Field(ge=-1.0, le=1.0, description="Điểm số cảm xúc tổng quan đối với (các) mã cổ phiếu hoặc công ty được nhắc đến, từ -1.0 (rất tiêu cực) đến 1.0 (rất tích cực).")
    entities: List[ExtractedEntity] = Field(default=[], description="Danh sách các thực thể được trích xuất từ bài báo")
    relationships: List[ExtractedRelationship] = Field(default=[], description="Danh sách các mối quan hệ được trích xuất từ bài báo")

def create_tasks(entity_extractor_agent, sentiment_analyst_agent) -> tuple[Task, Task]:
    extract_entities_task = Task(
        description=(
            "Phân tích bài báo tài chính sau và trích xuất tất cả các thực thể quan trọng cùng mối quan hệ giữa chúng.\n"
            "Tiêu đề: {title}\n"
            "Nội dung: {content}"
        ),
        expected_output="Danh sách các thực thể (COMPANY, TICKER, PERSON, MACRO, EVENT) và các mối quan hệ giữa chúng.",
        agent=entity_extractor_agent
    )

    analyze_sentiment_task = Task(
        description=(
            "Đọc bài báo và các thực thể/quan hệ đã được trích xuất:\n"
            "Tiêu đề: {title}\n"
            "Nội dung: {content}\n"
            "Nhiệm vụ của bạn là đánh giá và chấm điểm cảm xúc của tin tức đối với các thực thể liên quan (đặc biệt là các mã ticker chứng khoán) từ -1.0 đến 1.0.\n"
            "Tổng hợp tất cả các thông tin (thực thể, quan hệ, điểm cảm xúc) vào cấu trúc đầu ra chuẩn."
        ),
        expected_output="Đầu ra cấu trúc ExtractionResult chứa điểm cảm xúc, thực thể và các mối quan hệ.",
        agent=sentiment_analyst_agent,
        context=[extract_entities_task],
        output_pydantic=ExtractionResult
    )
    return extract_entities_task, analyze_sentiment_task

# For backwards compatibility with existing references/tests
extract_entities_task, analyze_sentiment_task = create_tasks(entity_extractor_agent, sentiment_analyst_agent)
