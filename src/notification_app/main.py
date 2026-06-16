"""
B7 – Multi-Channel Alert Service (Notification Service)
FIT4110 Lab 04 – Docker Packaging

Endpoints:
  GET  /health
  POST /alerts
  GET  /alerts/recent
  PUT  /notifications/preferences/{userId}

Auth: HTTP Bearer JWT (token checked against AUTH_TOKEN env var)
Errors: RFC 7807 ProblemDetails (application/problem+json)
Deduplication: eventId uniqueness enforced in-memory
"""

import os
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Set

from fastapi import Depends, FastAPI, Header, HTTPException, Path, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator


# ─────────────────────────── Config ────────────────────────────────────────

SERVICE_NAME = os.getenv("SERVICE_NAME", "notification-service")
SERVICE_VERSION = os.getenv("SERVICE_VERSION", "0.1.0")
AUTH_TOKEN = os.getenv("AUTH_TOKEN", "local-dev-token")

# ─────────────────────────── App ───────────────────────────────────────────

app = FastAPI(
    title="Multi-Channel Alert Service API (B7)",
    version=SERVICE_VERSION,
    description=(
        "B7 Notification Service – tiếp nhận yêu cầu cảnh báo từ B6 Core Business, "
        "xử lý deduplication và gửi thông báo đa kênh (SMS, Email, Push)."
    ),
)

# ─────────────────────────── In-memory stores ──────────────────────────────

NOTIFICATIONS: List[Dict] = []          # danh sách notification đã tạo
SEEN_EVENT_IDS: Set[str] = set()        # deduplication set
USER_PREFERENCES: Dict[str, List[str]] = {}  # userId → enabledChannels

# ─────────────────────────── Enums & Schemas ───────────────────────────────

class AlertSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class NotificationStatus(str, Enum):
    PENDING = "PENDING"
    SENT = "SENT"
    FAILED = "FAILED"


class Channel(str, Enum):
    SMS = "SMS"
    EMAIL = "EMAIL"
    PUSH = "PUSH"


# ─── Problem Details (RFC 7807) ─────────────────────────────────────────────

class Problem(BaseModel):
    type: str = "about:blank"
    title: str
    status: int = Field(..., ge=400, le=599)
    detail: Optional[str] = None
    instance: Optional[str] = None


# ─── Health ─────────────────────────────────────────────────────────────────

class HealthStatus(BaseModel):
    status: str
    service: str
    time: str


# ─── Alert Payload (ánh xạ 100% với B6 contract) ────────────────────────────

class AlertData(BaseModel):
    alertId: str = Field(..., description="UUID của alert")
    severity: AlertSeverity
    message: str = Field(..., min_length=5)
    targetUserId: str = Field(..., example="SV-12345")


class AlertPayload(BaseModel):
    eventId: str = Field(..., description="UUID dùng làm deduplication key")
    eventType: str = Field(..., pattern="^core\\.alert\\.created$")
    occurredAt: str
    correlationId: str
    source: str
    data: AlertData


# ─── Responses ───────────────────────────────────────────────────────────────

class NotificationAccepted(BaseModel):
    notificationId: str
    status: str = "PENDING"
    acceptedAt: str


class NotificationStatusDetail(BaseModel):
    notificationId: str
    alertId: str
    currentStatus: NotificationStatus
    targetUserId: str
    sentAt: Optional[str] = None
    errorMessage: Optional[str] = None


class UpdatePreferencesRequest(BaseModel):
    enabledChannels: List[Channel] = Field(..., min_length=1)


# ─────────────────────────── Helpers ───────────────────────────────────────

def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_problem(
    *,
    status_code: int,
    title: str,
    detail: Optional[str] = None,
    instance: Optional[str] = None,
    problem_type: str = "https://api.campus.local/errors/error",
) -> Dict:
    problem: Dict = {
        "type": problem_type,
        "title": title,
        "status": status_code,
    }
    if detail is not None:
        problem["detail"] = detail
    if instance is not None:
        problem["instance"] = instance
    return problem


# ─────────────────────────── Exception handlers ────────────────────────────

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    if isinstance(exc.detail, dict):
        problem = exc.detail
    else:
        problem = build_problem(
            status_code=exc.status_code,
            title=_http_title(exc.status_code),
            detail=str(exc.detail),
            instance=str(request.url.path),
        )
    return JSONResponse(
        status_code=exc.status_code,
        content=problem,
        media_type="application/problem+json",
        headers=getattr(exc, "headers", None),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    first_error = exc.errors()[0] if exc.errors() else {}
    location = ".".join(str(x) for x in first_error.get("loc", []))
    message = first_error.get("msg", "Validation error")
    detail = f"{location}: {message}" if location else message

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=build_problem(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            title="Unprocessable Entity",
            detail=detail,
            instance=str(request.url.path),
            problem_type="https://api.campus.local/errors/validation-error",
        ),
        media_type="application/problem+json",
    )


