from pydantic import BaseModel, ConfigDict, Field
from typing import Literal


class SearchQueries(BaseModel):
    model_config = ConfigDict(extra="forbid")

    queries: list[str] = Field(
        min_length=1,
        # Nodes enforce separate initial, follow-up, and total limits. Keeping
        # the tool schema permissive avoids provider rejection before trimming.
        description="""Specific web-searchable queries derived from required_information.
        Maximum 1 query per required_information item.
        Respect scope for time boundaries.
        Respect constraints for source preferences."""
    )


# class InformartionRetrieval(BaseModel):
#     web_information : list[str]

class NoteExtractor(BaseModel):
    model_config = ConfigDict(extra="forbid")

    research_notes: list[str] = Field(
        default_factory=list,
        # Groq rejects the entire tool call when the model exceeds a schema list
        # limit, so the node accepts the response and applies its own safe cap.
        description="Atomic factual notes extracted from one retrieved document.",
    )

# we fill these information for each notes we ectarcted from llm
class ResearchNote(BaseModel):
    content: str = Field(description="A single atomic factual finding extracted from the source.")
    source_url: str = Field(description="URL of the document this note was extracted from.")
    query: str = Field(description="Search query that retrieved this document.")

class RequiredInfoCoverage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    item: str = Field(
        description="Must match a required_information entry verbatim."
    )
    covered: bool = Field(
        description="Whether the research notes contain sufficient evidence for this item."
    )
    gap_note: str | None = Field(
        default=None,
        description="If not covered, a specific description of what's missing. Null if covered."
    )
    gap_reason: Literal["not_yet_searched", "likely_unavailable"] | None = Field(
        default=None,
        description=(
            "If not covered: 'not_yet_searched' if a better/different search query "
            "could plausibly find this. 'likely_unavailable' if this information "
            "probably doesn't exist in public sources (e.g. private company data, "
            "unpublished internal metrics). Null if covered."
        )
    )

class CoverageCheck(BaseModel):
    model_config = ConfigDict(extra="forbid")

    coverage: list[RequiredInfoCoverage] = Field(
        description=(
            "Coverage status for each required_information item. Must include "
            "exactly one entry per item, no more, no fewer, using the item text verbatim."
        )
    )
    coverage_assessment: str = Field(
        description="A concise 1-3 sentence summary explaining the overall research state."
    )
