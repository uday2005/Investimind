from pydantic import BaseModel, ConfigDict, Field

class ClarifyWithUser(BaseModel):
    model_config = ConfigDict(extra="forbid")

    need_clarification: bool = Field(
        description="Whether additional user input is required before research can begin."
    )

    clarification_question: str | None = Field(
        default=None,
        description="A single concise question to resolve the ambiguity. Leave null when no clarification is needed."
    )


class ResearchBrief(BaseModel):
    model_config = ConfigDict(extra="forbid")

    objective: str = Field(
        description="One concise sentence describing the core research goal."
    )
    scope: str = Field(
        description="Defines the boundaries of the research including entities, industries, geography and time period."
    )
    constraints: list[str] = Field(
        default_factory=list,
        max_length=5,
        description="Hard requirements the Research Agent must follow. Maximum 5 concise items."
    )
    required_information: list[str] = Field(
        min_length=1,
        max_length=8,
        description="Specific evidence that must be collected. Each item should be independently searchable. Maximum 8 items."
    )
