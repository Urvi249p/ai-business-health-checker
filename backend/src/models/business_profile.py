"""
models/business_profile.py — Structured Business Profile model.

Replaces the free-text `business_description` string with a validated,
structured payload that the API receives and the audit pipeline consumes.
"""
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class BusinessType(str, Enum):
    """The primary category of the business."""
    RETAIL = "Retail"
    RESTAURANT = "Restaurant"
    MANUFACTURING = "Manufacturing"
    SERVICE = "Service"
    FREELANCER = "Freelancer"
    AGENCY = "Agency"
    STARTUP = "Startup"
    HEALTHCARE = "Healthcare"
    EDUCATION = "Education"
    OTHER = "Other"


class CustomerType(str, Enum):
    """Describes who the business primarily sells to."""
    B2B = "B2B"
    B2C = "B2C"
    BOTH = "Both"


class GoalType(str, Enum):
    """Predefined strategic goals the business may want to pursue."""
    INCREASE_REVENUE = "Increase Revenue"
    REDUCE_COSTS = "Reduce Costs"
    IMPROVE_MARKETING = "Improve Marketing"
    HIRE_EMPLOYEES = "Hire Employees"
    EXPAND_BUSINESS = "Expand Business"
    IMPROVE_CUSTOMER_RETENTION = "Improve Customer Retention"
    GO_DIGITAL = "Go Digital"
    EXPORT_PRODUCTS = "Export Products"
    OTHER = "Other"


# ---------------------------------------------------------------------------
# Business Profile model
# ---------------------------------------------------------------------------

class BusinessProfile(BaseModel):
    """Structured profile of a business submitted for an AI health-check audit."""

    business_type: BusinessType = Field(
        ...,
        description="Primary category of the business.",
        examples=["Retail", "Startup"],
    )

    years_in_business: int = Field(
        ...,
        ge=0,
        description="Number of years the business has been operating (0 for brand-new).",
        examples=[4],
    )

    team_size: int = Field(
        ...,
        gt=0,
        description="Total number of people in the team (must be at least 1).",
        examples=[8],
    )

    customer_type: CustomerType = Field(
        ...,
        description="Who the business primarily sells to.",
        examples=["B2C"],
    )

    customer_sources: List[str] = Field(
        ...,
        min_length=1,
        description="Channels through which customers are acquired (e.g. Walk-ins, Instagram).",
        examples=[["Walk-ins", "Instagram"]],
    )

    biggest_challenges: List[str] = Field(
        ...,
        min_length=1,
        description="Key challenges the business is currently facing.",
        examples=[["Low repeat customers", "Pricing"]],
    )

    goals: List[GoalType] = Field(
        ...,
        min_length=1,
        description="Strategic goals the business wants to achieve.",
        examples=[["Increase Revenue", "Improve Marketing"]],
    )

    additional_notes: Optional[str] = Field(
        default=None,
        description="Any extra context or notes about the business (optional).",
        examples=["We make custom cakes."],
    )

    # -----------------------------------------------------------------------
    # Validators
    # -----------------------------------------------------------------------

    @field_validator("customer_sources", "biggest_challenges", mode="before")
    @classmethod
    def _reject_empty_strings_in_list(cls, values: list) -> list:
        """Ensure list items are non-empty strings after stripping whitespace."""
        cleaned = [v.strip() if isinstance(v, str) else v for v in values]
        if any(not v for v in cleaned):
            raise ValueError("List items must not be empty strings.")
        return cleaned

    @field_validator("additional_notes", mode="before")
    @classmethod
    def _strip_additional_notes(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            return v if v else None
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "business_type": "Retail",
                    "years_in_business": 4,
                    "team_size": 8,
                    "customer_type": "B2C",
                    "customer_sources": ["Walk-ins", "Instagram"],
                    "biggest_challenges": ["Low repeat customers", "Pricing"],
                    "goals": ["Increase Revenue", "Improve Marketing"],
                    "additional_notes": "We make custom cakes.",
                }
            ]
        }
    }
