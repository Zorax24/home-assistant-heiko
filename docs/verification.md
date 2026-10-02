[Deutsch](verification.de.md) · **English**

# Verification and support boundaries

## Implementation

The reference catalog contains 128 unique named indices, including 125 writable and three read-only version entries. All baseline definitions, ranges, types, integer flags, units and protocol enum numeric values are retained. CMD01 decoding covers the reference 43-field payload; not every raw field has a useful public entity. Entity creation is checked from the actual platform definitions, not a past deployment claim.

Only the W600 reference framing/controller family is targeted. There is **no hardware-verified model/firmware matrix** for 0.5.2. Names of other heat-pump brands in an upstream adapter do not establish compatibility. A loaded integration, entity count, successful dashboard or simulated ACK is not a physical-device acceptance test.

Local-mode CMD01/CMD02 acknowledgements, cloud toggling, socket preservation, reconnect, command serialization, CMD05 writes followed by CMD07 and a new matching CMD02, stale values, CRC failures and identity mismatch are covered using synthetic frames and loopback servers. Parameter tests do not actuate hardware. A timeout after sending a write does not mean the device rejected it.

English/German translation key parity, catalog choice coverage, custom entity IDs, disabled/other-entry exclusion, package structure/content, deterministic archive build and source privacy gates are tested. CI includes a fresh checkout and a separate real Home Assistant Core 2026.9.4 smoke check, with local loopback only and forwarding disabled. Unit tests use small HA stubs; neither layer substitutes for physical commissioning. CI and release results are visible under the repository Actions tab. See [release evidence](release-evidence.json) for completed gates of this release.

## Safety and confidentiality

Service/protection groups are labeled and warned in exported dashboards. Catalog limits are enforced before sending writes. The catalog is a reverse-engineered reference: it does not establish all firmware interlocks, units, dependencies or safe commissioning values. No new service-level lockout is silently enabled, and no tests write to a real device.

Downloads of HA diagnostics expose only allowlisted metadata: software version, connection/freshness/cloud flags, ages and field counts, and supported configuration ranges. They omit configured addresses/ports, timestamps, actual parameter/measurement values, raw frames, identities and secrets. State attributes in HA can still contain operational information; review screenshots, logs and all support attachments manually.

The sanitized repository was built with a file allowlist and a new Git history. Personal deployment notes, network diagrams, logs, screenshots, backups and old archives are not included. Local Gitleaks scanning is complemented by a custom private-data/path/address scan and manual source/document/archive review. A scanner is not a proof that no possible sensitive string exists; report any issue confidentially to the maintainer; do not include sensitive details in public issues.

## HACS boundary and official sources

Single-integration structure and manifest metadata follow [HA manifest](https://developers.home-assistant.io/docs/creating_integration_manifest/) and [HACS integration requirements](https://www.hacs.dev/docs/publish/integration/). Localization follows [HA custom integration localization](https://developers.home-assistant.io/docs/internationalization/custom_integration/) and [backend localization](https://developers.home-assistant.io/docs/internationalization/core/).

HACS installation has not been validated. Default-list inclusion and Home Assistant Brands submission are not completed. Review the current official requirements and complete an installation test before documenting HACS as supported. Manual release-ZIP installation is the supported path.
