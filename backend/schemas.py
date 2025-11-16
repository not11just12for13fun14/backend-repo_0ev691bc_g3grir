from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

# Each Pydantic model represents a collection (lowercased name)

class Lead(BaseModel):
    email: str = Field(..., description="Lead email")
    plan: Optional[str] = Field(None, description="Interested plan")
    source: Optional[str] = Field(None, description="Source of lead")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
