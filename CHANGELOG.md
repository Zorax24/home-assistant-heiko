# Changelog

## 0.6.0

- Add Polish (`pl`) translations for setup/options, all entities and catalog choices, status/error messages, actions and complete dashboard export including service/protection warnings.
- Support `pl` in the export action and Home Assistant system-language selection; preserve custom names, entity IDs, raw states, catalog and cloud choice.
- Load dashboard translation files in the executor during setup, fixing the blocking disk-read startup warning.
- Extend catalog/translation parity and real Home Assistant smoke checks to all three languages. No production or device writes are part of these automated tests.

Deutsch: Vollständige polnische Bedienoberfläche und Dashboard-Export ergänzt; Startwarnung beim Laden der Dashboard-Texte behoben.
Polski: Dodano polskie tłumaczenia interfejsu i eksportu panelu; usunięto blokujący odczyt plików tłumaczeń podczas uruchamiania.

## 0.5.2

- Review all English/German entity names, options, connection/write-result states, setup fields and dashboard labels. Pump/compressor binary status displays On/Off (Ein/Aus) through integration-specific state translations instead of the RUNNING device-class wording.
- Keep device classes, raw states, unique IDs, configuration, protocol/catalog definitions and availability unchanged. Missing or stale telemetry remains unavailable, never Off. Standby, utility lockout and emergency operation retain their distinct meaning.
- Name enable switches as functions or permissions, not proof of actual operation. Clarify local reception versus the manufacturer connection, and label write readback as Confirmed rather than an unexplained CMD02 state.
- Keep dashboard catalog labels consistent with entity translations. Existing exported dashboards contain static names: regenerate and manually replace their YAML if you want the revised labels. Explicit user names remain unchanged.
- Add translation/catalog consistency tests and actual HA smoke checks for all six binary sensors: on, off, unavailable, and both languages. No physical-device writes or production changes.

Deutsch: Pumpen und Verdichter zeigen Ein/Aus. Fehlende Daten bleiben Nicht verfügbar. Schalter für Funktionen und Freigaben, Verbindungstexte, Schreibbestätigung und Dashboard-Bezeichnungen sind überarbeitet. Kennungen, Zustandswerte, Geräteklassen und Protokoll bleiben gleich. Bestehende Dashboard-Texte bei Bedarf neu exportieren; eigene Namen bleiben erhalten.

### Documentation preparation since 0.5.1

- Separate installation and connection setup. Add a prepared HACS custom-repository shortcut and four-step instructions, explicitly conditional on public availability and installation validation; shorten the working ZIP method to three steps in both languages.

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
