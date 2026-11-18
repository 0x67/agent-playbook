# Example PRD (excerpt)

Excerpts from "Sample PRD: Digital Account Opening v1.0". The document is fictional: the company, people, metrics, and requirements are invented, and it may be copied or adapted without restriction. The full sample has 18 stories; four are kept here. Read it for the level of detail and the wording, and do not reuse its numbers.

# PRDSM042 Digital Account Opening (e-KYC)

| | |
|---|---|
| Target release | Q2 2027 |
| Epic | Onboarding |
| Platform | Arunika Invest Mobile, Arunika Pro Desktop |
| Document status | Draft |
| Document owner | Rangga |
| Designer | Prita |
| Tech lead | IT Development |
| Stakeholders involved | Product, IT Development, Compliance, Operations, Customer Service, Data Analyst |

## Objective

This initiative replaces the current branch-assisted account opening flow with a fully remote digital onboarding journey for individual retail investors. The MVP will allow a prospective customer to open a securities trading account and its linked investor fund account entirely from Mobile or Desktop, using automated identity document capture, liveness-verified face matching, and a digitally signed customer agreement.

The target outcome is a median time-to-approval under one business day for applications that pass automated screening, without weakening the identity assurance or record-keeping standards that apply to securities account opening. Applications that cannot be cleared automatically shall be routed to a reviewable manual queue rather than silently rejected. Existing account maintenance, beneficiary changes, institutional onboarding, and account closure processes remain unchanged unless explicitly covered by this PRD.

## Current process and limitations

Account opening today begins with a web form that collects basic contact details, after which the prospective customer must either visit a branch or arrange a video call with an operations officer to present the original identity document. Supporting documents are uploaded as free-form image attachments and are reviewed manually against the submitted form by the onboarding team during business hours.

Because document data is retyped by the reviewer, transcription errors are a recurring source of rework, particularly for address fields and the taxpayer identification number. Applications containing a mismatch are returned to the applicant by email with a free-text explanation, and the applicant must restart the form from the beginning as no partial application state is persisted beyond twenty-four hours. There is also no structured reason code attached to a rejection, so Customer Service cannot tell a caller which step failed or what to correct. Funnel instrumentation stops at form submission, which means drop-off between submission and approval is not measurable and cannot be attributed to a specific step.

## Current metrics

| Metric | Current | Source |
|---|---|---|
| Median time from submission to account approval | 4.2 business days | Operations case log |
| Applications requiring manual data correction | 38% | Onboarding review queue |
| Applicant drop-off before completing identity verification | Not measurable | |
| Applications abandoned and restarted from scratch | 21% | Web form analytics |
| Customer Service contacts citing unclear application status | 1,340 / month | Ticket taxonomy |

## Success metrics

| Metric | Baseline | Target (90 days post-launch) |
|---|---|---|
| Median time from submission to account approval | 4.2 business days | ≤ 1 business day |
| Applications cleared without manual review | 62% | ≥ 80% |
| Applicants resuming an abandoned application | | ≥ 45% of abandonments |
| Customer Service contacts citing unclear status | 1,340 / month | ≤ 500 / month |
| Step-level funnel coverage | 0 of 7 steps | 7 of 7 steps instrumented |
| Liveness spoof attempts detected and blocked | | ≥ 98% of seeded test attempts |

## User stories

| User story | Requirement | Notes |
|---|---|---|
| **1.** As a prospective customer, I want to begin an application with only my mobile number and email, so that I can start without preparing documents first. | <ul><li>The system shall create an application record upon verified mobile number and email ownership.</li><li>Mobile number ownership shall be proven by SMS one-time passcode; email ownership shall be proven by a tokenised link.</li><li>Both verifications shall be required before the applicant proceeds past the first step.</li><li>A one-time passcode shall expire after five minutes and shall be limited to five requests per number per hour.</li><li>The system shall reject a mobile number or email already bound to an active account, returning reason code `DUP-CONTACT`.</li><li>Reason codes shall be surfaced to the applicant as plain language and stored verbatim in the application audit trail.</li></ul> | Duplicate-contact handling deliberately blocks rather than merges. Account recovery remains the path for existing customers. |
| **4.** As a prospective customer, I want to know exactly why a step failed and what to do next, so that I am not stuck guessing. | <ul><li>Every terminal and recoverable failure shall carry a structured reason code and a corresponding plain-language message.</li><li>The message shall state what failed, whether it is retryable, and the next action available to the applicant.</li><li>The system shall not expose model scores, internal thresholds, or screening vendor names to the applicant.</li><li>Reason codes shall be identical across Mobile and Desktop for the same underlying condition.</li><li>The reason code and message shall be visible to Customer Service against the application reference.</li></ul> | Shared code list is the contract between Product, Operations, and Customer Service. Changes require sign-off from all three. |
| **10.** As a compliance officer, I want screening performed before approval, so that prohibited parties are not onboarded. | <ul><li>The system shall screen the verified identity against sanctions, politically exposed person, and internal deny lists before any approval decision.</li><li>Screening shall execute after identity verification succeeds and before account creation.</li><li>A potential match shall route to manual review and shall never auto-reject.</li><li>A confirmed deny-list match shall reject with a generic applicant-facing message that does not disclose the screening outcome.</li><li>Screening list version and result shall be stored against the application.</li><li>Screening service unavailability shall hold the application in a pending state and shall raise an operational alert. It shall not default to pass.</li></ul> | Fail-closed on screening outage. This is the one step where degraded availability must block rather than proceed. |
| **18.** As an operations officer, I want to tune thresholds and lists without waiting for a release, so that review volume can be managed day to day. | <ul><li>Extraction confidence thresholds, face match thresholds, cooling-off periods, and the supported bank list shall be runtime-configurable.</li><li>A configuration change shall require a second approver before taking effect.</li><li>Every change shall be recorded with the previous value, the new value, both operator identities, and the effective timestamp.</li><li>Changes shall apply only to applications submitted after the effective timestamp, and shall not re-evaluate applications already decided.</li><li>The system shall expose the configuration set currently in force, and shall support reverting to the previously active set.</li><li>A threshold change exceeding the configured safety bound shall be rejected regardless of approval.</li></ul> | Safety bounds stop a well-intentioned tuning change from effectively disabling a control. |

