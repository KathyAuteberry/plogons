# Mostly Harmless plugins

Dalamud custom repository metadata. Add this subscription URL in Dalamud settings:

https://raw.githubusercontent.com/KathyAuteberry/plogons/master/mostly-harmless.json

The bootstrap array is empty until the first verified release is published. ZIPs live in
GitHub Releases of their source repositories, never here. FluffySim releases update their
entry automatically after tests and publication; other plugins coexist by unique InternalName.
Kotodama releases do the same. Every updater call names its plugin with `--plugin`.

Version, API level and download links come only from a published release ZIP. Author,
description, punchline, tags, URLs and the changelog come from the plugin's source `master`
(`AnoMech/FluffySim.json` / `Kotodama/Kotodama.json` and the CHANGELOG), so editing those and
pushing master updates this manifest without a new release. The `Changelog` field is a short
plain-text summary of the CHANGELOG entry for the published version.

For manual updates/recovery, use the Jujutsu and updater commands in [AGENTS.md](AGENTS.md).
Run `python -m unittest discover -s tools/tests` before committing. Inspect diffs to ensure
other plugin entries survive. A failed publication must not downgrade a version or overwrite
concurrent work. FluffySim's RELEASING.md documents release triggers, credentials and reruns.
