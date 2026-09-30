# Changelog

## Unreleased

- Make English/German documentation and installation instructions suitable for a general audience. Remove distribution-specific access wording while retaining experimental status, hardware limitations and the unverified HACS boundary. No runtime or installation-package changes.

- Deutsch/Englisch für allgemeine Nutzung formuliert; experimenteller Stand, Hardware-Grenzen und ungeprüfte HACS-Installation bleiben ausdrücklich genannt. Laufzeitcode und Installationspaket unverändert.

## 0.5.1

- Fix legacy German select-option service aliases at the HA service-handler boundary, before core option validation. Both legacy labels and stable `option_<code>` calls now reach the same protocol value.
- Add a regression through the real HA `select.select_option` service with a synthetic write recorder, without physical-device transport.
- Existing 0.5.0 release/tag are preserved. Prefer 0.5.1 for installation.

Alte deutsche Auswahltexte werden jetzt vor der HA-Auswahlprüfung normalisiert. Der echte HA-Service ist mit einem synthetischen Schreibrekorder geprüft. 0.5.0 bleibt erhalten; für Installation 0.5.1 verwenden.

## 0.5.0

- Prepare a standalone distribution from the complete 0.4.0 custom integration; retain the full catalog, protocols, CRC checks, readback confirmation, requests and independent optional manufacturer relay.
- Add complete English/German HA translations for catalog controls, choices, connection states, write-result states, buttons, setup/options, exceptions and export action.
- Generate English/German dashboards from the local registry; retain stable IDs and custom names. Highlight service/protection groups and include a warning. Never save a dashboard automatically.
- Add deliberate manufacturer-forwarding choice to setup/options. Preserve old saved choice and enabled default for legacy installations.
- Add reproducible install ZIPs, local privacy checks, unit/loopback tests and isolated HA smoke validation in CI.
- Remove personal installation artifacts from the separate repository export. Add bilingual manuals and MIT provenance notices.

### Upgrade notes / Hinweise zum Update

Domain `heiko_w600`, config-entry version 1, listener/upstream option keys, device identifier tuples and all entity unique IDs remain unchanged. No config-entry/identity migration is required. Protocol values and catalog ranges are unchanged.

Select entities now expose language-independent `option_<numeric code>` states/options (for example `option_1` is Heating/Heizen for operating mode). HA translates their display labels. Existing German labels are still accepted as aliases by `select.select_option`, but **state-based automations must use the new stable states**. Existing entity IDs stay registered. Connection/write-result sensors similarly use stable states (`waiting`, `fresh`, `confirmed`, etc.); use those in automations. Write index/value are separate attributes.

Die bestehenden Domain-, Config-Entry-, Geräte- und eindeutigen Entitätskennungen bleiben erhalten; keine Identitätsmigration nötig. Protokollwerte und Kataloggrenzen bleiben unverändert. Auswahlelemente verwenden jetzt sprachunabhängige Zustände `option_<Zahl>`, etwa `option_1` für Heizen im Arbeitsmodus. HA übersetzt die Anzeige. Alte deutsche Auswahltexte werden bei `select.select_option` weiterhin als Alias angenommen. **Zustandsabhängige Automationen auf die neuen Kennungen umstellen.** Verbindungs-/Schreibstatus verwendet ebenfalls feste Zustände wie `waiting`, `fresh` und `confirmed`. Parameterindex und angeforderter Wert stehen getrennt in Attributen.

## Baseline 0.4.0

Incoming W600 TCP bridge, complete catalog controls, dashboard export with short labels and persistent cloud forwarding toggle. Earlier personal deployment records are intentionally excluded from this repository.

Parameter metadata attributes now use English developer keys (`section`, `confirmation`, `source`); connection flag keys remain unchanged and have translated display labels. / Parameter-Metadaten verwenden jetzt englische Entwicklerschlüssel; Verbindungs-Flags bleiben erhalten und erhalten übersetzte Anzeigenamen.
