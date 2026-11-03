from pydantic import BaseModel, Field

class TestCaseCreate(BaseModel):
    title: str = Field(min_length=3, max_length=120)
    question: str = Field(min_length=3)
    expected_answer: str = Field(min_length=3)
    reference_context: str = Field(min_length=3)
    category: str = "general"

class RunRequest(BaseModel):
    test_case_ids: list[int] | None = None

class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)

class RegressionRequest(BaseModel):
    baseline_run_id: int
    comparison_run_id: int
