from crewai import Agent
from app.agents.gateway import llm

from crewai import Agent
from app.agents.gateway import llm

def create_agents() -> tuple[Agent, Agent]:
    entity_extractor_agent = Agent(
        role="Entity Extractor",
        goal="Đọc tin tức tài chính và bóc tách các thực thể vĩ mô, công ty, mã ticker chứng khoán, và lãnh đạo doanh nghiệp.",
        backstory="Bạn là một chuyên gia phân tích dữ liệu tài chính hàng đầu. Nhiệm vụ của bạn là đọc kỹ các bài báo tài chính, tin tức doanh nghiệp và trích xuất tất cả các thực thể quan trọng bao gồm: tên công ty, mã cổ phiếu (ticker), tên ban lãnh đạo, và các yếu tố kinh tế vĩ mô có ảnh hưởng.",
        llm=llm,
        verbose=True
    )

    sentiment_analyst_agent = Agent(
        role="Sentiment Analyst",
        goal="Phân tích cảm xúc của tin tức đối với các mã cổ phiếu hoặc công ty được nhắc đến và chấm điểm từ -1.0 (rất tiêu cực) đến 1.0 (rất tích cực).",
        backstory="Bạn là một nhà phân tích thị trường tài chính kỳ cựu với khả năng đọc vị tâm lý thị trường cực tốt. Nhiệm vụ của bạn là đánh giá xem tin tức có tác động tích cực hay tiêu cực như thế nào đến công ty hoặc cổ phiếu tương ứng, đồng thời chấm điểm cảm xúc chính xác từ -1.0 đến 1.0.",
        llm=llm,
        verbose=True
    )
    return entity_extractor_agent, sentiment_analyst_agent

# For backwards compatibility with existing references/tests
entity_extractor_agent, sentiment_analyst_agent = create_agents()
