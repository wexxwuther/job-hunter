# ATS Formatting Guide

ATS (Applicant Tracking System) software parses resumes before a human sees them. Common ATS
products: Workday, Greenhouse, Lever, iCIMS, Taleo, Jobvite, ADP, BambooHR, SmartRecruiters,
Ashby. Behaviors vary, but the safe baseline below works across all of them.

## Format that parses cleanly

**File type**

- **.docx** is the safest universal choice. Most ATS parse it natively.
- **PDF** works on modern ATS but older Taleo/iCIMS sometimes mangle it. If the job posting
  doesn't specify a format and uses an older ATS (visible in the URL — e.g., `*.taleo.net`,
  `*.iCIMS.com`), prefer .docx.
- **.txt** parses perfectly but loses formatting; only use if the posting demands it.
- **.rtf / .pages / .odt** — risky, often misparsed. Convert to .docx first.

**Page setup**

- Single column. ATS read top-to-bottom, left-to-right. Two-column layouts get scrambled.
- 0.5"-1" margins. Sub-0.5" can be truncated.
- 10-12 pt body, 12-14 pt headers. Smaller may not parse.
- Standard fonts: Arial, Calibri, Helvetica, Georgia, Times New Roman. Avoid custom or unusual
  fonts — they may not embed, and substitution can shift line breaks.

**Structure**

- Use standard section headings exactly: **Summary**, **Experience** (or **Work Experience**),
  **Education**, **Skills**, **Certifications**, **Projects**. ATS keyword-extractors look for
  these literal strings. Cute headings ("Where I've Made an Impact") may not be recognized as a
  Work Experience section.
- Date format: `MMM YYYY - MMM YYYY` (e.g., `Jan 2022 - Mar 2024`) or `MM/YYYY - MM/YYYY`.
  Avoid creative date formats.
- Job title on its own line, company on its own line. Don't combine them in one bolded blob.

## What breaks ATS

- **Tables** — ATS often read tables row-by-row across columns, producing garbled output.
  Especially deadly for skills tables and date/title side-by-side layouts.
- **Text in headers/footers** — many ATS skip header/footer content entirely. Don't put contact
  info or critical content there.
- **Text inside images or graphics** — never parsed.
- **Text boxes** — varies; risky. Use plain inline text.
- **Embedded SmartArt, icons, infographics** — never parsed.
- **Special characters in section headings** — `▪ Experience` may not match `Experience`.
  Stick to plain text headings.
- **Multi-column layouts** — almost always misparse.
- **PDFs with form fields or scanned-image PDFs** — never parsed.

## Keyword discipline

ATS rank resumes by keyword match against the job description. To improve match rate:

1. Mirror the job description's exact terminology. If the JD says "Kubernetes," don't write
   "K8s." If the JD says "Customer Relationship Management (CRM)," write the full phrase at
   least once even if you also use "CRM."
2. Include both acronyms and expansions on first use: "Software-as-a-Service (SaaS)."
3. Put high-value keywords in section headings, the summary line, and the Skills section.
   Some ATS weight these higher than body text.
4. **Do NOT keyword-stuff** — modern ATS (Workday, Greenhouse, Ashby) detect repetition and
   penalize it. Also, a human reads the resume eventually. Aim for 2-4 organic occurrences of
   the top keywords across the resume, not 15.
5. **Never use white-on-white keyword tricks.** ATS catch them, and they're considered fraud.

## Quick pre-submit checklist

Run this before producing the final file:

- Single column, no tables
- Standard section headings (Summary / Experience / Education / Skills / etc.)
- All contact info in the body, NOT in headers/footers
- Dates in MMM YYYY format, consistent across all entries
- File saved as .docx (or PDF if the posting requires it and the ATS is modern)
- Keywords from the JD appear naturally in the summary and skills section
- File name follows pattern: `Resume_[CompanyName]_[RoleShorthand].docx`
- No graphics, icons, charts, or text boxes
- Font is Arial / Calibri / Helvetica / Georgia / Times New Roman

## When the posting requires plain text

A few legacy ATS (and some federal/gov postings) require copy-paste into a text field. For these:
- Convert to .txt (Save As Plain Text in Word)
- Remove all bullet characters (`•`, `▪`, `▸`) — replace with `-` or nothing
- Use blank lines instead of indentation to separate sections
- Preview the text by opening it in Notepad before pasting

## Verifying your output

If you want to sanity-check what an ATS sees, use a free parsing preview:
- **Jobscan** (jobscan.co) — paste resume + JD, get a match score
- **Resume Worded** — similar
- These are external services, treat their output as suggestive only.
