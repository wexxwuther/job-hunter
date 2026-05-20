# Follow-up Email Templates and Cadence

When and how to follow up after a job application or interview. The skill drafts emails using `scripts/draft_followup.py`; this reference documents the *why* behind the patterns so you (and the agent) can adapt them to specific situations.

## Two scenarios, two templates

### Check-in: 7-10 business days after applying, no response

**The principle:** the hiring team is busy; your application is one of many; a polite, specific check-in puts you back at the top of the inbox without making you look impatient or entitled.

**The template (`check_in`):**

- **Subject:** "Following up — {role} at {company}"
- **Opening:** state the role and applied date in one short sentence
- **Middle:** one specific qualification that maps to a stated requirement (this is the part the user must personalize — generic check-ins get ignored)
- **CTA:** offer to share additional examples or jump on a brief call
- **Sign-off:** standard

### Thank-you: 24-48 hours after a phone screen, onsite, or other interview

**The principle:** thank-you notes are table stakes for many hiring managers — sending none is a soft negative signal. But the format matters more than the existence: a generic "thanks for your time" is forgettable; a thank-you that references a specific thing discussed shows you were engaged.

**The template (`thank_you`):**

- **Subject:** "Thank you — {role} at {company}"
- **Opening:** thank them, name the role, anchor the time ("yesterday" / "earlier today" / "on May 18")
- **Middle:** reference one specific thing discussed — a problem they raised, a project they mentioned, an architecture decision you went deep on
- **Bridge:** reiterate one strong qualification connecting to that topic
- **CTA:** offer to provide anything else as they evaluate
- **Sign-off:** standard

## Cadence rules

| Scenario | When to send | Frequency cap |
|---|---|---|
| Post-application check-in | 7-10 business days after applying | 1 check-in. Send a shorter second touch 5-7 business days later only if you have something new to add (a recent accomplishment, an article relevant to their work). |
| Post-interview thank-you | Within 24-48 hours of the interview | 1 thank-you per interview round. Subsequent contact should be timed to their stated next-step timeline. |
| After 21 days of no response | Move on. Update tracker.json status to `no_response_after_21d`. |

## What the script does NOT do

- **Send the email.** The user copy-pastes. The skill never owns the send step. (See `tests/test_draft_followup.py::test_no_smtp_or_send_imports_in_script` — this is a load-bearing safety boundary.)
- **Auto-personalize.** The script emits a structurally correct draft with placeholders (`[Add one specific qualification...]`, `[Add one specific thing discussed...]`) that the user must fill in. Generic content there is worse than no follow-up.
- **Track follow-up send dates.** The agent appends to DECISIONS.md when a follow-up is drafted; the user updates DECISIONS.md or tracker.json when they actually send it. The skill doesn't try to be a CRM.

## Common mistakes the script's placeholders try to prevent

| Mistake | Why it backfires | What to do instead |
|---|---|---|
| "Just wanted to check in" with no specifics | Reads as needy + adds zero information for the hiring manager | Reference one specific thing about the role or company |
| "Thanks for your time" with no detail | Looks like a template you sent to 30 companies | Mention one concrete thing from the conversation |
| Re-sending the same email weekly | Crosses from persistent to annoying after the second touch | Cap follow-ups at 2 per application; move on after 21d silence |
| Asking for "any update" in a check-in | Puts work on the hiring manager and signals you're just waiting | Offer to provide something (a writing sample, a code review of a relevant project, anything that adds value) |

## Sources

These patterns are drawn from hiring-advisor consensus, not invention. Specifically:

- [Indeed Career Advice — How To Write a Follow-Up Email After a Job Application](https://www.indeed.com/career-advice/finding-a-job/follow-up-email-after-application)
- [The Muse — How to Follow Up on a Job Application](https://www.themuse.com/advice/how-to-follow-up-on-a-job-application-an-email-template)
- [Robert Half — How to Follow Up on a Job Application](https://www.roberthalf.com/us/en/insights/landing-job/should-you-follow-up-after-applying-for-a-job)
- [Teal HQ — How to Follow Up (Email Templates)](https://www.tealhq.com/post/how-to-follow-up-on-a-job-application-email-template)

The "7-10 business days" timing and the 2-follow-up cap are conventional across these sources. The "+30% response rate" figure is sometimes cited (e.g., CareerBldr) but should be treated as directional guidance, not a precise benchmark — it's drawn from sales-context studies that don't perfectly translate to job-applicant outbound.
