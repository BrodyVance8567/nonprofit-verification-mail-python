"""Runnable signup example: create the user record, then send verification."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.infrai_client import InfraiClient
from src.nonprofit_signup import CampaignReport, EmailReceipt, NonprofitSignup, SignupRequest, VolunteerReminder


def main() -> None:
    email = os.environ["DEMO_SIGNUP_EMAIL"]
    password = os.environ["DEMO_SIGNUP_PASSWORD"]
    signup = NonprofitSignup(InfraiClient(), os.environ.get("PUBLIC_APP_URL", "https://example.org"))
    outcome = signup.register_and_send_verification(
        SignupRequest(email=email, password=password, name="Avery Lee", role="donor")
    )
    receipt = signup.donation_receipt(EmailReceipt("Avery Lee", 2500, "DON-104"))
    reminder = signup.volunteer_reminder(VolunteerReminder("Morgan Chen", "Food pantry", "Saturday 09:00"))
    report = signup.campaign_report(CampaignReport("Autumn pantry", 14, 35000))
    print(f"Verification sent to {outcome.email}: {outcome.message_id}")
    print(receipt["subject"])
    print(reminder["subject"])
    print(report)


if __name__ == "__main__":
    main()
