"""Install-readiness guards: catch breakage that only surfaces once each
family member is installed as a SEPARATE directory (not in the monorepo).

The trap: a member SKILL.md that references a sibling skill by a monorepo-
relative path (e.g. `job-hunter/references/...`) resolves in the repo but breaks
once installed at ~/.claude/skills/<member>/, where sibling skills are not
subdirectories. Every member must be self-contained on its references."""
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
MEMBERS = ["job-hunter", "career-profile", "job-search",
           "resume-tailor", "application-tracker", "outcome-learning"]
SIBLINGS = [m for m in MEMBERS]


def test_no_member_references_a_sibling_by_monorepo_path():
    """No SKILL.md may contain a path like `<sibling>/references/...` or
    `<sibling>/scripts/...` — those don't resolve post-install."""
    offenders = []
    for m in MEMBERS:
        text = (REPO / m / "SKILL.md").read_text(encoding="utf-8")
        for sib in SIBLINGS:
            if sib == m:
                continue
            # a path segment that starts with the sibling name + a subdir
            for pat in (rf"{re.escape(sib)}/references/", rf"{re.escape(sib)}/scripts/",
                        rf"{re.escape(sib)}/evals/"):
                if re.search(pat, text):
                    offenders.append(f"{m}/SKILL.md references {sib} by path ({pat})")
    assert not offenders, "monorepo-relative sibling references break post-install:\n" + "\n".join(offenders)


def test_every_member_ships_the_workspace_contract():
    """Each member that consumes the shared workspace must carry its own copy
    of the contract so it's self-contained once installed."""
    for m in MEMBERS:
        contract = REPO / m / "references" / "workspace-contract.md"
        assert contract.exists(), f"{m} is missing references/workspace-contract.md (won't resolve post-install)"


def test_each_member_skill_md_has_scripts_it_references():
    """Every `scripts/<name>.py` a member's SKILL.md names must exist in that
    member's own scripts/ dir (no reaching into a sibling for a script)."""
    missing = []
    for m in MEMBERS:
        text = (REPO / m / "SKILL.md").read_text(encoding="utf-8")
        for script in set(re.findall(r"scripts/([a-z_]+\.py)", text)):
            if not (REPO / m / "scripts" / script).exists():
                missing.append(f"{m}/SKILL.md names scripts/{script} but it's not in {m}/scripts/")
    assert not missing, "members reference scripts they don't own:\n" + "\n".join(missing)
