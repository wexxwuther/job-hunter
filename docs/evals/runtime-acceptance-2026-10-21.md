# Runtime acceptance evidence (2026-10-21)

Scope: live ChatGPT skill upload and OpenClaw skill discovery/execution, followed
by a GitHub documentation update that reports only verified behavior.

## Packages under test

- Source commit: `070a49c`.
- ChatGPT ZIP SHA-256: `0726c22479d2fd5e8485a22508c20df74248a6eddba3b1e1abf9a6fb8bb7417f`.
- OpenClaw ZIP SHA-256: `b8a63be9cc36205cb4806b24232d37a635b0930daf5163d4be2b41a8d0772946`.
- Local baseline at the package source: 461 tests passed; this is not live host
  acceptance evidence. After preserving concurrent job-search 1.1.1 updates, the
  merged source passed 479 tests (71.90 seconds).

The host tests below use the unchanged archives built from `070a49c`. Subsequent
job-search 1.1.1 construction-role/board updates are covered by the merged local
suite; they are not included in these exact host-tested archive hashes. Building
from a later source commit produces different package contents.

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
No real candidate data, job-site accounts or real company submissions were used.

## OpenClaw: workflow verified; CLI cleanup failed

No runtime was initially installed. User explicitly approved official OpenClaw
2026.10.5 and Node 24.16.0 under an isolated temporary test directory; no global
Node/package settings or existing skill folders were changed. Current package
engine requirement is `>=24.16.0 <25 || >=26.1.0`; the machine's default Node
22.18.0 is outside that range. The Linux Node download matched its official
SHASUMS entry. Installation uses a fresh HOME/state/config/cache and no provider
credentials. Discovery handoff: `E:/tmp/job-hunter-openclaw-discovery-2026-10-21.md`.

Actual OpenClaw `--version`, `skills list --json`, `skills info job-hunter --json`
and `skills check --json` exited 0 from a Linux ext4 prefix. All eight family
skills were eligible, model-visible and command-visible, sourced from the isolated
workspace, with no missing prerequisites. See `openclaw-discovery.json`. An earlier
E:-mounted Linux attempt ended with `skills list` exit 137; that attempt is not
counted as passed.

Linux helpers from the extracted OpenClaw archive passed workspace/profile init,
deterministic scoring (4.0 with all four grade inputs 4), invented-claim rejection,
export and byte-verified restore. This is helper execution, not OpenClaw's own
model-driven orchestration. User also approved one synthetic run through the
existing signed-in Codex app-server. Native Windows Node 24.16.0, OpenClaw
2026.10.5 and the matching official Codex plugin are installed; Windows version,
list/info/check and configuration validation all exit 0. All eight skills are
eligible and visible there too; see `openclaw-windows-preflight.json`.

The initial agent launch failed before inference: `owner-plugin-degraded`, with
null model/provider and no workflow outputs. Inspection identified a setup error:
loading the official npm plugin through `plugins.load.paths` gives it `config`
origin, which cannot register the registry-owned Codex harness. A managed local
path link also retained that classification. The documented registry installation
of `npm:@openclaw/codex@2026.10.5` corrected it: a fresh official runtime inspection
reports `global` origin, `trusted-official` provenance, harness `codex`, and no
diagnostics. Final config validation passes without warnings. The exact official
package's 177 files match the verified npm archive byte-for-byte. See
`openclaw-plugin-repair.json`. The initial failed launch is retained in
`openclaw-initial-runtime-error.json`; it is not a passing model test.

The one approved model run then executed through the native Codex app-server,
model `gpt-6.1-sol`, using the existing sign-in without copying credentials.
It read the orchestrator and four member workflows and actually launched the
bundled Python scripts sequentially. Main-loop inspection independently confirms:

- Profile initialization/readback and TXT resume text extraction completed.
- Salary normalized to USD 75,000-85,000 annually. Score **4.0** with the four
  supplied test grades all 4 and penalty 0; legitimacy was not independently checked.
