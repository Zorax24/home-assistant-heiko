# Development and reproducible release

Use Python 3.14 (the HA smoke gate pins Core 2026.9.4). No infrastructure credentials or real device are needed. The unit suite uses standard-library unittest and explicit HA stubs. The real-HA smoke gate runs separately to prevent stubs masking HA API errors.

```sh
python -m venv .venv
# Activate the venv using your operating system's instructions.
python -m unittest discover -s tests -v
python tools/check_project.py
python build_package.py
python tools/check_project.py --archive dist/heiko_w600-ha-0.6.0.zip
```

For the isolated real-HA gate on Linux:

```sh
python -m pip install -r requirements-ha-test.txt
python tools/ha_smoke.py
```

The smoke script creates a temporary HA configuration directory and loopback listener, disables cloud forwarding explicitly, checks entity translation coverage and listener failure, then tears down its own runtime. It must not be run against a productive HA directory. No W600 or manufacturer host is contacted.

The ZIP builder uses sorted files, a fixed timestamp, fixed file modes and deflate level 9. Exact bytes are reproducible with the same Python/zlib runtime. The package includes only the integration directory, licenses and its runtime resources. `SHA256SUMS` is generated alongside it. GitHub source archives have a different shape and are not installation ZIPs.

Before committing, review `git ls-files`, all binary metadata and every archive member. Run official Gitleaks locally (`gitleaks dir . --redact --no-banner`, then `gitleaks git . --redact --no-banner`) in addition to the custom privacy validator. Never upload scanner findings or personal data to third-party analysis services. Synthetic test placeholders and protocol constants are not real secrets.

The initial sanitized export is separate from the original personal project; no original Git history is imported. New commits use the verified GitHub account's noreply identity. The release tag must be new and must identify the tested commit; never overwrite a tag/release. CI runs unit/package/privacy gates and real-HA smoke from a fresh checkout, with read-only repository permissions. No automatic production installation is configured.

## Reference preservation

Catalog and protocol code provenance is in THIRD_PARTY_NOTICES.md. Preserve the catalog indices, bounds and numeric options when translating labels. Entity unique IDs are keyed by entry ID and catalog/protocol index, never translated. Internal select states are `option_<code>`; legacy German service-call labels remain accepted aliases. State-based user automations require the change documented in CHANGELOG.md.

The included `hacs.json` and manifest are preparation metadata. HACS installation has not been validated; default-list inclusion and Home Assistant Brands submission are not completed. Keep the manual release-ZIP instructions until these gates have been verified.
