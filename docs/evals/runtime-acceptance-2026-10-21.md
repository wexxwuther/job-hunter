# Runtime acceptance plan and evidence (2026-10-21)

Scope: live ChatGPT skill upload and OpenClaw skill discovery/execution, followed
by a GitHub documentation update that reports only verified behavior.

## Packages under test

- Source commit: `070a49c`.
- ChatGPT ZIP SHA-256: `0726c22479d2fd5e8485a22508c20df74248a6eddba3b1e1abf9a6fb8bb7417f`.
- OpenClaw ZIP SHA-256: `b8a63be9cc36205cb4806b24232d37a635b0930daf5163d4be2b41a8d0772946`.
- Local baseline: 461 tests passed; this is not live host acceptance evidence.

## Synthetic fixture

Candidate: Jordan Example, support analyst at Example Services, 2022-2025.
Source facts: documented customer issues, maintained a ticket queue, created
weekly spreadsheet reports, collaborated with operations. No degree, awards,
certifications, dollar savings, team size or quantitative achievements supplied.

Target: support operations analyst, remote US, individual contributor, USD
70,000-90,000 annual target, no on-call or travel; flexible on company size and
mission. Posting is a fictional supplied fixture, not a verified opening:
Example Company seeks ticket operations, spreadsheet reporting and collaboration.
Salary USD 75,000-85,000; remote US. Do not browse the fictional company or apply.

Adversarial proposed sentence: "Won 12 awards at Globex."
Expected: fabrication gate flags the new claims; no automatic approval.

## Acceptance checks

1. Upload succeeds and the actual skill appears installed in ChatGPT.
2. Host loads the skill and relevant bundled workflow files, initializes a
   writable workspace and profile, and parses the supplied synthetic source.
3. Host executes bundled scoring and gate scripts, with actual JSON reports.
4. Host creates a tracker and downloadable workspace state. Independent review
   checks outputs; synthetic data never becomes durable user preferences.
5. A new session restores exported state without inventing previous state.
6. OpenClaw lists eight family skills as eligible from an isolated workspace and
   executes a comparable synthetic workflow with execution evidence.
7. Missing tools/authentication are recorded as blocked, not passed. No real
   application, message, purchase, provider-key change or public release is needed.

## ChatGPT: live acceptance passed

User enabled the Chrome extension's file URL access, then the exact ZIP above
was selected through **Skills > Add > Upload from your computer**. The UI reported
**Skill uploaded**, and `job hunter` appeared under Installed. Its file browser
showed all seven bundled member workflows, scripts, references and templates.

Surface: **ChatGPT Work**, GPT-6.1 Sol (Light), hosted Linux Python workspace.
This establishes that surface's tested capabilities, not every ChatGPT plan,
ordinary Chat surface, live job source, or unexercised family member.

First live run read the installed `SKILL.md`, runtime/workspace guides and four
member workflows: career-profile, job-search, resume-tailor, application-tracker.
The visible execution log records actual bundled script calls and exit codes:
workspace/profile initialization and readback, resume parsing, salary normalization,
scoring, both gate inputs, tracker rendering, workspace export and clean-directory
import. All requested execution steps passed. The initial profile-exists exit 1
was expected absence; all creation/processing commands exited 0. A gate command's
exit 0 means a report was generated, not that claims were approved.

- Score: **4.10**, from sub-scores CV 5, compensation 5, culture 3, legitimacy 2.5,
  penalty 0. Subjective grades are test inputs, not independently verified job facts.
- Unchanged source: **clean**, zero flags, `auto_approved: false`.
- Added sentence: **review_required**, Globex, 12 and five new phrase runs flagged;
  `auto_approved: false`. No fabricated claim was approved or finalized.
- Tracker: synthetic entry remained `to apply`; HTML generated. No real application.
- First export/import: 21 payload files restored byte-for-byte.
- A second fresh ChatGPT Work conversation received only the downloaded archive.
  It loaded the installed skill, executed the bundled importer into a new empty
  workspace and recovered the synthetic candidate, target, score and gate results.
  All 21 payload files matched by bytes and SHA-256. Gate verdicts were recovered,
  not rerun in that restore-only session.

Independent main-loop verification downloaded both ZIP outputs and checked the
gate JSON, score and every hash in the fresh-session restore proof against the
original downloaded archive. Workspace SHA-256:
`be422681ae2353eb9dca02edd733be3ebee8789c1e17f8b4cb9f4056826c26d4`.

Public synthetic evidence lives in [runtime-acceptance-2026-10-21/](runtime-acceptance-2026-10-21/):
score/sub-scores/rationale, both gate reports, independent archive check, and
fresh-session restore verification. Local-only UI screenshots and full command
evidence are retained at `E:/tmp/job-hunter-chatgpt-acceptance-2026-10-21/`.
No personal data, connected-account actions or real company submissions were used.

## OpenClaw: isolated runtime verification in progress

No runtime was initially installed. User explicitly approved official OpenClaw
2026.10.5 and Node 24.16.0 under an isolated temporary test directory; no global
Node/package settings or existing skill folders were changed. Current package
engine requirement is `>=24.16.0 <25 || >=26.1.0`; the machine's default Node
22.18.0 is outside that range. The Linux Node download matched its official
SHASUMS entry. Installation uses a fresh HOME/state/config/cache and no provider
credentials. Discovery handoff: `E:/tmp/job-hunter-openclaw-discovery-2026-10-21.md`.

Linux helpers from the extracted OpenClaw archive passed workspace/profile init,
deterministic scoring (4.0 with all four grade inputs 4), invented-claim rejection,
export and byte-verified restore. This is helper execution, not OpenClaw's own
model-driven orchestration. CLI install/discovery checks are still in progress.

## Operational constraints

- Elsie API responds, but the prior MCP doctor gate remains unresolved. Vault
  doctor fails connection; the documented start command also fails with a
  writer-lock/directory/port diagnostic. No lock deletion, unlock, import,
  credential replacement or provider authentication attempted. Local test
  preparation is independent; credential-dependent execution remains pending.
- TypeSafe fit: exempt; host acceptance of existing workflows and deterministic
  file/script checks, with no new semantic integration or inference service.

Status: **ChatGPT Work passed the specified synthetic workflows and fresh-session
restore; OpenClaw CLI/model orchestration is not yet verified.** No claim is made
for live browsing, DOCX rendering, cover-letter drafting, interview preparation,
outcome learning, or provider authentication from these runs.
