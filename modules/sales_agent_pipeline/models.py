from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum

class LeadStatus(str, Enum):
    QUALIFIED = "QUALIFIED"
    UNQUALIFIED = "UNQUALIFIED"
    NURTURING_REQUIRED = "NURTURING_REQUIRED"
    PENDING = "PENDING"

class ExtractedLeadInfo(BaseModel):
    """Holds structured information extracted from the conversation by the Extractor Agent."""
    customer_name: Optional[str] = Field(default=None, description="The identified name of the customer.")
    company_name: Optional[str] = Field(default=None, description="The business or company name, if applicable.")
    budget_range: Optional[str] = Field(default=None, description="Financial capacity or budget explicitly mentioned or inferred.")
    primary_pain_point: Optional[str] = Field(default=None, description="The core problem or need the customer is trying to solve.")
    timeline: Optional[str] = Field(default=None, description="When the customer intends to purchase or implement the solution.")

class LeadScoreMetadata(BaseModel):
    """Detailed multi-criteria analysis produced by the Scorer Agent."""
    budget_fit: int = Field(..., ge=0, le=10, description="Score from 0-10 on budget alignment.")
    intent_strength: int = Field(..., ge=0, le=10, description="Score from 0-10 on urgency and intent.")
    authority_level: int = Field(..., ge=0, le=10, description="Score from 0-10 on whether the contact is a decision maker.")
    justification: str = Field(..., description="Technical rationale behind the evaluation scores.")

class PipelineState(BaseModel):
    """The global session state passed across the multi-agent pipeline workflow."""
    session_id: str = Field(..., description="Unique tracking identifier for the B2B sales call or chat session.")
    conversation_history: List[Dict[str, str]] = Field(default_factory=list, description="Raw append-only log of the conversation.")
    extracted_data: ExtractedLeadInfo = Field(default_factory=ExtractedLeadInfo, description="Accumulated structured lead indicators.")
    evaluation: Optional[LeadScoreMetadata] = Field(default=None, description="Final rating assigned by the qualification agent.")
    status: LeadStatus = Field(default=LeadStatus.PENDING, description="Current operational state of the lead.")