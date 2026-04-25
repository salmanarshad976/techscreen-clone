import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from .db import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    plan = Column(String, default="free")  # free, pro, max
    searches_used = Column(Integer, default=0)
    searches_limit = Column(Integer, default=5)
    saved_leads_count = Column(Integer, default=0)
    pitches_sent = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    leads = relationship("Lead", back_populates="user")
    searches = relationship("Search", back_populates="user")
    proposals = relationship("Proposal", back_populates="user")
    campaigns = relationship("Campaign", back_populates="user")
    templates = relationship("Template", back_populates="user")
    case_studies = relationship("CaseStudy", back_populates="user")


class Search(Base):
    __tablename__ = "searches"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    niche = Column(String, nullable=False)
    location = Column(String, nullable=False)
    result_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="searches")
    results = relationship("Lead", back_populates="search")


class Lead(Base):
    __tablename__ = "leads"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    search_id = Column(Integer, ForeignKey("searches.id"), nullable=True)
    business_name = Column(String, nullable=False)
    address = Column(String)
    city = Column(String)
    state = Column(String)
    phone = Column(String)
    website = Column(String)
    rating = Column(Float)
    review_count = Column(Integer, default=0)
    opportunity_score = Column(Integer, default=50)
    has_website = Column(Boolean, default=True)
    has_ssl = Column(Boolean, default=True)
    page_speed = Column(Float, nullable=True)
    needs = Column(JSON, default=list)
    pitch_suggestion = Column(String)
    niche = Column(String)
    location = Column(String)
    saved = Column(Boolean, default=False)
    pipeline_stage = Column(String, default="new")  # new, contacted, replied, proposal, closed
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="leads")
    search = relationship("Search", back_populates="results")


class Proposal(Base):
    __tablename__ = "proposals"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=True)
    title = Column(String, nullable=False)
    client_name = Column(String)
    content = Column(Text)
    status = Column(String, default="draft")  # draft, sent, accepted, declined
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="proposals")


class Campaign(Base):
    __tablename__ = "campaigns"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String, nullable=False)
    status = Column(String, default="draft")  # draft, active, paused, completed
    total_leads = Column(Integer, default=0)
    emails_sent = Column(Integer, default=0)
    replies = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="campaigns")


class Template(Base):
    __tablename__ = "templates"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String, nullable=False)
    subject = Column(String)
    body = Column(Text)
    category = Column(String, default="pitch")  # pitch, followup, proposal, review
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="templates")


class CaseStudy(Base):
    __tablename__ = "case_studies"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String, nullable=False)
    client_name = Column(String)
    before_metrics = Column(JSON, default=dict)
    after_metrics = Column(JSON, default=dict)
    description = Column(Text)
    published = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="case_studies")
