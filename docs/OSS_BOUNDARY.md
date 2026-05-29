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

Before any public release, scan:

```bash
rg -n "/home/argo|/mnt/homes|Vaults|conversation-archive|argobox/sessions|\\.codex|\\.hermes|abx-ssh|credential-broker|sk-[A-Za-z0-9]|BEGIN OPENSSH PRIVATE KEY|BEGIN RSA PRIVATE KEY" .
```

