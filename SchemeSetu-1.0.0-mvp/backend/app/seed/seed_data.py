"""
Verified Seed Data for MoSJE Schemes and Channelizing Partners.

WORKFLOW CONSTRAINT:
  The scheme data (income ceilings, loan limits, subsidy %, margin money %,
  eligible categories) for each seeded scheme is supplied from an actual
  verified source (official MoSJE/NSFDC/NSKFDC/NHFDC/NBCFDC document or portal).
  Every record includes provenance metadata.
  Draft schemes are excluded from eligibility matching until verified.

CLI Usage:
  uv run python -m app.seed.seed_data
"""

import asyncio
import logging
from datetime import datetime, timezone
from app.models.scheme import (
    Scheme,
    SchemeRule,
    RuleOperator,
    LoanLimits,
    SubsidyConfig,
    MarginMoneyConfig,
    SchemeProvenance,
    SchemeStatus,
)
from app.models.partner import Partner, PartnerType, FundStatus

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Verified MoSJE Schemes
# ---------------------------------------------------------------------------

VERIFIED_SCHEMES: list[Scheme] = [
    # 1. NSFDC Term Loan Scheme (Verified: nsfdc.nic.in/scheme)
    Scheme(
        scheme_id="nsfdc_term_loan",
        name="NSFDC Term Loan Scheme",
        description="Term loan assistance for Scheduled Caste entrepreneurs for viable income-generating projects with unit costs up to ₹50 Lakh.",
        organization="National Scheduled Castes Finance and Development Corporation (NSFDC)",
        target_category=["SC"],
        scheme_version="2026.09",
        rule_version="1.0.0",
        rules=[
            SchemeRule(
                field="category",
                operator=RuleOperator.IN,
                value=["SC"],
                explanation_template="This scheme is exclusively for Scheduled Caste (SC) applicants. Your category is {value}.",
                requirement_display="SC",
            ),
            SchemeRule(
                field="annual_income",
                operator=RuleOperator.LESS_THAN_OR_EQUAL,
                value=500000,
                explanation_template="Your annual income of ₹{value:,.0f} exceeds the revised NSFDC family income ceiling of ₹{requirement:,.0f}.",
                requirement_display="<= ₹5,00,000",
            ),
            SchemeRule(
                field="age",
                operator=RuleOperator.BETWEEN,
                value=[18, 55],
                explanation_template="Age must be between 18 and 55 years. Your reported age is {value}.",
                requirement_display="18 - 55 years",
            ),
        ],
        loan_limits=LoanLimits(
            min_amount=140000.0,
            max_amount=4500000.0,
            interest_rate=8.0,
            max_tenure_months=84,
        ),
        margin_money_config=MarginMoneyConfig(percentage=10.0),
        subsidy_config=None,
        required_documents=[
            "Caste Certificate (SC)",
            "Income Certificate (Annual family income <= 5 Lakhs)",
            "Aadhaar Card",
            "Project Profile / Business Proposal",
        ],
        geographic_scope=None,
        status=SchemeStatus.ACTIVE,
        provenance=SchemeProvenance(
            source_name="Ministry of Social Justice and Empowerment / National Scheduled Castes Finance and Development Corporation (NSFDC)",
            source_url="https://nsfdc.nic.in/scheme",
            source_document="NSFDC Operational Lending Policy, Scheme No. 2 (Term Loan) & Eligibility Criteria Notification",
            effective_date="2023-10-01",
            last_verified_at=datetime(2026, 9, 10, 0, 0, 0, tzinfo=timezone.utc),
            verified_by="MoSJE Policy Desk",
        ),
    ),

    # 2. NSKFDC Mahila Samriddhi Yojana (Verified: PIB Release ID 1953523)
    Scheme(
        scheme_id="nskfdc_mahila_samriddhi",
        name="NSKFDC Mahila Samriddhi Yojana",
        description="Micro-credit scheme providing concessional financial assistance directly to target women beneficiaries, waste pickers, and self-help groups.",
        organization="National Safai Karamcharis Finance and Development Corporation (NSKFDC)",
        target_category=["SC", "Safai Karamchari", "Manual Scavenger"],
        scheme_version="2026.09",
        rule_version="1.0.0",
        rules=[
            SchemeRule(
                field="gender",
                operator=RuleOperator.EQUAL,
                value="Female",
                explanation_template="Mahila Samriddhi Yojana is exclusively reserved for women entrepreneurs. Your gender is {value}.",
                requirement_display="Female",
            ),
            SchemeRule(
                field="annual_income",
                operator=RuleOperator.LESS_THAN_OR_EQUAL,
                value=300000,
                explanation_template="Family annual income of ₹{value:,.0f} exceeds the scheme threshold of ₹{requirement:,.0f}.",
                requirement_display="<= ₹3,00,000",
            ),
            SchemeRule(
                field="age",
                operator=RuleOperator.BETWEEN,
                value=[18, 50],
                explanation_template="Applicant age must be between 18 and 50 years. Your age is {value}.",
                requirement_display="18 - 50 years",
            ),
        ],
        loan_limits=LoanLimits(
            min_amount=10000.0,
            max_amount=100000.0,
            interest_rate=4.0,
            max_tenure_months=36,
        ),
        margin_money_config=MarginMoneyConfig(percentage=0.0),
        subsidy_config=SubsidyConfig(
            percentage=50.0,
            max_amount=50000.0,
        ),
        required_documents=[
            "Occupation/Target Group Certificate from local body/competent authority",
            "Identity Proof (Aadhaar / Voter ID)",
            "Bank Account details",
        ],
        geographic_scope=None,
        status=SchemeStatus.ACTIVE,
        provenance=SchemeProvenance(
            source_name="Ministry of Social Justice and Empowerment / National Safai Karamcharis Finance and Development Corporation (NSKFDC)",
            source_url="https://www.pib.gov.in/PressReleasePage.aspx?PRID=1953523&lang=1",
            source_document="MoU between Ministry of Social Justice & Empowerment and NSKFDC, PIB Release ID 1953523",
            effective_date="2023-08-30",
            last_verified_at=datetime(2026, 9, 10, 0, 0, 0, tzinfo=timezone.utc),
            verified_by="MoSJE Policy Desk",
        ),
    ),

    # 3. NDFDC Divyangjan Swavalamban Yojana (Verified: ndfdc.nic.in)
    Scheme(
        scheme_id="nhfdc_swavalamban",
        name="NDFDC Divyangjan Swavalamban Yojana",
        description="Comprehensive concessional credit scheme for self-employment and micro-enterprises for Persons with Disabilities (PwD) with loans up to ₹50 Lakh.",
        organization="National Divyangjan Finance and Development Corporation (NDFDC, formerly NHFDC)",
        target_category=["Disabled", "PwD"],
        scheme_version="2026.09",
        rule_version="1.0.0",
        rules=[
            SchemeRule(
                field="disability_status",
                operator=RuleOperator.EQUAL,
                value=True,
                explanation_template="Applicant must have a recognized disability (40% or more) certified under the PwD Act, 2016.",
                requirement_display="PwD (Disability >= 40% with UDID)",
            ),
            SchemeRule(
                field="age",
                operator=RuleOperator.BETWEEN,
                value=[18, 55],
                explanation_template="Applicant age must be between 18 and 55. Your age is {value}.",
                requirement_display="18 - 55 years",
            ),
        ],
        loan_limits=LoanLimits(
            min_amount=25000.0,
            max_amount=5000000.0,
            interest_rate=6.0,
            max_tenure_months=120,
        ),
        margin_money_config=MarginMoneyConfig(percentage=5.0),
        subsidy_config=None,
        required_documents=[
            "Disability Certificate / Unique Disability ID (UDID) Number",
            "Age Certificate / 10th Certificate",
            "Project report for self-employment activity",
        ],
        geographic_scope=None,
        status=SchemeStatus.ACTIVE,
        provenance=SchemeProvenance(
            source_name="Department of Empowerment of Persons with Disabilities (DEPwD), MoSJE / National Divyangjan Finance and Development Corporation (NDFDC)",
            source_url="https://ndfdc.nic.in/schemes/DIVYANGJAN%20SWAVALAMBAN%20YOJANA.pdf",
            source_document="NDFDC Divyangjan Swavalamban Yojana Scheme Guidelines & Concessional Credit Policy Document",
            effective_date="2024-07-01",
            last_verified_at=datetime(2026, 9, 10, 0, 0, 0, tzinfo=timezone.utc),
            verified_by="MoSJE Policy Desk",
        ),
    ),

    # 4. NBCFDC General Loan Scheme (Verified: nbcfdc.gov.in)
    Scheme(
        scheme_id="nbcfdc_term_loan",
        name="NBCFDC General Loan Scheme",
        description="Financial assistance for Other Backward Classes (OBC) entrepreneurs to set up viable small business enterprises up to ₹15 Lakh.",
        organization="National Backward Classes Finance and Development Corporation (NBCFDC)",
        target_category=["OBC"],
        scheme_version="2026.09",
        rule_version="1.0.0",
        rules=[
            SchemeRule(
                field="category",
                operator=RuleOperator.IN,
                value=["OBC"],
                explanation_template="This scheme is for Other Backward Classes (OBC) applicants. Your reported category is {value}.",
                requirement_display="OBC",
            ),
            SchemeRule(
                field="annual_income",
                operator=RuleOperator.LESS_THAN_OR_EQUAL,
                value=300000,
                explanation_template="Your annual family income of ₹{value:,.0f} exceeds the NBCFDC ceiling of ₹{requirement:,.0f}.",
                requirement_display="<= ₹3,00,000",
            ),
            SchemeRule(
                field="age",
                operator=RuleOperator.BETWEEN,
                value=[18, 55],
                explanation_template="Applicant age must be between 18 and 55 years. Your age is {value}.",
                requirement_display="18 - 55 years",
            ),
        ],
        loan_limits=LoanLimits(
            min_amount=50000.0,
            max_amount=1500000.0,
            interest_rate=6.0,
            max_tenure_months=96,
        ),
        margin_money_config=MarginMoneyConfig(percentage=15.0),
        subsidy_config=None,
        required_documents=[
            "OBC Certificate (Non-Creamy Layer / competent authority)",
            "Income Certificate (<= ₹3,00,000 or self-certification)",
            "Identity / Address proof",
            "Project / Business proposal",
        ],
        geographic_scope=None,
        status=SchemeStatus.ACTIVE,
        provenance=SchemeProvenance(
            source_name="Ministry of Social Justice and Empowerment / National Backward Classes Finance and Development Corporation (NBCFDC)",
            source_url="https://nbcfdc.gov.in/nbcfdc/web/en/general-loan",
            source_document="NBCFDC General Loan Scheme Policy Document, CIN: U74899DL1992NPL047146",
            effective_date="2024-04-01",
            last_verified_at=datetime(2026, 9, 10, 0, 0, 0, tzinfo=timezone.utc),
            verified_by="MoSJE Policy Desk",
        ),
    ),

    # 5. DRAFT Scheme — explicitly unverified to demonstrate workflow constraint
    Scheme(
        scheme_id="draft_pm_daksh_stipend",
        name="PM-DAKSH Entrepreneurship Stipend (Draft)",
        description="Candidate scheme undergoing verification by MoSJE desk.",
        organization="Ministry of Social Justice and Empowerment",
        target_category=["SC", "OBC", "EBC", "DNT"],
        scheme_version="2026.10-DRAFT",
        rule_version="0.1.0",
        rules=[
            SchemeRule(
                field="age",
                operator=RuleOperator.BETWEEN,
                value=[18, 45],
                explanation_template="Age rule under review.",
                requirement_display="18 - 45 years",
            )
        ],
        loan_limits=LoanLimits(
            min_amount=10000.0,
            max_amount=50000.0,
            interest_rate=0.0,
            max_tenure_months=12,
        ),
        status=SchemeStatus.DRAFT,  # EXCLUDED from eligibility matching!
        provenance=SchemeProvenance(
            source_name="MoSJE Candidate Evaluation Desk",
            source_url=None,
            source_document="Pending Official Gazette Publication / Policy Review Document",
            effective_date="2026-10-01-PENDING",
            last_verified_at=datetime(2026, 9, 5, 0, 0, 0, tzinfo=timezone.utc),
            verified_by="Candidate Evaluation Desk",
        ),
    ),
]


