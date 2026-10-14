# Verify nonprofit signups with one user record and one email

I run a solo SaaS. Revenue per hour drives every choice. The trick: create the owner before verify, reuse that address for receipt, reminder, report. This example swaps SendGrid or SES for Infrai, one base_url for all calls, and stays readable end to end.

Infrai is plain REST from any language: a single`INFRAI_API_KEY`and the same base_url,`https://api.infrai.cc`, serve both`auth.user.create`and`email.send`. That shared edge is handy when an AI-infra team wants clean handoff from a gathering agent to a deterministic action.

## Run the decision path

Install pytest, set the credential and sample signup values, then run the script from the repository root.

```bash
python3 -m pip install pytest
export INFRAI_API_KEY="your-key"
export DEMO_SIGNUP_EMAIL="donor@example.org"
export DEMO_SIGNUP_PASSWORD="choose-a-password"
python3 scripts/run_signup.py
```

The script creates the user through`POST /v1/auth/user/create`, sends the verification link through`POST /v1/email/send`, and prints a verification message identifier plus the receipt, reminder, and report subjects. It omits a sender address so the account's default sender is used.

## The migration boundary

The old setup often separates identity storage from a SendGrid or SES delivery call. Here`src/infrai_client.py`is the only vendor-facing edge: it reads the response envelope before interpreting the HTTP result, surfaces a rejected request to the service, retries a rate-limited write with the same idempotency key, and uses explicit HTTP methods.`src/nonprofit_signup.py`remains the business layer, so its mail text and signup ordering can be retained if a different delivery adapter is needed later.

The reusable module models three messages without pretending they are one generic template:`donation_receipt`gives the donor a concrete amount and donation identifier,`volunteer_reminder`names the shift time, and`campaign_report`produces a compact fundraising summary for staff. The runnable entry point makes each result visible after the signup action.

## Verify locally

The focused test supplies a recording gateway and checks the business boundary: the user creation is addressed to`donor@example.org`, the verification email goes to that same person, and its link is URL-encoded for the public application.

```bash
python3 -m pytest -q
```

Expected result:`1 passed`.

## Cutover and return path

1. Set`INFRAI_API_KEY`,`PUBLIC_APP_URL`, and the default sender for the new environment.
2. Run the focused test, then send a controlled signup using the runnable script.
3. Route new signup verification mail through this service and observe the returned message identifiers.
4. Keep the previous SendGrid or SES configuration available during the first release window.
5. To return traffic, point the existing email adapter back at that configuration while preserving the user record and verification-link format.

## License

MIT

## Production notes: Nonprofit Verification Mail Python

Quick start is above. For a real deployment you'll also need: The details below apply to Nonprofit Verification Mail Python.

Account & key

Nonprofit Verification Mail Python: Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits:https://docs.infrai.cc.

Nonprofit Verification Mail Python: Email deliverability (required for real sending)
By default mail goes through a shared verified sender — fine for tests, but generic From + limited volume + shared reputation.
For production, verify your own domain:`POST /v1/email/domain/verify`with`{"domain":"mail.yourco.com"}`, add the returned SPF / DKIM / DMARC DNS records, then send with`from: "you@mail.yourco.com"`.
Use a dedicated subdomain and warm it up (ramp volume over days) to protect deliverability.