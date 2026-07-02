from pydantic import BaseModel , Field


class InformationPlan(BaseModel):
    required_information : list[str] = []
    
class SearchQueries(BaseModel):
    queries  : list[str] = []
    
# class InformartionRetrieval(BaseModel):
#     web_information : list[str]

class NoteExtractor(BaseModel):
    research_notes : list[str] = []
    
class CoverageCheck(BaseModel):
    is_sufficient: bool = Field(
        description="Whether the current research is sufficient to produce a comprehensive, accurate, and well-supported final report."
    )

    missing_information: list[str] = Field(
        description="Specific information that is still missing and should be researched further. Leave empty if the research is sufficient."
    )

    coverage_assessment: str = Field(
        description="A concise assessment explaining why the research is sufficient or what important gaps remain."
    )

    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence that the current research is sufficient. 1.0 means very confident, 0.0 means not confident."
    )