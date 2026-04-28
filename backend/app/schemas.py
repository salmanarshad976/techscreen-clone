from pydantic import BaseModel, EmailStr
from typing import Optional


class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: str


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class SearchRequest(BaseModel):
    niche: str
    location: str


class BulkSearchRequest(BaseModel):
    niche: str
    cities: list[str]


class NicheScanRequest(BaseModel):
    niches: list[str]
    cities: list[str]
    service_type: str = "seo_wp"


class SerpRequest(BaseModel):
    query: str
    location: str = "United States"


class PitchRequest(BaseModel):
    lead_id: int
    tone: str = "professional"


class PipelineUpdateRequest(BaseModel):
    lead_id: int
    stage: str


class ProposalCreateRequest(BaseModel):
    lead_id: Optional[int] = None
    title: str
    client_name: str


class CampaignCreateRequest(BaseModel):
    name: str
    niche: Optional[str] = None
    location: Optional[str] = None


class TemplateCreateRequest(BaseModel):
    name: str
    subject: str
    body: str
    category: str = "pitch"


class CaseStudyCreateRequest(BaseModel):
    title: str
    client_name: str
    description: str
    before_metrics: dict = {}
    after_metrics: dict = {}


class CompetitorCompareRequest(BaseModel):
    url1: str
    url2: str


class NapAuditRequest(BaseModel):
    business_name: str
    address: str
    phone: str


class BacklinkRequest(BaseModel):
    domain: str


class RankTrackRequest(BaseModel):
    domain: str
    keywords: list[str]
    location: str = "United States"


class RoiCalculatorRequest(BaseModel):
    monthly_revenue: float
    current_traffic: int
    projected_traffic_increase: float
    conversion_rate: float


class WebsiteGenerateRequest(BaseModel):
    business_name: str
    niche: str
    location: str
    phone: Optional[str] = None
    description: Optional[str] = None
