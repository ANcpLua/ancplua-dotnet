# Test project and CI discovery

Read the existing test projects, shared MSBuild files and exact CI command before
creating another project. Reuse the intended project; restore a missing
`ProjectReference` or solution/filter entry when that is the actual defect.

For a new project, use the [native stack](native-stack.md) and existing target
framework/package policy. Let `MSTest.Sdk` own framework, adapter and MTP
registration. Add the production `ProjectReference`; shared test helpers have
their own library boundary. Do not introduce VSTest, duplicate SDK-owned package
references or a second runner bootstrap.

Inspect evaluated SDK markers before deleting project flags: `UsingMSTestSdk`
identifies SDK use and `IsTestingPlatformApplication` identifies a native test
application. MSTest.Sdk 4.5.1 does not itself set `IsTestProject`; an imported SDK
may gate analyzers or other behavior on an explicit value. Check those imports
before removing it. A helper library using MSTest.Sdk sets `IsTestApplication=false`
to avoid becoming a test executable.

Trace membership through the artifact CI actually uses: `.sln`, `.slnx`,
`.slnf`, an explicit project list or a repository wrapper. A `.slnf` lists
project paths relative to its underlying solution, so adding only to that
solution can still leave CI unaware of the tests. Preserve the existing format,
path conventions and unrelated entries. Check the wrapper's selection and
working directory rather than replacing it with an easier direct command.

Verify the affected project directly and through that entrypoint when they
exercise different discovery paths. Require the intended test identities and
executed counts; a successful build or a direct-project pass alone does not
prove CI inclusion. Use the normal native MTP command syntax in
[mstest-run-tests](../../mstest-run-tests/SKILL.md), retaining established
repository commands. Do not add unrelated test cases to prove project wiring.
