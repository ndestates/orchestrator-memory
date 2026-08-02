"""Phase 0 safety-net tests for scripts/customize-skills-for-project.py.

Pins the decontamination behavior: universal "Project Template" rewrite, the
manifest-name-wins title rule (added this session), and the EXCLUDE_SKILLS guard
that keeps self-referential template tooling from being corrupted.
"""

from __future__ import annotations


def _write_manifest(target, name):
    d = target / ".claude"
    d.mkdir(parents=True, exist_ok=True)
    (d / "project-manifest.yaml").write_text(
        f'project:\n  name: "{name}"\nstack:\n  framework: "generic"\n',
        encoding="utf-8",
    )


def test_expand_and_apply_pairs(customize_mod):
    ctx = {"title": "Acme", "slug": "acme"}
    assert customize_mod.expand_placeholders("hi {title}", ctx) == "hi Acme"
    text, n = customize_mod.apply_pairs("a Project Template b", [["Project Template", "{title}"]], ctx)
    assert text == "a Acme b" and n == 1


def test_universal_replacement_rewrites_project_template(customize_mod, target, tmp_path):
    _write_manifest(target, "Acme")
    profile = {"project_title": "Generic App"}
    ctx = customize_mod.profile_context(target, profile)
    f = tmp_path / "SKILL.md"
    f.write_text("# Copilot Instructions — Project Template\n", encoding="utf-8")
    n = customize_mod.apply_profile_to_file(f, profile, ctx)
    assert n >= 1
    assert "Project Template" not in f.read_text(encoding="utf-8")
    assert "Acme" in f.read_text(encoding="utf-8")


def test_profile_context_manifest_name_wins(customize_mod, target):
    # Real manifest name beats the generic stack-profile title.
    _write_manifest(target, "Mailchimp")
    ctx = customize_mod.profile_context(target, {"project_title": "Python Flask App"})
    assert ctx["title"] == "Mailchimp"


def test_profile_context_falls_back_to_profile_title_when_placeholder(customize_mod, target):
    _write_manifest(target, "Project Template")  # uncustomized placeholder
    ctx = customize_mod.profile_context(target, {"project_title": "Python Flask App"})
    assert ctx["title"] == "Python Flask App"


def test_collect_skill_files_excludes_self_referential(customize_mod, tmp_path):
    skills = tmp_path / ".grok" / "skills"
    for name in ("foo", "orchestrator-deploy", "template-decontaminate"):
        d = skills / name
        d.mkdir(parents=True)
        (d / "SKILL.md").write_text("x", encoding="utf-8")
    collected = {p.relative_to(skills).parts[0] for p in customize_mod.collect_skill_files(skills)}
    assert "foo" in collected
    assert "orchestrator-deploy" not in collected
    assert "template-decontaminate" not in collected