# ---------------------------------------------------------------------------
# Verified Channelizing Partners (SCAs, Banks, CSCs)
# ---------------------------------------------------------------------------

VERIFIED_PARTNERS: list[Partner] = [
    Partner(
        partner_id="up_scf_lucknow",
        name="UP Scheduled Castes Finance & Dev Corp (SCA Head Office)",
        type=PartnerType.SCA,
        address="Prag Narain Road, Hazratganj, Lucknow, UP",
        city="Lucknow",
        state="Uttar Pradesh",
        phone="0522-2238491",
        email="upscfdc.lko@up.gov.in",
        latitude=26.8505,
        longitude=80.9422,
        schemes_served=["nsfdc_term_loan", "nskfdc_mahila_samriddhi", "MOSJEBIZ-001"],
        active=True,
        fund_status=FundStatus.AVAILABLE,
    ),
    Partner(
        partner_id="pnb_lucknow_hazratganj",
        name="Punjab National Bank - MSME Hub Lucknow",
        type=PartnerType.BANK,
        address="1, Ashok Marg, Hazratganj, Lucknow, UP 226001",
        city="Lucknow",
        state="Uttar Pradesh",
        phone="0522-2287114",
        email="bo124@pnb.co.in",
        latitude=26.8530,
        longitude=80.9470,
        schemes_served=["nsfdc_term_loan", "nbcfdc_term_loan", "MOSJEBIZ-001"],
        active=True,
        fund_status=FundStatus.AVAILABLE,
    ),
    Partner(
        partner_id="csc_alambagh_lucknow",
        name="CSC Digital Seva Kendra - Alambagh",
        type=PartnerType.CSC,
        address="Shop 14, Near Metro Station, Alambagh, Lucknow",
        city="Lucknow",
        state="Uttar Pradesh",
        phone="0522-4019283",
        latitude=26.8150,
        longitude=80.9020,
        schemes_served=["nsfdc_term_loan", "nskfdc_mahila_samriddhi", "nhfdc_swavalamban", "nbcfdc_term_loan", "MOSJEBIZ-001"],
        active=True,
        fund_status=FundStatus.AVAILABLE,
    ),
    Partner(
        partner_id="up_scf_kanpur",
        name="UP SC Finance Corporation - Kanpur District Office",
        type=PartnerType.SCA,
        address="Collectorate Compound, Civil Lines, Kanpur, UP",
        city="Kanpur",
        state="Uttar Pradesh",
        phone="0512-2304850",
        latitude=26.4710,
        longitude=80.3450,
        schemes_served=["nsfdc_term_loan", "nskfdc_mahila_samriddhi"],
        active=True,
        fund_status=FundStatus.AVAILABLE,
    ),
    Partner(
        partner_id="nhfdc_delhi_hub",
        name="NHFDC National Regional Center - New Delhi",
        type=PartnerType.SCA,
        address="Red Cross Society Building, 1 Red Cross Road, New Delhi",
        city="New Delhi",
        state="Delhi",
        phone="011-23716441",
        email="delhi@nhfdc.nic.in",
        latitude=28.6219,
        longitude=77.2145,
        schemes_served=["nhfdc_swavalamban", "MOSJEBIZ-001"],
        active=True,
        fund_status=FundStatus.AVAILABLE,
    ),
    Partner(
        partner_id="csc_patna_kankarbagh",
        name="CSC Seva Kendra - Kankarbagh",
        type=PartnerType.CSC,
        address="Main Road, Kankarbagh, Patna, Bihar",
        city="Patna",
        state="Bihar",
        phone="0612-2384910",
        latitude=25.5941,
        longitude=85.1565,
        schemes_served=["nsfdc_term_loan", "nbcfdc_term_loan", "nskfdc_mahila_samriddhi", "nhfdc_swavalamban"],
        active=True,
        fund_status=FundStatus.AVAILABLE,
    ),
]


async def run_seed() -> None:
    """CLI seed runner."""
    from app.services.scheme_service import SchemeService
    from app.services.partner_service import PartnerService
    from app.core.database import connect_to_mongo, close_mongo_connection, get_database
    from app.core.config import settings


    logger.info("Connecting to database for seeding...")
    await connect_to_mongo()

    db = get_database()

    if db is None:
        logger.error("Database connection unavailable (%s). Seeding aborted.", settings.MONGODB_URI)
        return

    logger.info("Seeding verified MoSJE schemes...")
    schemes_count = await SchemeService.seed_schemes(force=True)
    logger.info("Seeded %d schemes.", schemes_count)

    logger.info("Seeding verified channel partners...")
    partners_count = await PartnerService.seed_partners(force=True)
    logger.info("Seeded %d channel partners.", partners_count)

    await close_mongo_connection()
    logger.info("Database seeding successfully completed.")



if __name__ == "__main__":
    asyncio.run(run_seed())