## Out of scope

| Item | Rationale |
|---|---|
| Institutional and corporate account opening | Requires authorised signatory and beneficial ownership handling. Separate initiative. |
| Joint and custodial accounts | Multi-party identity verification not supported by the MVP flow. |
| Account closure and dormancy reactivation | Existing processes remain unchanged. |
| Migration of in-flight applications from the legacy form | Legacy applications complete on the legacy path. Cutover is date-based. |

## Dependencies and assumptions

| Type | Detail | Owner |
|---|---|---|
| Dependency | Identity document extraction and liveness service contracted with the required accuracy and availability terms | Product / Procurement |
| Dependency | Event pipeline capable of fifteen-minute query latency | Data Analyst |
| Assumption | The applicant has a front-facing camera and grants camera permission | Product |
| Assumption | Manual review is staffed to meet the one-business-day service level target at projected volume | Operations |

## Open questions

| # | Question | Owner | Needed by |
|---|---|---|---|
| 1 | What fuzzy-match tolerance applies to the bank account holder name comparison? | Compliance | Design sign-off |
| 3 | What is the retention period for liveness artefacts on a rejected application? | Compliance | Development start |
| 5 | Which operational alert channel receives screening outage notifications? | IT Development | Pre-launch |

## Non-functional requirements

| Area | Requirement |
|---|---|
| Performance | Identity document extraction shall return within six seconds at the 95th percentile. Liveness and face match shall return within eight seconds at the 95th percentile. |
| Availability | The onboarding journey shall target 99.5% monthly availability measured at the application entry point. |
| Degradation | Unavailability of extraction or liveness shall present a retry-later state preserving application progress. Unavailability of screening shall hold the application pending. |
| Capacity | The journey shall sustain 400 concurrent applications and a peak of 6,000 submissions per day without breaching the stated latency targets. |
| Auditability | Every decision affecting an application outcome shall be reconstructible from the append-only audit log without reference to application logs. |
| Accessibility | All steps shall meet WCAG 2.2 Level AA on both Mobile and Desktop. |
| Localisation | All applicant-facing text, including reason-code messages, shall be available in Indonesian and English, selectable at the first step. |

## Rollout plan

| Phase | Scope | Exit criteria |
|---|---|---|
| 1: Internal | Staff applications only, on a hidden entry point. Every application reviewed manually regardless of automated outcome. | 50 applications completed end to end. Extraction accuracy measured per field. No unresolved severity-one defect. |
| 2: Limited | 5% of new applicants on Mobile only. Automated clearance enabled. Manual queue staffed for full volume. | Automated clearance rate at or above 70%. Median approval within two business days. Spoof detection validated against seeded attempts. |
| 3: Expanded | 50% of new applicants on Mobile. Desktop enabled at 5%. | Automated clearance at or above 78%. Reason-code distribution reviewed with Compliance and Customer Service. Funnel dashboard complete for all seven steps. |
| 4: General | 100% of new applicants on both platforms. Legacy form remains reachable by direct link. | Targets in the Success Metrics section met for thirty consecutive days. |
| 5: Legacy retirement | Legacy form withdrawn. In-flight legacy applications complete on the legacy path. | Zero legacy submissions for fourteen consecutive days. Operations sign-off obtained. |

Rollback at any phase shall return the affected traffic share to the legacy form. In-flight applications on the digital journey shall continue to completion rather than be transferred.

## Glossary

| Term | Definition |
|---|---|
| Application reference | The identifier assigned when an application record is created. Stable across resume and used as the sole analytics join key. |
| Indeterminate outcome | A step result that is neither a pass nor a fail and therefore routes to manual review. |
| Reason code | A structured, stable identifier for a specific failure or block condition, paired with a plain-language message. |
