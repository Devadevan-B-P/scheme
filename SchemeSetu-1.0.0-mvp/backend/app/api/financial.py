"""
Financial Router — API for subsidy, margin money, and EMI simulations.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.models.contracts import FinancialSummary
from app.services.scheme_service import SchemeService
from app.engine.financial import generate_financial_summary

router = APIRouter(prefix="/financial", tags=["Financial"])


class FinancialSimulationRequest(BaseModel):
    scheme_id: str
    loan_amount: Optional[float] = Field(None, ge=0, description="Requested project / loan cost")
    tenure_months: Optional[int] = Field(None, gt=0, description="Requested repayment tenure in months")


@router.post("/simulate", response_model=FinancialSummary)
async def simulate_financials(request: FinancialSimulationRequest):
    """
    Simulate financial breakdown for an eligible scheme:
    returns exact subsidy amount, required margin money, net bank loan, and EMI schedule.
    """
    scheme = await SchemeService.get_scheme_by_id(request.scheme_id)
    if not scheme:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scheme '{request.scheme_id}' not found",
        )

    return generate_financial_summary(
        scheme=scheme,
        requested_loan_amount=request.loan_amount,
        requested_tenure_months=request.tenure_months,
    )
