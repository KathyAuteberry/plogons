# plogons agent instructions

This independent colocated Jujutsu/Git repository stores Dalamud custom-plugin metadata,
not build ZIPs. Source: KathyAuteberry/plogons, origin uses the owner's SSH host alias.
Use Conventional Commit messages for every new commit. Use jj locally; inspect `jj status`, `jj log`, `jj bookmark list --all-remotes`,
`jj git remote list`, `jj op log` before edits. Preserve working changes and history.
`master` is the publication bookmark. No push or live update without explicit owner authorization.

Authoritative file: `mostly-harmless.json`.
Exact subscription: https://raw.githubusercontent.com/KathyAuteberry/plogons/master/mostly-harmless.json
It is a JSON array of plugin objects keyed by unique InternalName; `[]` is the initial
bootstrap until a verified release exists. Do not invent a 2.0.0.0 entry before publication.
Each released entry needs Name, Author, Description, InternalName, AssemblyVersion,
DalamudApiLevel and DownloadLinkInstall/Update/Testing. Preserve all other plugin entries.

FluffySim's tag workflow in the separate FluffySim repository tests, builds and publishes
its ZIP, then checks out this repository's master and runs:
`python tools/update_manifest.py --zip <downloaded-public-ZIP> --version X.Y.Z.0`.
The updater verifies ZIP CRC/identity/API metadata and constructs exact HTTPS GitHub release
URLs under KathyAuteberry/FluffySim, matching tag and asset versions. CI downloads that
asset before updating; manual operators must do the same, not supply an unverified local build.
No downgrades; equal versions must have identical metadata. It atomically replaces the local
JSON; cross-process writers must be serialized. CI retries rejected pushes by fetching and
recomputing, preserving concurrent entries. Never force-push manifest recovery.

Cross-repository authentication is FluffySim's `PLOGONS_TOKEN` Actions secret, a fine-grained
Contents read/write token limited to this repo. No credentials belong in source. Branch rules
must permit that bot update. This repo needs no build secrets or compiled artifacts.

Manual recovery: `jj git fetch --remote origin`, inspect new master and current work, then
`jj new master@origin` in a preserved/clean working copy. Download the exact public release ZIP,
run the updater, `python -m unittest discover -s tools/tests`, inspect `jj diff`,
`jj commit -m "chore(release): update FluffySim metadata"`, `jj bookmark set master -r @-`.
Review `jj git push --remote origin --bookmark master --dry-run`; actual push needs owner approval.
Inspect `jj op log` and `jj --at-operation <id> log` for recovery; don't blindly restore whole
operations. Failed releases are repaired with higher versions, never mutable asset replacement.
See README.md for routine maintenance. FluffySim source history never belongs in this repository.