- Unchanged resume: **clean**, zero flags. Invented sentence: **review_required**,
  seven flags including Globex and 12. Both `auto_approved` values are false.
- Tracker stayed `to apply`, with no applied date; HTML was generated.
- Export/import restored **18 payload files** into a new empty directory. Main
  independently compared every payload's bytes and SHA-256, excluding the manifest.
  Archive SHA-256: `fd7e7e51d93cda17bcb900e821e01565d033a9eaaca3f3b527f62a3c331e3807`.
- The retained log has 24 actual Python commands: two expected initial absence
  probes exited 1; every other Python command exited 0.

This is **not a clean overall OpenClaw pass**. The agent returned its final answer
and complete evidence, but `agent exec` exited **1** after 630.29 seconds with
`error.kind: cleanup`: "Agent runtime cleanup did not settle; state ownership
retained until this process exits." The specific release step could not confirm
Codex one-shot client cleanup. That initial Windows test used one model run;
the owner subsequently requested the cleanup fix and reruns recorded below.

Other observed limits: direct exec probes returned no output and no verifiable
exit status; terminal access was unavailable. The agent recovered using local
`node_repl` / Node `child_process` to launch Python, so direct shell-tool execution
is not proven by this run. TXT text extraction worked but returned empty section
metadata for the Markdown-style headings. HTML content/existence was checked,
without interactive browser testing. Restore happened inside this run, not in a
fresh OpenClaw session. Default export includes immediate `.job-hunter/` files;
arbitrary nested evidence directories are outside that default scope.

Public proof: `openclaw-agent-summary.json`, score and gate reports, and
`openclaw-independent-check.json`. Full local command and runtime evidence remains
under `E:/tmp/job-hunter-openclaw-test-2026-10-21/`. The cleanup issue is a remaining
Windows runtime limitation; the successful workflow outputs do not erase that
historical failure. The later Linux result is recorded separately below.

Read-only diagnosis found that the exact plugin conservatively marks cleanup
uncertain after native execution; this can explain the cleanup guard result,
but it is not a confirmed sole cause or an upstream-confirmed bug. A scoped
process snapshot found no surviving test-owned Node/Codex process. No process
termination or additional model run was used during that read-only diagnosis.

## Cleanup fix and Linux / WSL rerun

