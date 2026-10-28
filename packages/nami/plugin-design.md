# Packaging decision

Checked on 2026-10-27 against Codex CLI 0.164.0 and current official documentation.

- Repository skills and marketplace discovery use `.agents`.
- A portable plugin uses root `plugin.json` and `skills/`; `.codex-plugin` is an optional legacy overlay.
- An isolated temporary Codex profile recognized that layout with `installed: false`.
- Claude Code still documents `.claude/skills`; the Agent Skills standard announcement is not proof that every client changed discovery paths.
- This repository uses the portable plugin format, with no `.claude` or `.codex` compatibility trees. That packaging verification did not install a plugin or marketplace in the user's profile; installation is a separate explicit action.

Sources: [OpenAI packaging](https://developers.openai.com/plugins/build/plugins),
[OpenAI skills](https://learn.chatgpt.com/docs/build-skills),
[Claude Code skills](https://code.claude.com/docs/en/skills).

The package is distributed through `ancplua-dotnet`. Its former standalone `nami` marketplace has been retired; package validation does not require a local catalog.
