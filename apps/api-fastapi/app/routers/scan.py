import hmac

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import SCAN_API_KEY
from ..database import get_session
from ..schemas import ScanIn, ScanOut
from ..services.scan import InvalidQrToken, scan_ticket

router = APIRouter(prefix="/scan", tags=["scan"])


@router.post("", response_model=ScanOut)
async def scan_endpoint(
    payload: ScanIn,
    x_scan_key: str = Header(default=""),
    session: AsyncSession = Depends(get_session),
):
    """Scan d'un billet à l'entrée. Protégé par une clé partagée
    (X-Scan-Key) donnée manuellement au staff — pas de compte staff dédié
    dans l'API pour l'instant (voir docs/RAPPORT.md, ouvert au jalon M4)."""
    if not SCAN_API_KEY:
        raise HTTPException(status_code=503, detail="Scan non configuré (SCAN_API_KEY absente)")
    if not hmac.compare_digest(x_scan_key, SCAN_API_KEY):
        raise HTTPException(status_code=401, detail="Clé de scan invalide")

    try:
        result = await scan_ticket(session, payload.qr_token)
    except InvalidQrToken as exc:
        raise HTTPException(status_code=400, detail="Billet invalide") from exc

    if result.already_scanned:
        raise HTTPException(
            status_code=409,
            detail=f"Billet déjà scanné le {result.scanned_at.isoformat()}",
        )

    return ScanOut(
        ticket_id=result.ticket_id,
        ticket_type_name=result.ticket_type_name,
        event_title=result.event_title,
        scanned_at=result.scanned_at,
    )
