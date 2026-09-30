**Deutsch** · [English](README.md)

# HEIKO W600 für Home Assistant

Eine **Custom Integration**, kein Supervisor-Add-on beziehungsweise App. Sie empfängt W600-TCP-Daten direkt in Home Assistant, stellt Messwerte und den vollständigen Referenz-Parameterkatalog bereit und kann die Verbindung optional an MyHeatPump weiterleiten. Dafür sind kein eigener Serverdienst und keine Anmeldung mit einem Cloud-Konto nötig.

**Stand: 0.5.1, experimentell, private Weitergabe.** Das Repository bleibt privat. Downloads funktionieren nur mit einem berechtigten GitHub-Konto. Kommunikation und Schreibvorgänge dieser Version sind **noch nicht an einer echten Wärmepumpe bestätigt**. Der Katalog stammt aus einem HEIKO-ioBroker-Adapter; das ist keine vom Hersteller geprüfte Kompatibilitätsliste. Nicht jeder Regler und jede Firmware muss alle Parameter unterstützen. Siehe [Prüfungen und Grenzen](docs/verification.de.md).

## Schnellstart

1. Mit einem berechtigten GitHub-Konto anmelden. Unter [Releases](https://github.com/Zorax24/home-assistant-heiko/releases) `heiko_w600-ha-0.5.1.zip` und `SHA256SUMS` herunterladen. Das Installations-ZIP verwenden, nicht das automatisch erzeugte Quellcode-ZIP von GitHub.
2. Ein Home-Assistant-Backup erstellen. Einen vorhandenen Ordner `heiko_w600` und die bisherigen W600-Zieleinstellungen separat sichern.
3. Das Installations-ZIP entpacken. Den enthaltenen Ordner `custom_components/heiko_w600` in das Home-Assistant-Konfigurationsverzeichnis kopieren. Danach muss `/config/custom_components/heiko_w600/manifest.json` vorhanden sein. Manche Editoren nennen das Konfigurationsverzeichnis `/homeassistant`. Keinen zweiten verschachtelten Ordner `custom_components` erzeugen.
4. Home Assistant selbst neu starten. **Einstellungen → Geräte & Dienste → Integration hinzufügen → HEIKO W600** öffnen.
5. Lokale Listener-Adresse und freien TCP-Port einstellen. Standard ist `0.0.0.0:8899`, also alle lokalen Netzwerkschnittstellen. **Weiterleitung zur Herstellercloud** bewusst wählen; sie ist zur Kompatibilität zunächst aktiv. Hersteller-Referenzwerte sind `www.myheatpump.com:18899`. Das beweist nicht, dass dein Modul genau dieses Ziel verwendet.
6. Die bestehende TCP-Client-Verbindung des W600 auf die **aus seinem Netz erreichbare LAN-Adresse von Home Assistant** und den gewählten Listener-Port einstellen. Der W600 baut die Verbindung auf. `0.0.0.0` ist eine Bind-Adresse und niemals die Zieladresse für den W600. Vorher [Netzwerk und W600](docs/network.de.md) lesen.
7. Auf aktuelle Messwerte und Einstellungen warten. Ohne aktuelle, geprüfte Einstellungen bleiben Bedienelemente nicht verfügbar. Danach das Dashboard wie unten beschrieben erstellen.

Benötigt werden Dateizugriff auf das HA-Konfigurationsverzeichnis, Berechtigung für einen HA-Neustart, ein W600 mit dem Referenz-TCP-Protokoll sowie eine LAN-/VPN-Route vom W600 zum Listener. Ein funktionierender Browserzugriff auf HA-Port 8123 prüft nicht den W600-Port. **Listener und W600-Verwaltungsoberfläche nicht ins Internet freigeben.**

## Funktionen und tägliche Bedienung

- Vorlauf-, Rücklauf-, Außen- und Warmwassertemperatur, Verdichter- und Pumpenzustände sowie weitere zugeordnete Messwerte. Unbekannte, ungültige oder veraltete Werte werden nicht erfunden.
- **128 benannte Katalogparameter**, davon **125 schreibbare Bedienelemente** und drei nur lesbare Versionswerte. Die Entitätszahl einer Installation kann wegen Registry-Einstellungen abweichen; sie ist keine Kompatibilitätszusage.
- Alltag: Ein/Aus, Betriebsmodus, Raum- und Warmwasser-Sollwerte und Heizkurvenverschiebung. **Alle Einstellungen** enthält zusätzlich Service- und Schutzparameter. Diese beeinflussen unter anderem Frostschutz, elektrische Lasten, Legionellenfunktion, Ventile, Pumpen und Estrichtrocknung. Vor Änderungen eine fachkundige Person hinzuziehen. Referenzgrenzen beweisen nicht, dass ein Wert für dein Gerät sicher ist.
- **Messwerte abfragen / Einstellungen abfragen** senden ausdrücklich Leseanfragen und setzen keine Parameter.
- Schreibvorgänge werden nacheinander ausgeführt und verlangen aktuelle Einstellungen. Erst ein neuer passender CMD02-Einstellungsrahmen bestätigt den angeforderten Wert. Ein Zeitablauf bedeutet **unbekanntes Geräteergebnis**; vor Wiederholung den aktuellen Wert prüfen.
- CRC- und Identitätsprüfung, Überwachung des Datenalters, begrenzte Rahmenverarbeitung, Wiederverbindungen und datensparsame herunterladbare Diagnose.

Betriebsmodi und Auswahltexte stammen aus dem Katalog. Tatsächliche Verfügbarkeit hängt vom Regler ab. Die Integration ist kein `climate`-Raumthermostat und berechnet weder COP noch Energieerträge.

## Eigenes Dashboard erstellen

1. **Einstellungen → Werkzeuge → Aktionen** öffnen; ältere HA-Versionen nennen den Bereich Entwicklerwerkzeuge.
2. **Wärmepumpen-Dashboard erzeugen** beziehungsweise `heiko_w600.export_dashboard` auswählen.
3. `de` oder `en` wählen. Ohne Angabe wird die HA-Systemsprache verwendet; weitere Sprachen fallen auf Englisch zurück. Im YAML-Modus:

   ```yaml
   action: heiko_w600.export_dashboard
   data:
     language: de
   ```

4. Aktion ausführen. Das YAML **innerhalb des Antwortfeldes `yaml`** kopieren; dessen äußere Zeile und die zusätzliche Einrückung von zwei Leerzeichen weglassen.
5. Unter Einstellungen → Dashboards ein **neues leeres Dashboard** anlegen. Bearbeiten → Dashboard-Menü → Raw-Konfigurationseditor öffnen, YAML einfügen und speichern.

Der Export verwendet deine registrierten Entitäten einschließlich umbenannter IDs. Deaktivierte Entitäten werden ausgelassen und ausdrücklich angepasste Namen erhalten. Er **schreibt oder überschreibt selbst kein Dashboard**. Die drei Ansichten heißen Übersicht, Alle Einstellungen und Messwerte und Diagnose. Kurze Namen ersetzen wiederholte Gerätepräfixe. Für eine andere Export-Sprache erneut erzeugen; bestehende Dashboard-Texte sind statisch. Entitätsübersetzungen folgen den HA-Sprachmechanismen.

## Schalter für die Herstellercloud

**Weiterleitung an MyHeatPump** erscheint im Dashboard und bei den Konfigurationsentitäten der Integration. Der Schalter ist bereits ohne W600-Verbindung verfügbar. Seine Auswahl bleibt über Neustarts und Optionsänderungen erhalten.

- **Ein:** Der vollständige TCP-Datenstrom des W600 wird zum konfigurierten Herstellerziel weitergeleitet; Herstellerantworten und -befehle gehen zurück zum Gerät. Enthalten sein können Protokoll-Gerätekennungen, Messwerte, Betriebszustände und Einstellungen. Herstellerbefehle können die Wärmepumpe verändern. Die Integration fügt keine Konto-Zugangsdaten hinzu und filtert den Rohdatenstrom nicht nach einzelnen Feldern. Sie verschlüsselt den Referenz-TCP-Transport nicht.
- **Aus:** Keine Herstellerverbindung; eine vorhandene Verbindung wird geschlossen. Gültige lokale CMD01-/CMD02-Rahmen erhalten lokale CMD03-/CMD04-Bestätigungen. Lokale Messwerte, Leseanfragen und Schreiben mit aktueller Rücklesebestätigung bleiben implementiert. Die Live-Fernfunktionen von MyHeatPump erhalten diesen Datenstrom nicht mehr; beim Hersteller bereits gespeicherte Daten werden nicht gelöscht. Das tatsächliche Geräteverhalten dieses Modus ist für diese Version noch nicht bestätigt.

Das Umschalten setzt selbst keinen Wärmepumpenparameter und erhält die W600-Verbindung. Bestehende Installationen behalten ihre gespeicherte Auswahl. Fehlt der bisherige Schaltzustand, gilt wie in 0.4.0 **Ein**. Eine konfigurierte Auswahl wird nicht stillschweigend geändert.

## Update, Sicherung, Rückkehr und Entfernen

Vor Updates HA sichern, angepasste Dashboards exportieren und den alten Integrationsordner aufbewahren. [Änderungen](CHANGELOG.md) lesen, insbesondere die Automations-Zustandsänderungen in 0.5.1. Nur `/config/custom_components/heiko_w600` vollständig durch den neuen Ordner ersetzen und HA neu starten. Für normale Updates die Integration nicht löschen und erneut anlegen: Domain, Config-Entry-IDs und eindeutige Entitätskennungen bleiben erhalten.

Zur Rückkehr den alten Integrationsordner und bei Bedarf das Dashboard wiederherstellen und HA neu starten. Bei ebenfalls zurückzunehmenden Konfigurationsänderungen das HA-Backup wiederherstellen. Zum Entfernen zuerst ein funktionierendes W600-Ziel wiederherstellen, falls der W600 diesen Listener benötigt. Anschließend Integration unter Geräte & Dienste entfernen, ihren Komponentenordner löschen und HA neu starten. Verweise in Dashboards und Automationen bereinigen. Das Entfernen setzt keine Wärmepumpenparameter zurück und löscht keine Herstellerdaten.

## Fehlerbehebung und Support

| Symptom | Prüfen |
|---|---|
| Warte auf Wärmepumpe | W600-TCP-Ziel, erreichbare LAN-/VPN-Route, gleicher Listener-Port und Firewall-Regeln. |
| Listener startet nicht | Port bereits belegt, Bind-Adresse nicht am HA-Rechner vorhanden oder fehlende Berechtigung. Freien Port verwenden und im W600 entsprechend setzen. |
| Keine Messwerte / nicht verfügbar | Eine TCP-Verbindung genügt nicht: aktuelle, korrekt adressierte und gültige CMD01- und CMD02-Daten sind erforderlich. Datenalter und Zähler prüfen. |
| Herstellercloud nicht erreichbar | Ziel und ausgehende TCP-Verbindung prüfen. Die lokale W600-Sitzung bleibt offen; bei aktiver Weiterleitung ersetzt lokale Auto-Bestätigung jedoch nicht die Cloud. |
| Schreiben nicht bestätigt | Aktuelle Einstellungen prüfen; nicht fortlaufend wiederholen oder unveränderten Gerätewert annehmen. |
| Integration nach Kopieren nicht vorhanden | Exakten Ordnerpfad, Vollständigkeit und HA-Protokoll prüfen. HA neu starten und Browsercache aktualisieren. |

Für Support HA-Version, Integrationsversion und bekannte nicht identifizierende Modell-/Regler-/Firmwareangaben nennen. Im Integrationsmenü **Diagnosedaten herunterladen** verwenden. Diagnose lässt konfigurierte Adressen und Ports, Konto-/Gerätekennungen, Rohrahmen sowie tatsächliche Temperaturen und Parameterwerte weg. Enthalten sind Softwareversion, Datenalter, Feldzahlen und Verbindungs-/Cloud-Flags. Jeden Anhang vor Weitergabe prüfen. Keine Zugangsdaten, Rohmitschnitte, privaten Screenshots oder vollständigen Serien-/MAC-Nummern posten. Siehe [technische Prüfungen](docs/verification.de.md).

## Privater Zugriff, HACS und Lizenz

Der unterstützte Weg ist manuelle ZIP-Installation durch berechtigte Personen. **HACS unterstützt keine privaten Repositories**, siehe [offizielle FAQ](https://hacs.dev/docs/faq/private_repositories/). Struktur und Metadaten bereiten eine spätere öffentliche Prüfung vor. HACS-Aufnahme/-Installation und Aufnahme in Home Assistant Brands sind weder behauptet noch abgeschlossen. Öffentliche Freigabe und neue Zugriffsberechtigungen sind separate Entscheidungen.

MIT-Lizenz; [LICENSE](LICENSE) und [Herkunftshinweise](THIRD_PARTY_NOTICES.md) nennen die ioBroker-Referenz. Das Projekt ist unabhängig vom Hersteller und behauptet keine Gerätezertifizierung. Für Entwicklung: [reproduzierbarer Build und Tests](docs/development.md).
