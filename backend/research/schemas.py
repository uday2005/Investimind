from pydantic import BaseModel


class InformationPlan(BaseModel):
    required_information : list[str] = []
    
class SearchQueries(BaseModel):
    queries  : list[str] = []
    
# class InformartionRetrieval(BaseModel):
#     web_information : list[str]

class NoteExtractor(BaseModel):
    research_notes : list[str] = []
    
class CovergaeChecker(BaseModel):
    research_outpt : list[str] = []