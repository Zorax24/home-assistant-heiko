**Deutsch** · [English](README.md)

# HEIKO W600 für Home Assistant

**Vibe-coded:** Dieses Projekt wurde mit KI-Coding-Assistenten entwickelt. Automatisierte Prüfungen ersetzen keine fachliche Prüfung und keinen Test mit deiner tatsächlichen Wärmepumpe. Siehe [Prüfungen und Grenzen](docs/verification.de.md).

Eine **Custom Integration**, kein Supervisor-Add-on beziehungsweise App. Sie empfängt W600-TCP-Daten direkt in Home Assistant, stellt Messwerte und den vollständigen Referenz-Parameterkatalog bereit und kann die Verbindung optional an MyHeatPump weiterleiten. Dafür sind kein eigener Serverdienst und keine Anmeldung mit einem Cloud-Konto nötig.

**Stand: 0.5.2, experimentell.** **Echte Kommunikation und einzelne Schreibvorgänge sind an einer HEIKO Thermal 9 mit W600 bestätigt:** aktuelle Messwerte, ein Moduswechsel mit frischer Rücklesebestätigung und eine anschließende Reaktion der Wärmepumpe wurden beobachtet. Das bestätigt die geprüften Funktionen einer Anlage, nicht jeden Parameter oder einen gesonderten Hardwaretest des Pakets 0.5.2. Der Katalog stammt aus einem HEIKO-ioBroker-Adapter; das ist keine vom Hersteller geprüfte Kompatibilitätsliste. Nicht jeder Regler und jede Firmware muss alle Parameter unterstützen. Siehe [Prüfungen und Grenzen](docs/verification.de.md).

## Installation

### Repository in HACS hinzufügen — für öffentliche Verfügbarkeit vorbereitet

