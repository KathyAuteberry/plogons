# Mostly Harmless plugins

Dalamud custom repository metadata. Add this subscription URL in Dalamud settings:

https://raw.githubusercontent.com/KathyAuteberry/plogons/master/mostly-harmless.json

The bootstrap array is empty until the first verified release is published. ZIPs live in
GitHub Releases of their source repositories, never here. FluffySim releases update their
entry automatically after tests and publication; other plugins coexist by unique InternalName.

For manual updates/recovery, use the Jujutsu and updater commands in [AGENTS.md](AGENTS.md).
Run `python -m unittest discover -s tools/tests` before committing. Inspect diffs to ensure
other plugin entries survive. A failed publication must not downgrade a version or overwrite
concurrent work. FluffySim's RELEASING.md documents release triggers, credentials and reruns.
