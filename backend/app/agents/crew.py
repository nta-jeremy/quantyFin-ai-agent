from crewai import Crew, Process
from app.agents.agents import create_agents
from app.agents.tasks import create_tasks, ExtractionResult
from pydantic import ValidationError

def run_extraction(title: str, content: str) -> ExtractionResult:
    # Khởi tạo Agents và Tasks mới cho mỗi cuộc gọi để tránh race condition/rò rỉ trạng thái
    extractor_agent, analyst_agent = create_agents()
    entities_task, sentiment_task = create_tasks(extractor_agent, analyst_agent)
    
    # Khởi tạo Crew với hai agent và hai task tuần tự
    crew = Crew(
        agents=[extractor_agent, analyst_agent],
        tasks=[entities_task, sentiment_task],
        process=Process.sequential,
        verbose=True
    )
    
    # Thực thi crew với dữ liệu đầu vào là tiêu đề và nội dung bài báo
    output = crew.kickoff(inputs={"title": title, "content": content})
    
    # Trích xuất kết quả Pydantic từ CrewOutput
    if hasattr(output, "pydantic") and output.pydantic is not None:
        try:
            # Đảm bảo validation hoạt động khi trích xuất pydantic trực tiếp
            if isinstance(output.pydantic, ExtractionResult):
                return output.pydantic
            return ExtractionResult(**output.pydantic.model_dump())
        except Exception:
            pass
    
    # Phép fallback trong trường hợp CrewOutput trả về json/dict
    if hasattr(output, "json_dict") and output.json_dict is not None:
        try:
            return ExtractionResult(**output.json_dict)
        except ValidationError as val_err:
            raise ValueError(f"Dữ liệu JSON từ CrewAI không hợp lệ cấu trúc ExtractionResult: {str(val_err)}")
        
    # Phép fallback phân tích từ chuỗi raw JSON
    import json
    try:
        data = json.loads(output.raw)
        return ExtractionResult(**data)
    except Exception as e:
        # Nếu không thể parse, ném lỗi để ingestion service bắt được và đánh dấu bài báo thất bại
        raise ValueError(f"Không thể trích xuất cấu trúc dữ liệu hợp lệ từ CrewAI. Lỗi: {str(e)}. Raw output: {output}")