The owner requested a cleanup fix and rerun. The clean route uses the unchanged
official OpenClaw and Codex plugin 2026.10.5, Node 24.16.0, native **Linux Codex
0.160.0**, and `gpt-6.1-sol` through the existing native sign-in. A finite tool
allowlist disables native Codex commands; direct OpenClaw-owned read/write/exec
tools run the bundled Python helpers. See the [configuration](../../install/openclaw.md#codex-one-shot-cleanup-tested-linux--wsl-configuration).

The initial Linux setup timed out before inference while native state was being
initialized. A fresh native configuration and SQLite directory initialized in
3.38 seconds. Existing authentication was referenced; no credential bytes were
manually read, copied or logged. A later npm-launcher run completed the workflow
but still failed cleanup. Those failures remain local evidence, not passing runs.

A no-auth, no-model test of the real installed client and Codex established the
remaining cause: the npm launcher spawns native Codex as a descendant. POSIX
containment terminates that descendant, then the launcher mirrors its `SIGKILL`;
the transport correctly refuses `closed` for a signaled root. Selecting the
official native executable with supported `appServer.command` removes that extra
process. The comparison returned `uncertain` / `SIGKILL` for the npm launcher and
`closed` / exit 0 for the native executable, with native execution unobserved in
both. No cleanup guard was weakened. Three additional real-process fixtures kept
native-execution uncertainty and verified removal of a test-owned descendant.

The full native-binary run **exited 0**, `ok: true`, with no cleanup error after
260.59 seconds. Main independently checked:

- Profile initialization/readback, TXT parsing, salary USD 75,000-85,000, and
  score **4.0** with the four supplied grades all 4 and penalty 0.
- Unchanged gate **clean**, zero flags; invented gate **review_required**, eight
  flags including Globex and 12. Both `auto_approved` values are false.
- Tracker **to apply**, no applied date, and generated HTML content.
- **25 payload files** restored byte-for-byte with matching SHA-256 values.
  Export SHA-256: `e780674cb4d74eaa5c9876f1c360f648dd27bea9516d2bf364a1b7dfe54a7cb2`.
- All **71 installed skill files** still match the original tested archive;
  all **177 plugin files** match the SHA-512-verified official package.

The runtime recorded 47 read/write/edit/exec calls and one recovered missing-`rg`
probe. The final command log has 28 entries: 25 exit 0, two expected absence
probes exit 1, and the missing `rg` probe exit 127 followed by Python discovery.
An orchestration logger initially overwrote seven child records; main matched
the recovered records against actual captured child stdout and the executed
wrapper. No required helper failed. Archived command evidence is a pre-export
snapshot. The normalizer used the supplied USD hint and default annual period.
Host exec used `mode: full` for the authorized isolated synthetic fixture; the
finite tool list is not an enforced filesystem sandbox.

A second **fresh OpenClaw session** started in a different workspace containing
only the installed skills, task, and original exported ZIP. It executed the
bundled importer into a new empty destination, read the restored profile, score,
saved gates and tracker, and **exited 0** with no cleanup error in 121.76 seconds.
Its six exec calls had zero failures. Main independently verified all **25**
restored payloads against the original archive by bytes and SHA-256, confirmed
the new session ID and initial absence of profile/state, and checked that scoring
and gates were read from saved reports rather than rerun. See
`openclaw-linux-fresh-restore.json`.

Final postflight observed no matching test-owned process, removed the test-created
sign-in reference, and confirmed the original sign-in file remained present.
Both sessions' 71 installed skill files and all 177 plugin files still matched
their exact original archives. Native state, account files and raw account logs
are excluded from public evidence.

Public proof: `openclaw-linux-native-summary.json`, its score/gate reports, and
`openclaw-cleanup-regression.json`. Raw source/receipts are local under
`E:/tmp/job-hunter-openclaw-test-2026-10-21/linux-native-evidence/` and
`linux-native-workflow/`. Native Windows stdio remains uncertain in this version;
the passing route uses Linux under WSL2. Broader workflows remain outside scope.

## Publication verification

Source and evidence commit `50264fc` was pushed to the public repository. Its
[exact CI run](https://github.com/wexxwuther/job-hunter/actions/runs/39706919631)
passed all nine jobs: Ubuntu, macOS and Windows with Python 3.10, 3.11 and 3.12.
The acceptance record was read back from GitHub at that exact commit. This is
source/documentation publication; no compatibility release assets were created.

## Operational constraints

- Elsie's missing MCP service was recovered with the documented runtime start
  command, preserving the healthy API and applying no migrations. The scoped
  runtime doctor now passes; project tracking can be synchronized.
- Vault storage remains unverified: its earlier doctor/start attempts failed.
  No vault lock deletion, unlock, import or credential replacement occurred.
  The separately approved Codex test uses native user-home authentication through
  the official plugin; credentials are not copied into the test installation.
- TypeSafe fit: exempt; host acceptance of existing workflows and deterministic
  file/script checks, with no new semantic integration or inference service.

Status: **ChatGPT Work and OpenClaw on the documented Linux / WSL2 configuration
passed the specified synthetic workflow and fresh-session restore. Both later
OpenClaw CLI runs exited 0 with no cleanup error.** The historical native Windows
stdio limitation remains. No claim is made
for live browsing, DOCX rendering, cover-letter drafting, interview preparation,
or outcome learning from these runs.
