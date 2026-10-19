# ANcpLua .NET privacy policy

Effective date: 19 October 2026

ANcpLua .NET is maintained by Alexander Nachtmann (ANcpLua). This policy covers
the plugin's skills, supporting scripts and repository support.

## Plugin operation

The plugin provides agent instructions and local development helpers. It has no
publisher-operated backend, account system, advertising trackers or built-in
usage analytics. Installing it does not give the maintainer access to your
repositories, prompts or diagnostic artifacts.

Your AI host may process source code, prompts, file paths, package metadata,
build logs and diagnostics supplied by you or accessible to the host. The host's
policies, permissions and account settings govern that processing, including
storage, retention and training choices. For ChatGPT and Codex, see
[OpenAI's privacy policy](https://openai.com/policies/privacy-policy/).

Requested workflows can run local commands, read project/package files, restore
dependencies and write reports or temporary build artifacts. Release helpers
can use a local candidate-package cache, compare package bytes and query NuGet
indexing. Commands may contact configured feeds, GitHub or other services needed
for the requested task. Those services receive the information required by the
request, such as package identifiers and versions, under their own policies.
The plugin does not automatically send workspace contents to its maintainer.

## Support, retention and controls

You choose what to post in public GitHub issues or pull requests. Your identity,
messages and attachments may be visible publicly and are used to investigate
and maintain the plugin. They are not sold or used for advertising. Avoid
posting credentials or confidential project data. See
[GitHub's privacy statement](https://docs.github.com/en/site-policy/privacy-policies/github-general-privacy-statement).

The maintainer keeps no separate store of your prompts or workspace. Local
artifacts remain under your control; hosts and external services set retention
for their copies. Public contributions and third-party caches may persist.

You can uninstall the plugin, restrict host permissions and remove local
artifacts. Direct questions or requests about repository support information to
the [issue tracker](https://github.com/ANcpLua/ancplua-dotnet/issues). For records
held by another provider, contact that provider. Updates to this policy are
published here with a revised effective date.
