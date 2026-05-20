# North-Star Profile Questions

Five questions whose answers don't typically appear on a resume but heavily influence which
postings are worth pursuing. Answers persist across sessions in the user's workspace as
`.job-hunter-profile.md`, so subsequent runs don't re-ask.

This is the "career-ops insight" we adopted from the upstream review:
> "The first evaluations won't be great. The system doesn't know you yet."

A skill that re-parses the resume on every run and forgets everything else is a tool that
resets. The 5-question profile is what makes the tool accumulate context.

## The five questions

### 1. Target archetype (or "what KIND of role")

> "Beyond your job title, what kind of role do you actually want? Are you targeting
> hands-on individual-contributor work, technical leadership, people management,
> founding/zero-to-one, or something else?"

Rationale: a "Senior Backend Engineer" resume could match an IC role at Stripe, a tech lead
role at a startup, or an engineering manager role at a mid-sized company — three very
different applications. Without this, the skill has to guess from title alone.

How it feeds scoring: `cv_match` and `cultural_signals` both shift based on archetype.

### 2. Deal-breakers

> "What absolutely won't work for you? Examples: no on-call, no travel, no in-person
> 5-days-a-week, no commission-only, no equity-only, no government clearance work, no
> defense, no crypto, no gambling, no specific company X."

Rationale: deal-breakers turn the legitimacy/match scores into hard filters. A 5/5 match on
a defense contractor doesn't help a user who has explicitly excluded defense work.

How it feeds scoring: any posting that hits a deal-breaker gets `red_flags_penalty: 1.0`
(full multiplier kill) regardless of other scores.

### 3. Company-size preference

> "Pre-seed / Series A startup, Series B-C, Series D+ late stage, public mid-cap,
> public large-cap, or no preference? Are you allergic to any of these?"

Rationale: stability vs. upside vs. process tolerance vary 10x across these buckets. A
user who's "anti-late-stage-process-bureaucracy" is wasting their tailoring time on
Microsoft, regardless of how well the role matches their resume.

How it feeds scoring: shifts `cultural_signals` by ±1 point based on whether company size
matches preference.

### 4. Mission vs. comp priority

> "When you have to choose between 'role I'm excited about' and 'comp matches my target',
> which wins? (Common answers: 'mission within ±15% of comp', 'comp first always',
> 'mission first if at least 80% of comp', 'I don't know — let me see real tradeoffs first'.)"

Rationale: this lets the skill weight `comp_vs_target` versus `cultural_signals` for the
specific user. A "mission first" user shouldn't see comp-aligned-but-uninspiring roles
ranked above mission-aligned but slightly-under-comp roles.

How it feeds scoring: shifts the relative weight between `comp_vs_target` and
`cultural_signals` within the user's run; weights live in `score_posting.py` constants
unchanged (the script doesn't read the profile — the agent applies a soft re-rank).

### 5. Tolerance dimensions

> "Three quick yes/no questions: are you OK with (a) on-call rotation, (b) >20% travel,
> (c) office-required (in-person 4-5 days)? Saying 'depends' is fine — note what it
> depends on."

Rationale: these are softer than deal-breakers but still material. Many users say no to
on-call but would say yes for the right comp; this captures the conditional.

How it feeds scoring: each "no" subtracts 0.5 from `cultural_signals` for postings that
require that thing; "depends" flags the posting for user attention rather than auto-scoring.

## When to ask

- **First run** (no `.job-hunter-profile.md` in workspace): ask all 5 questions before
  Phase 2 search. This is part of Phase 1 — gate the search until you have the answers.
- **Subsequent runs:** read the existing profile, ask "anything changed since last time?"
  briefly, then proceed. Don't re-walk the user through 5 questions every session.
- **User declines to answer:** save what you have, mark unanswered fields as `unknown`,
  and proceed. The skill should still work without a profile; it just won't accumulate
  context.

## When the profile feels stale

If the profile is more than 90 days old, mention it once on resume: "your North-Star
profile is from 3+ months ago — want to update anything?" Don't be pushy.

## Privacy

The profile lives in the user's workspace folder as `.job-hunter-profile.md`. It is
NEVER committed to the skill repo or to `~/.claude/skills/`. The dot-prefix is
deliberate — most users' `.gitignore` patterns skip dot-files, so accidentally adding it
to a personal repo is harder. The skill should remind the user of this once when first
writing the file, then never again.

If the user explicitly asks to delete their profile, delete the file and confirm. Do not
keep "backups" the user didn't ask for.
