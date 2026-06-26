# Floyde — Telephony & Messaging Compliance

> Practical engineering checklist for taking Floyde's communications features
> from **stub mode** to **live** in the United States. This is operational
> guidance, **not legal advice** — confirm specifics with Twilio's current docs
> and your own counsel before launch.

Floyde follows a **stub-first** rule: with no provider credentials set, calls
and (future) messages are simulated locally and never leave the box. Nothing
below happens by accident — going live is a deliberate, account-side step.

---

## TL;DR — what applies to what

| Track | Used by | Registration you need |
|---|---|---|
| **Voice** (concierge "call now" bridge) | `app/services/telephony.py` | Trust Hub Business Profile · CNAM · SHAKEN/STIR · TCPA consent |
| **SMS/MMS** (Phase-2 marketing, reminders) | *not built yet* | A2P **10DLC** Brand + Campaign (or Toll-Free Verification) |

**Common confusion:** "Campaign registration" and the **opt-in policies/
statements** belong to the **SMS** track (A2P 10DLC / The Campaign Registry).
They are **not** required for outbound **voice**. CNAM is a **voice** concept.
You don't need a 10DLC campaign to run the concierge call bridge.

---

## Trust Hub Business Profile (the umbrella — do this first)

Most US carrier features now hang off a verified **Business Profile** in
Twilio **Trust Hub** (a "Customer Profile" / "Secondary Customer Profile").

Gather:
- Legal business name (exactly as registered)
- **EIN / Tax ID** (US) and business type (LLC, Corp, Sole Prop…)
- Registered business address
- Website URL
- Authorized representative(s): name, email, phone, job title
- Business industry / vertical

Once approved, the profile unlocks CNAM, SHAKEN/STIR attestation, A2P 10DLC,
and toll-free verification.

---

## Voice checklist (concierge "call now")

The concierge bridge dials the client and `<Dial>`s your desk number. Before
flipping it live:

- [ ] **Provision a number** for outbound voice (local 10DLC or toll-free).
      Toll-free voice has its own verification path.
- [ ] **CNAM (Caller ID Name)** — register the ≤15-char display name (e.g.
      `FLOYDE` / `FLOYDE BARBER`). Improves answer rates; without it the call
      shows a bare number. Note CNAM display ultimately depends on the
      *terminating* carrier reading the CNAM database.
- [ ] **SHAKEN/STIR** — verify number ownership so Twilio can sign calls with
      higher attestation. Unsigned/low-attestation calls increasingly get a
      **"Spam Likely"** label. Consider Twilio **Branded Calls / rich call
      data** for logo + reason-for-call where supported.
- [ ] **TCPA consent** — you must have prior consent to place the call.
      Floyde's posture is strong here: **the client requests the callback
      themselves**, which is the cleanest form of express consent. Still:
  - [ ] Record consent (who/when/how) for an audit trail. *(Floyde captures
        this implicitly via the `ConciergeRequest` the client creates;
        consider persisting an explicit consent timestamp — see "Recommended
        code follow-ups".)*
  - [ ] Honor the **National DNC** and any internal opt-out list.
  - [ ] Respect **calling-hours** rules (generally 8am–9pm in the called
        party's local time).
  - [ ] Note: pre-recorded/artificial-voice and autodialed calls carry
        stricter TCPA rules. The current flow is a **human** concierge bridge,
        which is the lower-risk pattern — keep it that way, or re-review if you
        add automated voice.
- [ ] **State law** — some states (e.g. FL, OK) have stricter mini-TCPA
      statutes; check the states you operate in.

### Environment variables (already wired)
```
FLOYDE_TWILIO_ACCOUNT_SID=
FLOYDE_TWILIO_AUTH_TOKEN=
FLOYDE_TWILIO_FROM_NUMBER=+1XXXXXXXXXX
FLOYDE_CONCIERGE_DESK_NUMBER=+1XXXXXXXXXX
```
`GET /health` reports `integrations.telephony` as `live` once SID + token +
from-number are present; otherwise `stub`.

---

## SMS checklist — A2P 10DLC (Phase 2: marketing, reminders, rebooking)

When Floyde adds SMS (booking reminders, marketing automation, rebooking
nudges — all in the blueprint's Phase 2), US carriers require **A2P 10DLC**
registration via **The Campaign Registry (TCR)**. **This** is where the
"campaign policies and statements" live.

### 1. Brand registration
- Legal name, EIN/Tax ID, address, website, vertical, contact — same data as
  the Trust Hub Business Profile (reused).

### 2. Campaign registration — the policies & statements
For each messaging use-case (e.g. "Customer Care", "Marketing", "2FA/OTP"):
- [ ] **Use-case** and description of message content
- [ ] **Sample messages** (2+ realistic examples per campaign)
- [ ] **Opt-in flow + opt-in language** — exactly how a user consents
      (web form checkbox copy, keyword, point-of-sale), with screenshots/URL
- [ ] **Opt-out language** — STOP handling, and HELP response
- [ ] **Privacy Policy URL** and **Terms of Service URL** (must be live and
      must state that consent isn't a condition of purchase, how numbers are
      used, and that message/data rates may apply)
- [ ] Expected message volume / throughput
- [ ] Embedded-link and phone-number disclosure if used

> Carriers actively reject campaigns whose hosted privacy policy / opt-in copy
> doesn't match the submitted statements. Get these live **before** submitting.

### Toll-free alternative
If you send SMS from a **toll-free** number instead, you complete **Toll-Free
Verification** (a different form) rather than 10DLC — similar opt-in/opt-out
and privacy-policy evidence required.

### Required opt-in to capture now
Even before sending any SMS, capture a compliant **SMS opt-in** (consent
boolean + timestamp + source) at signup / profile so you have a clean consent
record when 10DLC goes live. *(Not yet in the data model — see below.)*

---

## Email (marketing) — adjacent obligations

For the email side of Phase-2 marketing:
- [ ] **CAN-SPAM**: accurate From/Subject, physical mailing address in the
      footer, working one-click unsubscribe honored promptly.
- [ ] If you have EU/UK contacts, **GDPR/PECR** lawful basis + consent.

---

## Recommended code follow-ups (not yet implemented)

These were intentionally left out of this pass; they're the natural next steps
when you're ready to operationalize compliance:

1. **Explicit consent capture** — persist a TCPA consent timestamp/source on
   `ConciergeRequest` (and an SMS opt-in flag on `ClientProfile`) for an
   auditable record.
2. **Live-mode guard** — an explicit `FLOYDE_TELEPHONY_LIVE=true` flag so real
   dialing requires a deliberate opt-in, not merely the presence of creds.
3. **CNAM / Business-Profile settings** — store the CNAM display string and
   Trust Hub profile SID, and surface "registration readiness" in `/health`.
4. **Opt-out handling** — STOP/HELP keyword handling and an internal DNC list
   before any SMS sending.

Ask and I'll scaffold any of these.

---

## Quick reference — official docs to verify against

- Twilio Trust Hub / Customer Profiles
- Twilio CNAM (Caller ID) and SHAKEN/STIR
- Twilio A2P 10DLC (Brand & Campaign) and The Campaign Registry
- Twilio Toll-Free Verification
- FCC TCPA rules · FTC CAN-SPAM Act

*Last reviewed: 2026-06. Verify current carrier/regulatory requirements before
launch — these rules change frequently.*
