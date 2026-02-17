---
description: Structured workflow for baseline AppSec review and risk triage.
---

1. **Define scope and threat model**
   - Goal: Identify critical assets, trust boundaries, and threat scenarios.
   - Notes: Document in-scope targets, assumptions, and out-of-scope constraints.
   - Recommended Skills: ethical-hacking-methodology, threat-modeling-expert, attack-tree-construction

2. **Review authentication and authorization**
   - Goal: Find broken auth patterns and access-control weaknesses.
   - Notes: Prioritize account takeover and privilege escalation paths.
   - Recommended Skills: broken-authentication, auth-implementation-patterns, idor-testing

3. **Assess API and input security**
   - Goal: Detect high-impact API and injection risks.
   - Notes: Map findings to severity and exploitability, not only CVSS.
   - Recommended Skills: api-security-best-practices, api-fuzzing-bug-bounty, top-web-vulnerabilities

4. **Harden and verify**
   - Goal: Translate findings into concrete remediations and retest.
   - Notes: Track remediation owners and target dates; verify each fix with evidence.
   - Recommended Skills: security-auditor, sast-configuration, verification-before-completion
