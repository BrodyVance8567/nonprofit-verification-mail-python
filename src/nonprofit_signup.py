"""Domain decisions for a donor or volunteer signup."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Protocol
from urllib.parse import quote


@dataclass(frozen=True)
class SignupRequest:
    email: str
    password: str
    name: str
    role: str


@dataclass(frozen=True)
class EmailReceipt:
    donor_name: str
    amount_cents: int
    donation_id: str


@dataclass(frozen=True)
class VolunteerReminder:
    volunteer_name: str
    shift_name: str
    starts_at: str


@dataclass(frozen=True)
class CampaignReport:
    campaign_name: str
    donor_count: int
    amount_cents: int


@dataclass(frozen=True)
class SignupOutcome:
    email: str
    message_id: str


class NonprofitGateway(Protocol):
    def create_user(self, payload: dict[str, object]) -> dict[str, object]: ...

    def send_email(self, payload: dict[str, object], idempotency_key: str) -> dict[str, object]: ...


class NonprofitSignup:
    def __init__(self, gateway: NonprofitGateway, public_app_url: str) -> None:
        self.gateway = gateway
        self.public_app_url = public_app_url.rstrip("/")

    def register_and_send_verification(self, request: SignupRequest) -> SignupOutcome:
        key = self._key("signup", request.email)
        self.gateway.create_user(
            {
                "email": request.email,
                "password": request.password,
                "name": request.name,
                "metadata": {"role": request.role},
                "idempotency_key": key,
            }
        )
        link = f"{self.public_app_url}/verify-email?email={quote(request.email)}"
        result = self.gateway.send_email(
            {
                "to": request.email,
                "subject": "Verify your nonprofit account",
                "html": (
                    f"<p>Welcome, {request.name}.</p>"
                    f"<p><a href=\"{link}\">Verify your email</a></p>"
                ),
            },
            key,
        )
        return SignupOutcome(email=request.email, message_id=str(result["message_id"]))

    def donation_receipt(self, receipt: EmailReceipt) -> dict[str, object]:
        return {
            "subject": f"Donation receipt {receipt.donation_id}",
            "html": (
                f"<p>Thank you, {receipt.donor_name}.</p>"
                f"<p>Your gift was ${(receipt.amount_cents / 100):.2f}.</p>"
            ),
        }

    def volunteer_reminder(self, reminder: VolunteerReminder) -> dict[str, object]:
        return {
            "subject": f"Reminder: {reminder.shift_name}",
            "html": f"<p>{reminder.volunteer_name}, your shift starts {reminder.starts_at}.</p>",
        }

    def campaign_report(self, report: CampaignReport) -> str:
        return (
            f"{report.campaign_name}: {report.donor_count} donors, "
            f"${(report.amount_cents / 100):.2f} received."
        )

    @staticmethod
    def _key(prefix: str, email: str) -> str:
        digest = sha256(f"{prefix}:{email}".encode("utf-8")).hexdigest()[:24]
        return f"{prefix}-{digest}"