def _http_title(code: int) -> str:
    titles = {
        400: "Bad Request",
        401: "Unauthorized",
        403: "Forbidden",
        404: "Not Found",
        409: "Conflict",
        422: "Unprocessable Entity",
        429: "Too Many Requests",
        500: "Internal Server Error",
    }
    return titles.get(code, "HTTP Error")


# ─────────────────────────── Auth middleware ───────────────────────────────

def verify_bearer_token(
    authorization: Optional[str] = Header(default=None),
    request: Request = None,
) -> None:
    path = str(request.url.path) if request else "/"

    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=build_problem(
                status_code=401,
                title="Unauthorized",
                detail="Missing Authorization header. Provide: Bearer <token>",
                instance=path,
                problem_type="https://api.campus.local/errors/unauthorized",
            ),
            headers={"WWW-Authenticate": "Bearer"},
        )

    parts = authorization.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=build_problem(
                status_code=401,
                title="Unauthorized",
                detail="Authorization header must be in format: Bearer <token>",
                instance=path,
                problem_type="https://api.campus.local/errors/unauthorized",
            ),
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = parts[1]
    if token != AUTH_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=build_problem(
                status_code=401,
                title="Unauthorized",
                detail="Invalid bearer token",
                instance=path,
                problem_type="https://api.campus.local/errors/unauthorized",
            ),
            headers={"WWW-Authenticate": "Bearer"},
        )


# ─────────────────────────── Routes ────────────────────────────────────────

@app.get("/health", response_model=HealthStatus, tags=["health"])
def health() -> HealthStatus:
    """GET /health – không cần auth"""
    return HealthStatus(
        status="ok",
        service=SERVICE_NAME,
        time=now_iso(),
    )


@app.post(
    "/alerts",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=NotificationAccepted,
    tags=["alerts"],
    responses={
        400: {"model": Problem, "content": {"application/problem+json": {}}},
        401: {"model": Problem, "content": {"application/problem+json": {}}},
        409: {"model": Problem, "content": {"application/problem+json": {}}},
        422: {"model": Problem, "content": {"application/problem+json": {}}},
        429: {"model": Problem, "content": {"application/problem+json": {}}},
        500: {"model": Problem, "content": {"application/problem+json": {}}},
    },
)
def create_alert(
    payload: AlertPayload,
    request: Request,
    idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key"),
    _auth: None = Depends(verify_bearer_token),
) -> NotificationAccepted:
    """POST /alerts – tiếp nhận yêu cầu gửi cảnh báo an ninh"""
    path = str(request.url.path)

    # Deduplication: kiểm tra eventId
    if payload.eventId in SEEN_EVENT_IDS:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=build_problem(
                status_code=409,
                title="Conflict",
                detail=f"Duplicate eventId: {payload.eventId} đã được xử lý trước đó.",
                instance=path,
                problem_type="https://api.campus.local/errors/duplicate-event",
            ),
        )

    # Ghi nhận eventId vào dedup store
    SEEN_EVENT_IDS.add(payload.eventId)

    notification_id = str(uuid.uuid4())
    accepted_at = now_iso()

    NOTIFICATIONS.append({
        "notificationId": notification_id,
        "alertId": payload.data.alertId,
        "currentStatus": NotificationStatus.PENDING,
        "targetUserId": payload.data.targetUserId,
        "sentAt": None,
        "errorMessage": None,
        "acceptedAt": accepted_at,
    })

    return NotificationAccepted(
        notificationId=notification_id,
        status="PENDING",
        acceptedAt=accepted_at,
    )


@app.get(
    "/alerts/recent",
    response_model=List[NotificationStatusDetail],
    tags=["alerts"],
    responses={
        401: {"model": Problem, "content": {"application/problem+json": {}}},
        404: {"model": Problem, "content": {"application/problem+json": {}}},
        500: {"model": Problem, "content": {"application/problem+json": {}}},
    },
)
def get_recent_alerts(
    request: Request,
    _auth: None = Depends(verify_bearer_token),
) -> List[NotificationStatusDetail]:
    """GET /alerts/recent – tra cứu lịch sử cảnh báo"""
    return [
        NotificationStatusDetail(**n) for n in NOTIFICATIONS
    ]


@app.put(
    "/notifications/preferences/{userId}",
    tags=["alerts"],
    responses={
        400: {"model": Problem, "content": {"application/problem+json": {}}},
        401: {"model": Problem, "content": {"application/problem+json": {}}},
        500: {"model": Problem, "content": {"application/problem+json": {}}},
    },
)
def update_notification_preferences(
    userId: str = Path(..., example="SV-12345"),
    body: UpdatePreferencesRequest = None,
    _auth: None = Depends(verify_bearer_token),
) -> Dict:
    """PUT /notifications/preferences/{userId} – bật/tắt kênh nhận tin"""
    USER_PREFERENCES[userId] = [ch.value for ch in body.enabledChannels]
    return {"updated": True}
