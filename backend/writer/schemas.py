
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class EvidenceGroup(BaseModel):
    model_config = ConfigDict(extra="forbid")

    requirement: str = Field(
        description=(
            "One required_information item copied exactly without rewriting."
        )
    )

    selected_note_ids: list[int] = Field(
        description=(
            "IDs of 3-5 strongest notes supporting this requirement. "
            "Use only provided note IDs. Prefer authoritative sources. "
            "Do not include duplicate or conflicting note IDs."
        )
    )

    conflicting_note_ids: list[int] = Field(
        default_factory=list,
        description=(
            "IDs of credible notes that make incompatible claims about the same "
            "entity, metric, period, or test setup as selected evidence. Keep the "
            "stronger note selected and place the contradictory note here. Leave "
            "empty when no conflict exists. Do not repeat selected_note_ids."
        )
    )


class EvidenceCuration(BaseModel):
    model_config = ConfigDict(extra="forbid")

    groups: list[EvidenceGroup] = Field(
        description=(
            "Exactly one evidence group for every required_information item."
        )
    )


class CitedContent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    content: str = Field(
        description=(
            "Report prose supported only by the curated evidence. Use inline "
            "citations in the form [N1], [N2], and so on."
        )
    )
    cited_note_ids: list[int] = Field(
        default_factory=list,
        description=(
            "IDs of curated notes supporting the content. Use only IDs supplied "
            "to the report writer and do not invent IDs."
        )
    )


class ReportSection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    requirement: str = Field(
        description=(
            "One required_information item copied exactly without rewriting."
        )
    )
    heading: str = Field(
        description="A concise report heading for this requirement."
    )
    analysis: CitedContent = Field(
        description=(
            "Evidence-based analysis for the requirement. State insufficient "
            "evidence explicitly instead of inventing information."
        )
    )


class InvestmentReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(
        description="A concise title derived from the research objective."
    )
    executive_summary: CitedContent = Field(
        description=(
            "A concise synthesis of the strongest findings, important conflicts, "
            "and material limitations."
        )
    )
    sections: list[ReportSection] = Field(
        description=(
            "Exactly one report section for every required_information item, in "
            "the same order as the input requirements."
        )
    )
    evidence_limitations: list[str] = Field(
        default_factory=list,
        description=(
            "Important gaps, weak evidence, or unresolved conflicts that limit "
            "the report's conclusions."
        )
    )


class CitationIssue(BaseModel):
    model_config = ConfigDict(extra="forbid")

    location: str = Field(
        description=(
            "Report location containing the issue, such as executive_summary or "
            "the exact section requirement."
        )
    )
    claim: str = Field(
        description="The exact or concise report claim affected by the issue."
    )
    cited_note_ids: list[int] = Field(
        default_factory=list,
        description="Note IDs connected to the issue."
    )
    issue_type: Literal[
        "invalid_citation",
        "citation_mismatch",
        "missing_citation",
        "unsupported_claim",
        "conflict_ignored",
        "requirement_mismatch",
    ] = Field(description="The category of citation or evidence problem.")
    explanation: str = Field(
        description=(
            "A concise explanation of why the claim or citation is invalid and "
            "what must be corrected."
        )
    )


class CitationValidation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    is_valid: bool = Field(
        description=(
            "True only when every factual claim is supported and all citation "
            "references are valid."
        )
    )
    issues: list[CitationIssue] = Field(
        default_factory=list,
        description=(
            "All citation, unsupported-claim, and ignored-conflict issues found "
            "in the report. Leave empty only when is_valid is true."
        )
    )
