from src.nonprofit_signup import NonprofitSignup, SignupRequest


class RecordingGateway:
    def __init__(self) -> None:
        self.user_payload: dict[str, object] | None = None
        self.email_payload: dict[str, object] | None = None
        self.email_key: str | None = None

    def create_user(self, payload: dict[str, object]) -> dict[str, object]:
        self.user_payload = payload
        return {}

    def send_email(self, payload: dict[str, object], idempotency_key: str) -> dict[str, object]:
        self.email_payload = payload
        self.email_key = idempotency_key
        return {"message_id": "msg_123"}


def test_signup_creates_the_owner_then_addresses_a_verification_link() -> None:
    gateway = RecordingGateway()
    signup = NonprofitSignup(gateway, "https://giving.example.org")

    outcome = signup.register_and_send_verification(
        SignupRequest("donor@example.org", "a-strong-password", "Dana", "donor")
    )

    assert outcome.message_id == "msg_123"
    assert gateway.user_payload is not None
    assert gateway.user_payload["email"] == "donor@example.org"
    assert gateway.email_payload is not None
    assert gateway.email_payload["to"] == "donor@example.org"
    assert "https://giving.example.org/verify-email?email=donor%40example.org" in str(
        gateway.email_payload["html"]
    )
    assert gateway.email_key == gateway.user_payload["idempotency_key"]
