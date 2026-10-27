# Review materials that can be reproduced

Create a short evidence record for each tested case: source revision, exact package SHA-256, case ID, host surface,
account/fixture description without secrets, prompt, expected operations and
arguments, expected result, observed result, status, and evidence location.
Use Passed, Failed, Blocked, or Not run. A drafted expectation is Not run.

OpenAI initial MCP review needs five distinct positive and three negative
cases. Positive cases should cover the core workflow, a meaningful variation,
a valid boundary, and any supported multi-step operation. Use exact expected
tools and observable outputs without putting tool-selection instructions in
the natural user prompt. Negative cases should plausibly resemble the product
but require refusal, clarification, or a safe explanation rather than action.
A valid empty result or authentication failure is not an unsupported-workflow
negative test. Keep each server's cases with its own configuration.

Claude connector materials need at least three useful working examples;
exercise every tool and cover permission/error behavior too. Do not copy the
OpenAI count as a Claude requirement. For a skills-only plugin, evaluate the
skill's assistance rather than inventing MCP tools.

## Recording and screenshots

Help the creator rehearse a short sequence from real cases. Use an existing
working development connection; do not force a public draft upload just to
record. Confirm a recording capability first: browser control and screenshots
alone cannot produce video. If unavailable, give precise recording steps and
help the creator use their recorder. Capture actual prompts, results, and one
relevant boundary; keep unrelated private data and credentials off-screen.
Play the recording, verify readability, host it at the chosen accessible
location, then verify that reviewers can play the actual recording without
private access. A local video or script is not a verified recording URL.

Capture screenshots only when useful or required. Claude UI connector images
follow A8's count/size and separate-prompt rules. For usability evidence, show
the real installed workflow and a result. Label report screenshots as reports,
not installed plugin behavior. Never fabricate a host screenshot.

## Access and ownership facts

Prepare sample data and sufficient permissions for a dedicated reviewer account.
Confirm sign-in works through the reviewer route, including any subscription.
Put access details only in secure review fields; don't include them in a ZIP,
public README, case description, or report. Never use the creator's personal
account. Check the destination's current allowed sign-in methods.

The creator supplies legal identity, commerce behavior, supported countries,
and data-practice decisions. Draft policy text from those facts, then verify
the published pages. Do not convert unknown retention or sharing into reassuring
claims. Legal attestations are separate from code or package validation.

