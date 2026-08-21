"""orchestrator — versioned installer CLI for the orchestrator agent template.

Commands materialize/upgrade the template surfaces into a target project from a
pinned release, decontaminate, run the contamination gate, and commit on a
branch + PR (never leaving a dirty tree). See the plan and README.
"""
