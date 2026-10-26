# Working agreement

This repository contains an HTML/CSS visual synthesizer and Python standard-library development tools. Follow current Issue scope and record design decisions.

- Read README.md and docs/plan.md before changing product code.
- Treat user-confirmed requirements, proposed decisions, and measured results as different states. Never label a proposal approved or a test passed without evidence.
- Do not copy the rejected PHOSPHOR prototype, its styling, generated markup, branding, screenshots, or deployment configuration into this project.
- Follow requirement IDs and update their acceptance checks when scope changes.
- Resolve mathematical meaning, actual input behavior, and displayed precision before styling a control.
- Do not add JavaScript or TypeScript anywhere in the current source, including build tools, tests, fixtures, or package manifests. Do not require Node. Use Python standard-library development tools. Do not introduce a framework, Canvas renderer, SVG signal renderer, WebAssembly, or polyfill to make a pure CSS claim pass. If the proposed HTML/CSS-only requirement is infeasible for a requested interaction, record the conflict and alternatives.
- Do not build a decorative control that implies an unsupported interaction. A scroll input must look and behave like a scroll input.
- Keep mathematical model calculations independent of viewport aspect ratio unless distortion is explicit.
- Use a focused technical spike for an uncertain browser capability. Record exact browser/OS/viewport and the result; an iframe-width test is not a mobile-touch test.
- Do not infer performance from the absence of JavaScript. Measure the selected scene on a stated device.
- Do not add deployment, public access, telemetry, external fonts, or third-party scripts without the user requesting that scope.
- Do not invent approval gates for routine reversible work. Do keep open product decisions visible and do not silently promote assumptions into requirements.
- Create or select an Issue before implementation. Use an Issue-specific branch and a reviewable pull request; do not put feature work directly on main.
- Write Issue titles/bodies and PR titles/descriptions in Japanese. Reference the relevant Issue and report observed checks and unverified limits accurately.
