from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database.database import get_db
from services.contact_unification_service import import_customers_from_altimeter, import_vendors_from_altimeter

router = APIRouter()

@router.post("/sync-altimeter")
async def sync_altimeter_contacts(db: Session = Depends(get_db)):
    """
    Import customers and vendors from Altimeter into Atlas contacts.
    """
    customer_stats = import_customers_from_altimeter(db)
    vendor_stats = import_vendors_from_altimeter(db)

    return {
        "status": "success",
        "customers": customer_stats,
        "vendors": vendor_stats,
        "summary": {
            "total_imported": customer_stats["imported"] + vendor_stats["imported"],
            "total_updated": customer_stats["updated"] + vendor_stats["updated"],
            "total_errors": customer_stats["errors"] + vendor_stats["errors"]
        }
    }