Dieser Weg ist für ein öffentlich erreichbares Repository vorbereitet; er ist **noch nicht als Installationsweg getestet**. HACS muss bereits installiert sein. Private Repositories funktionieren mit HACS auch dann nicht, wenn du auf GitHub darauf zugreifen kannst ([offizielle FAQ](https://hacs.dev/docs/faq/private_repositories/)). Bis diese Voraussetzung und die übrigen HACS-Prüfungen erfüllt sind, die drei ZIP-Schritte unten verwenden.

[![Repository in HACS öffnen](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Zorax24&repository=home-assistant-heiko&category=integration)

Alternativ von Hand hinzufügen:

1. **HACS → ⋮ → Benutzerdefinierte Repositories** öffnen.
2. `https://github.com/Zorax24/home-assistant-heiko` einfügen, **Integration** wählen und **Hinzufügen** drücken.
3. **HEIKO W600** öffnen, herunterladen und Home Assistant neu starten.
4. **Einstellungen → Geräte & Dienste → Integration hinzufügen → HEIKO W600** öffnen.

Kein Supervisor-Add-on-Repository hinzufügen. Für den benutzerdefinierten Weg ist keine HACS-Standardlistenaufnahme nötig. Repository-Verfügbarkeit und eine tatsächliche HACS-Installation müssen trotzdem noch geprüft werden.

### Jetzt ohne HACS installieren — drei Schritte

Vorher Home Assistant sichern. Bei einem Update zusätzlich den bisherigen Integrationsordner aufbewahren.

1. [Installations-ZIP herunterladen](https://github.com/Zorax24/home-assistant-heiko/releases/download/v0.5.2/heiko_w600-ha-0.5.2.zip) und entpacken.
2. Den enthaltenen Ordner `custom_components/heiko_w600` nach `/config/custom_components/` auf deinem Home-Assistant-Rechner kopieren.
3. Home Assistant neu starten. Dann [HEIKO W600 hinzufügen](https://my.home-assistant.io/redirect/config_flow_start/?domain=heiko_w600) anklicken oder **Einstellungen → Geräte & Dienste → Integration hinzufügen** verwenden.

Danach liegt die Datei unter `/config/custom_components/heiko_w600/manifest.json`. Manche Editoren nennen `/config` stattdessen `/homeassistant`. Das Installations-ZIP verwenden, nicht das GitHub-Quellcode-ZIP. Die Prüfsumme steht unter [Releases](https://github.com/Zorax24/home-assistant-heiko/releases).

## Wärmepumpe verbinden

1. In der Einrichtung `0.0.0.0` und TCP-Port `8899` belassen, sofern der Port frei ist. Bewusst wählen, ob an MyHeatPump weitergeleitet werden soll.
2. Im W600 als Ziel seiner bestehenden TCP-Client-Verbindung die **aus seinem LAN/VPN erreichbare Adresse von Home Assistant** und Port `8899` beziehungsweise den gewählten Port eintragen. Das bisherige W600-Ziel vorher sichern.
3. Auf aktuelle Messwerte und Einstellungen warten und danach [das Dashboard erstellen](#eigenes-dashboard-erstellen).

Der W600 baut die Verbindung auf. `0.0.0.0` ist niemals seine Zieladresse; HA-Webport `8123` gehört zu einem anderen Dienst. **Den Listener nicht ins Internet freigeben.** Das konfigurierbare Hersteller-Referenzziel lautet `www.myheatpump.com:18899`. Bei abweichenden Modul-Einstellungen, Docker/VPN oder fehlenden Daten helfen die [Netzwerk- und W600-Details](docs/network.de.md).

Voraussetzungen: Home Assistant ab 2026.9.4 (geprüft mit 2026.9.4), ein W600 mit dem Referenz-TCP-Protokoll und eine funktionierende LAN-/VPN-Route. Für die ZIP-Installation ist zusätzlich Dateizugriff auf das HA-Konfigurationsverzeichnis nötig. Bedienelemente werden erst mit aktuellen, geprüften Einstellungen verfügbar.

## Funktionen und tägliche Bedienung

- Vorlauf-, Rücklauf-, Außen- und Warmwassertemperatur, Verdichter- und Pumpenzustände sowie weitere zugeordnete Messwerte. Unbekannte, ungültige oder veraltete Werte werden nicht erfunden.
- **128 benannte Katalogparameter**, davon **125 schreibbare Bedienelemente** und drei nur lesbare Versionswerte. Die Entitätszahl einer Installation kann wegen Registry-Einstellungen abweichen; sie ist keine Kompatibilitätszusage.
- Alltag: Ein/Aus, Betriebsmodus, Raum- und Warmwasser-Sollwerte und Heizkurvenverschiebung. **Alle Einstellungen** enthält zusätzlich Service- und Schutzparameter. Diese beeinflussen unter anderem Frostschutz, elektrische Lasten, Legionellenfunktion, Ventile, Pumpen und Estrichtrocknung. Vor Änderungen eine fachkundige Person hinzuziehen. Referenzgrenzen beweisen nicht, dass ein Wert für dein Gerät sicher ist.
- **Messwerte abfragen / Einstellungen abfragen** senden ausdrücklich Leseanfragen und setzen keine Parameter.
- Schreibvorgänge werden nacheinander ausgeführt und verlangen aktuelle Einstellungen. Erst ein neuer passender CMD02-Einstellungsrahmen bestätigt den angeforderten Wert. Ein Zeitablauf bedeutet **unbekanntes Geräteergebnis**; vor Wiederholung den aktuellen Wert prüfen.
- CRC- und Identitätsprüfung, Überwachung des Datenalters, begrenzte Rahmenverarbeitung, Wiederverbindungen und datensparsame herunterladbare Diagnose.

Betriebsmodi und Auswahltexte stammen aus dem Katalog. Tatsächliche Verfügbarkeit hängt vom Regler ab. Die Integration ist kein `climate`-Raumthermostat und berechnet weder COP noch Energieerträge.

Pumpen und Verdichter zeigen **Ein/Aus**. **Nicht verfügbar** bedeutet, dass kein aktueller gültiger Messwert vorliegt, nicht dass das Gerät aus ist. Funktions- und Freigabeschalter beschreiben die Erlaubnis zum Betrieb; sie belegen keinen laufenden Heizbetrieb und keine laufende Pumpe. Bestehende Dashboard-Texte sind statisch: Nach einem Update erneut exportieren, um die neuen Namen zu übernehmen. Eigene Namen bleiben erhalten.

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

**MyHeatPump-Weiterleitung** erscheint im Dashboard und bei den Konfigurationsentitäten der Integration. Der Schalter ist bereits ohne W600-Verbindung verfügbar. Seine Auswahl bleibt über Neustarts und Optionsänderungen erhalten.

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

## Installationswege, HACS und Lizenz

**Die manuelle ZIP-Installation ist der unterstützte Installationsweg.** Das Installationspaket eines Releases verwenden und den drei Schritten oben folgen. Das Repository enthält `hacs.json` und folgt den [HACS-Strukturanforderungen für Integrationen](https://www.hacs.dev/docs/publish/integration/). **Eine Installation über HACS wurde noch nicht geprüft.** Die Aufnahme in die HACS-Standardliste und Home Assistant Brands ist nicht abgeschlossen. Metadaten und ein erfolgreicher Hassfest-Test allein belegen keine HACS-Installationsunterstützung.

MIT-Lizenz; [LICENSE](LICENSE) und [Herkunftshinweise](THIRD_PARTY_NOTICES.md) nennen die ioBroker-Referenz. Das Projekt ist unabhängig vom Hersteller und behauptet keine Gerätezertifizierung. Für Entwicklung: [reproduzierbarer Build und Tests](docs/development.md).
