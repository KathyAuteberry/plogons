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

`tools/update_manifest.py` has two modes; each entry's fields have one owner:
Both the mode and `--plugin <InternalName>` are required; there is no default plugin.
- `release --plugin <InternalName> --zip <downloaded-public-ZIP> --version X.Y.Z.0`. It verifies ZIP CRC/identity/API
  metadata and writes the binary-owned fields (Name, InternalName, AssemblyVersion,
  DalamudApiLevel, MinimumDalamudVersion, load flags) plus exact HTTPS release URLs under the
  plugin's own repository. CI downloads that asset first; manual operators must do the same,
  never supply an unverified local build. No downgrades; rerunning an equal version must match
  the binary-owned fields and keeps any metadata synced since.
- `metadata --plugin <InternalName> --source <checkout of the plugin's master>`. It copies the
  source-owned fields (`SOURCE_FIELDS`: Author, Punchline, Description, Tags, RepoUrl, IconUrl,
  AcceptsFeedback, ...) from the plugin's own metadata JSON and writes `Changelog`, a plain-text
  summary of the CHANGELOG.md entry for the version already published. It never changes the
  version or links, so metadata can change without a release. URLs must point into the plugin's
  own repository, and the published version must have a changelog entry.
The allow-list `PLUGINS` maps FluffySim (`AnoMech/FluffySim.json`,
`docs/releases/CHANGELOG.md`) and Kotodama (`Kotodama/Kotodama.json`, `CHANGELOG.md`) to their
repositories. Both modes atomically replace the local JSON; cross-process writers must be serialized.

Each source repository runs `metadata` after every release and from its own
`sync-plogons-metadata.yml` workflow when its metadata JSON or changelog changes on master. CI retries rejected pushes by fetching and
recomputing, preserving concurrent entries. Never force-push manifest recovery.

Cross-repository authentication is each source repository's `PLOGONS_TOKEN` Actions secret, a fine-grained
Contents read/write token limited to this repo. No credentials belong in source. Branch rules
must permit that bot update. This repo needs no build secrets or compiled artifacts.

Manual recovery: `jj git fetch --remote origin`, inspect new master and current work, then
`jj new master@origin` in a preserved/clean working copy. Download the exact public release ZIP,
run the updater (`release`, then `metadata` against a checkout of the source master), `python -m unittest discover -s tools/tests`, inspect `jj diff`,
`jj commit -m "chore(release): update FluffySim metadata"`, `jj bookmark set master -r @-`.
Review `jj git push --remote origin --bookmark master --dry-run`; actual push needs owner approval.
Inspect `jj op log` and `jj --at-operation <id> log` for recovery; don't blindly restore whole
operations. Failed releases are repaired with higher versions, never mutable asset replacement.
See README.md for routine maintenance. FluffySim source history never belongs in this repository.
