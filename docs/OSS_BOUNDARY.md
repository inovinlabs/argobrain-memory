# OSS Boundary

This repo must remain synthetic-fixture only.

Do not add:

- private transcripts;
- real session summaries;
- generated memory from private sessions;
- private hostnames, internal IPs, or operator paths;
- credentials or credential variable values;
- live agent hook installers;
- default cloud providers that send user content without opt-in.

Before any public release, run the shared Release Forge scan from the private release tooling repo. Keep the literal private-pattern blocklist in private release tooling, not in this public-facing repository.

```bash
release-forge scan <staged-export> --manifest <release-forge.toml>
```
