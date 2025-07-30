from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field

class AnalysisRequest(BaseModel):
    query: str = Field(..., description="The analysis query or instruction")
    file_path: Optional[str] = Field(None, description="Path to a data file to analyze")
    code: Optional[str] = Field(None, description="Custom Python code to execute")
    thread_id: Optional[str] = Field("default", description="Thread ID for conversation continuity")
    
    
class Message(BaseModel):
    role: str
    content: str

class AnalysisResponse(BaseModel):
    result: Any = Field(..., description="The result of the analysis")
    logs: Optional[str] = Field(None, description="Execution logs")
    messages: List[Message] = Field(default_factory=list, description="Conversation messages")
    

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None