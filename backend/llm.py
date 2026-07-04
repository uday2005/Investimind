import os

from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()


SCOUT_MODEL = os.getenv(
    "GROQ_SCOUT_MODEL",
    "meta-llama/llama-4-scout-17b-16e-instruct",
)
RELIABLE_MODEL = os.getenv(
    "GROQ_RELIABLE_MODEL",
    "llama-3.3-70b-versatile",
)


def build_groq_llm(model: str) -> ChatGroq:
    return ChatGroq(
        model=model,
        temperature=0,
        api_key=os.getenv("GROQ_API_KEY"),
    )


# Cheaper / higher-TPM model. Use where the schema is simple and the node can
# tolerate slightly weaker reasoning.
query_generator_llm = build_groq_llm(SCOUT_MODEL)
follow_up_query_generator_llm = build_groq_llm(SCOUT_MODEL)
note_extractor_llm = build_groq_llm(SCOUT_MODEL)
coverage_checker_llm = build_groq_llm(SCOUT_MODEL)
evidence_curator_llm = build_groq_llm(RELIABLE_MODEL)

# Keep the 70B model only where bad structured output or weak reasoning is most
# expensive for the product experience.
clarification_llm = build_groq_llm(RELIABLE_MODEL)
research_brief_llm = build_groq_llm(RELIABLE_MODEL)
report_writer_llm = build_groq_llm(RELIABLE_MODEL)
citation_validator_llm = build_groq_llm(RELIABLE_MODEL)

# Backward-compatible default for quick experiments and older imports.
llm = query_generator_llm
