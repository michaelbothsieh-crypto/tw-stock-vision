---
description: End-to-end workflow to scope, build, test, and ship a SaaS MVP quickly.
---

1. **Plan the scope**
   - Goal: Convert the idea into a clear implementation plan and milestones.
   - Notes: Define problem, user persona, MVP boundaries, and acceptance criteria before coding.
   - Recommended Skills: brainstorming, concise-planning, writing-plans

2. **Build backend and API**
   - Goal: Implement the core data model, API contracts, and auth baseline.
   - Notes: Prefer small vertical slices; keep API contracts explicit and testable.
   - Recommended Skills: backend-dev-guidelines, api-patterns, database-design, auth-implementation-patterns

3. **Build frontend**
   - Goal: Deliver the primary user flows with production-grade UX patterns.
   - Notes: Prioritize onboarding, empty states, and one complete happy-path flow.
   - Recommended Skills: frontend-developer, react-patterns, frontend-design

4. **Test and validate**
   - Goal: Catch regressions and ensure key flows work before release.
   - Notes: Use go-playwright when the product stack or QA tooling is Go-based.
   - Recommended Skills: test-driven-development, systematic-debugging, browser-automation, go-playwright

5. **Ship safely**
   - Goal: Release with basic observability and rollback readiness.
   - Notes: Define release checklist, minimum telemetry, and rollback triggers.
   - Recommended Skills: deployment-procedures, observability-engineer, postmortem-writing
