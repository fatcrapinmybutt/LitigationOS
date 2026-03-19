
import os
from pathlib import Path

# Change this to your desired drive path
base_path = Path("F:/OMNILITIGATION_SYSTEM")

structure = [
    "EvidenceRepository/AllChronological/2023_Events",
    "EvidenceRepository/AllChronological/2024_Events",
    "EvidenceRepository/AllChronological/2025_Events",
    "EvidenceRepository/ByLegalType/Leases_Contracts",
    "EvidenceRepository/ByLegalType/Utility_Ledgers",
    "EvidenceRepository/ByLegalType/CourtOrders_Judgments",
    "EvidenceRepository/ByLegalType/Photos_MetadataAnchored",
    "EvidenceRepository/ByLegalType/Communications_Text_Email_AppClose",
    "EvidenceRepository/ByLegalType/Affidavits_SwornStatements",
    "EvidenceRepository/ByLegalType/EvidenceUnclassified_AuditQueue",
    "EvidenceRepository/ByLegalGrounds/MCL_554_139_Habitability",
    "EvidenceRepository/ByLegalGrounds/MCL_600_5714_EvictionStanding",
    "EvidenceRepository/ByLegalGrounds/MCL_445_903_MCPA_Fraud",
    "EvidenceRepository/ByLegalGrounds/MCL_600_5720_Retaliation",
    "EvidenceRepository/ByLegalGrounds/MCL_600_2919a_UnjustEnrichment",
    "EvidenceRepository/ByLegalGrounds/MCR_2_612_C_VoidJudgment",
    "EvidenceRepository/ByLegalGrounds/MCR_3_310_B_Injunctions",
    "EvidenceRepository/NotYetReviewed/Needs_OCR_OR_Classification",
    "CaseSystems/LT_25061626_HousingEviction",
    "CaseSystems/DC_1507_CustodySupport",
    "CaseSystems/PPO_WatsonSeries",
    "CaseSystems/Federal_1983",
    "CaseSystems/HUD_EGLE_AG_AgencyTrack",
    "FilingGenerators/Motions",
    "FilingGenerators/Complaints_Counterclaims",
    "FilingGenerators/Affidavits_Declarations",
    "FilingGenerators/ProposedOrders",
    "FilingGenerators/FiledDraftsArchive",
    "MasterEvidenceMatrix",
    "FilingBundles/ZIP_CourtBundles",
    "FilingBundles/USB_BinderPrep",
    "AIExecutionLogs",
    "System"
]

for subdir in structure:
    path = base_path / subdir
    path.mkdir(parents=True, exist_ok=True)
    print(f"Created: {path}")
