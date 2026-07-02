from pydantic import BaseModel , Field

class ClarifyWithUser(BaseModel):
    need_clarification: bool = Field(
        description="Whether additional user input is required before research can begin."
    )

    clarification_question: str | None = Field(
        default=None,
        description="A single concise question to resolve the ambiguity. Leave null when no clarification is needed."
    )

    reasoning: str = Field(
        description="Brief explanation for the decision. Used for debugging and evaluation."
    )

class ResearchBrief(BaseModel):
    objective: str = Field(
        description="One concise sentence describing the core research goal."
    )
    scope: str = Field(
        description="Defines the boundaries of the research including entities, industries, geography and time period."
    )
    constraints: list[str] = Field(
        description="Hard requirements the Research Agent must follow. Maximum 5 concise items."
    )
    required_information: list[str] = Field(
        description="Specific evidence that must be collected. Each item should be independently searchable. Maximum 8 items."
    )
