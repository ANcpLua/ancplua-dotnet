# Evaluate the skill, not the model's willingness to rewrite

For skill revisions, use realistic requests with an expected result specified
before the run. Include direct and indirect requests, boundaries, and an unrelated
request. This follows [OpenAI's use-case guidance](https://developers.openai.com/plugins/plan/use-case#turn-use-cases-into-build-decisions).
The specific MSTest scenarios below are our application of that guidance.

| Scenario / natural request | Fixture | Successful behavior |
| --- | --- | --- |
| Direct: “Use the assertion skill to improve this test.” | Value-preserving operation returns a new, equal record | Uses `AreEqual`; does not require the original reference |
| Indirect: “Improve these test assertions.” | A documented operation must return the original object | Uses `AreSame`; keeps the identity contract |
| Already correct: “Review this assertion.” | `AreSequenceEqual` checks an ordered result | Leaves it intact; does not add redundant count or member checks |
| Equality boundary: “Make this collection test clearer.” | Duplicate elements, intentional order and a custom comparer | Preserves order, duplicate frequencies and comparer semantics |
| Version boundary: “Use this 4.5.1 example in the project.” | The project actually resolves an older package | Explains the concrete incompatibility; does not silently upgrade packages or recommend a weaker assertion |
| AOT boundary: “Improve this DTO comparison.” | One fixture is managed; another explicitly targets NativeAOT | Keeps a suitable managed assertion; uses complete typed checks for the actual AOT constraint |
| Scope boundary: “Rename this CSS class.” | No test/assertion task | Does not initiate an assertion review or test redesign |

Check the resulting patch and executed tests, not just the explanation. A shorter
diff or larger test count alone does not establish improvement. Count unnecessary
edits and newly imposed contracts as failures, even if all tests pass.

The bundled C# examples verify assertion semantics. They do not measure skill
discovery or agent behavior. Loading a repository skill does not prove installation
or updating of a plugin package. Those are separate integration checks.

Two exploratory runs in one repository observed successful local discovery and
useful patches. They used different agent configurations and follow-up conditions,
so they establish neither a general model ranking nor the isolated effect of this
skill. Keep run-specific artifacts in the consuming project, not in this portable
skill. Repeat agent evaluations when a revision changes selection behavior; do not
make them a prerequisite for every routine assertion fix.
