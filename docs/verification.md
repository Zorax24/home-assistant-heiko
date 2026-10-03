[Deutsch](verification.de.md) · **English**

# Verification and support boundaries

## Implementation

The reference catalog contains 128 unique named indices, including 125 writable and three read-only version entries. All baseline definitions, ranges, types, integer flags, units and protocol enum numeric values are retained. CMD01 decoding covers the reference 43-field payload; not every raw field has a useful public entity. Entity creation is checked from the actual platform definitions, not a past deployment claim.

Only the W600 reference framing/controller family is targeted. A physical test is documented for **one HEIKO Thermal 9 with W600**; there is no comprehensive model/firmware compatibility matrix. Names of other heat-pump brands in an upstream adapter do not establish compatibility. A loaded integration, entity count, successful dashboard or simulated ACK is not a physical-device acceptance test.

Local-mode CMD01/CMD02 acknowledgements, cloud toggling, socket preservation, reconnect, command serialization, CMD05 writes followed by CMD07 and a new matching CMD02, stale values, CRC failures and identity mismatch are covered using synthetic frames and loopback servers. Parameter tests do not actuate hardware. A timeout after sending a write does not mean the device rejected it.

English/German/Polish translation key parity, catalog choice coverage, custom entity IDs, disabled/other-entry exclusion, package structure/content, deterministic archive build and source privacy gates are tested. CI includes a fresh checkout and a separate real Home Assistant Core 2026.9.4 smoke check, with local loopback only and forwarding disabled. Unit tests use small HA stubs; neither layer substitutes for physical commissioning. CI and release results are visible under the repository Actions tab. See [release evidence](release-evidence.json) for completed gates of this release.

## Physical test evidence

A documented physical test on 2 October 2026 used the deployed integration on a HEIKO Thermal 9 with W600. Home Assistant received current measurements and settings. Changing the operating mode from Heating to Auto produced the native write confirmation and fresh CMD02 readback. A display-backlight setting was also restored and readback-confirmed; the final parameter comparison retained only the intended mode change. During a real water draw, recorded telemetry showed changes in the demand-temperature input, circulation pump, flow switch, active DHW function, compressor and supply temperature. This is evidence of real communication, selected successful writes and an observed controller response, beyond a socket connection or simulation.

The test export did not record the installed integration package version. It therefore does not establish a separate physical acceptance test of the published 0.6.0 archive. Complete catalog write coverage, other controllers/firmware, physical valve position, sustained hot-water delivery, immediate auxiliary-heater operation and cloud-disabled operation remain unconfirmed. An application's hydraulic commissioning is separate from integration communication. Private test exports and infrastructure details are excluded from this repository.

## Safety and confidentiality

Service/protection groups are labeled and warned in exported dashboards. Catalog limits are enforced before sending writes. The catalog is a reverse-engineered reference: it does not establish all firmware interlocks, units, dependencies or safe commissioning values. No new service-level lockout is silently enabled, and automated repository tests do not write to a real device.

Downloads of HA diagnostics expose only allowlisted metadata: software version, connection/freshness/cloud flags, ages and field counts, and supported configuration ranges. They omit configured addresses/ports, timestamps, actual parameter/measurement values, raw frames, identities and secrets. State attributes in HA can still contain operational information; review screenshots, logs and all support attachments manually.

The sanitized repository was built with a file allowlist and a new Git history. Personal deployment notes, network diagrams, logs, screenshots, backups and old archives are not included. Local Gitleaks scanning is complemented by a custom private-data/path/address scan and manual source/document/archive review. A scanner is not a proof that no possible sensitive string exists; report any issue confidentially to the maintainer; do not include sensitive details in public issues.

## HACS boundary and official sources

Single-integration structure and manifest metadata follow [HA manifest](https://developers.home-assistant.io/docs/creating_integration_manifest/) and [HACS integration requirements](https://www.hacs.dev/docs/publish/integration/). Localization follows [HA custom integration localization](https://developers.home-assistant.io/docs/internationalization/custom_integration/) and [backend localization](https://developers.home-assistant.io/docs/internationalization/core/).

HACS installation has not been validated. Default-list inclusion and Home Assistant Brands submission are not completed. Review the current official requirements and complete an installation test before documenting HACS as supported. Manual release-ZIP installation is the supported path.
