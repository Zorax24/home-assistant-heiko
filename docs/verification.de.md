**Deutsch** · [English](verification.md)

# Prüfungen und Grenzen für Support

## Implementierung

Der Referenzkatalog enthält 128 eindeutige benannte Indizes, davon 125 schreibbare und drei nur lesbare Versionswerte. Alle bisherigen Definitionen, Grenzen, Typen, Ganzzahlvorgaben, Einheiten und numerischen Protokoll-Auswahlwerte bleiben erhalten. CMD01 dekodiert die Referenznutzlast mit 43 Feldern; nicht jedes Rohfeld hat eine sinnvolle öffentliche Entität. Entitätsanlage wird anhand der tatsächlichen Plattformdefinitionen geprüft und nicht aus früheren Installationsaussagen übernommen.

Ziel ist ausschließlich die Reglerfamilie mit W600-Referenzprotokoll. Für 0.5.1 gibt es **keine mit Hardware bestätigte Modell-/Firmwareliste**. Weitere Markennamen im Referenzadapter beweisen keine Kompatibilität. Erfolgreiches Laden, Entitätszahl, Dashboard und simulierte Bestätigungen sind kein physischer Geräte-Abnahmetest.

Lokale CMD01-/CMD02-Bestätigungen, Cloud-Umschaltung, Erhalt der W600-Verbindung, Wiederverbindung, Befehlsserialisierung, CMD05-Schreiben mit anschließendem CMD07 und neuer passender CMD02-Antwort, Datenalter, CRC-Fehler und falsche Geräteidentität werden mit synthetischen Rahmen und Loopback-Servern geprüft. Parametertests betätigen keine Hardware. Ein Zeitablauf nach dem Senden beweist nicht, dass das Gerät den Wert abgelehnt hat.

Deutsch-/Englisch-Schlüsselgleichheit, vollständige Katalog-Auswahlübersetzungen, angepasste Entitäts-IDs, Ausschluss deaktivierter/fremder Einträge, Paketstruktur/-inhalt, reproduzierbarer Archivbau und Datenschutzprüfungen werden automatisiert geprüft. CI verwendet einen frischen Checkout und getrennt einen Smoke-Test mit echtem HA Core 2026.9.4, nur lokalem Loopback und abgeschalteter Weiterleitung. Unit-Tests verwenden kleine HA-Attrappen. Beide Ebenen ersetzen keine physische Inbetriebnahme. CI-Ergebnisse stehen im Actions-Bereich; [Release-Nachweise](release-evidence.json) nennen abgeschlossene Prüfungen dieser Version.

## Sicherheit und Vertraulichkeit

Exportierte Dashboards kennzeichnen Service-/Schutzgruppen und enthalten eine Warnung. Kataloggrenzen werden vor Schreibbefehlen geprüft. Der Katalog ist eine rekonstruierte Referenz und beweist nicht sämtliche Firmware-Verriegelungen, Einheiten, Abhängigkeiten oder sicheren Inbetriebnahmewerte. Keine neue Service-Sperre wird stillschweigend aktiviert; Tests schreiben nicht an echte Geräte.

Die herunterladbare HA-Diagnose enthält nur freigegebene Metadaten: Softwareversion, Verbindungs-/Frische-/Cloud-Flags, Datenalter, Feldzahlen und unterstützte Konfigurationsbereiche. Konfigurierte Adressen/Ports, Zeitstempel, tatsächliche Parameter-/Messwerte, Rohrahmen, Gerätekennungen und Geheimnisse fehlen. HA-Zustandsattribute können dennoch Betriebsinformationen enthalten. Screenshots, Protokolle und Supportanhänge immer zusätzlich selbst prüfen.

Das bereinigte Repository wurde aus einer Dateiauswahlliste mit neuer Git-Historie erstellt. Persönliche Deployment-Notizen, Netzwerkpläne, Protokolle, Screenshots, Sicherungen und alte Archive sind nicht enthalten. Lokales Gitleaks wird durch eigene Prüfungen auf private Angaben, Pfade und Adressen sowie manuelle Quellcode-/Dokument-/Archivprüfung ergänzt. Kein Scanner beweist das Fehlen aller denkbaren privaten Zeichenfolgen. Auffälligkeiten vertraulich an den Maintainer melden; sensible Angaben nicht in öffentliche Issues aufnehmen.

## HACS-Grenze und offizielle Quellen

Einzelintegrationsstruktur und Metadaten folgen [HA-Manifest](https://developers.home-assistant.io/docs/creating_integration_manifest/) und [HACS-Anforderungen](https://www.hacs.dev/docs/publish/integration/). Übersetzungen folgen [HA-Custom-Integration-Übersetzungen](https://developers.home-assistant.io/docs/internationalization/custom_integration/) und [Backend-Übersetzungen](https://developers.home-assistant.io/docs/internationalization/core/).

Eine HACS-Installation wurde noch nicht geprüft. Standardlistenaufnahme und Home Assistant Brands sind nicht abgeschlossen. Vor einer HACS-Installationszusage die aktuellen offiziellen Anforderungen prüfen und einen Installationstest durchführen. Unterstützt wird die manuelle Installation des Release-ZIPs.
