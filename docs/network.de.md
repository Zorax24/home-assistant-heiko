**Deutsch** · [English](network.md)

# W600-Verbindung und Netzwerk

## Aus Quellcode belegt, kein Geräte-Einrichtungsassistent

Der Referenzadapter betreibt einen TCP-Server. Der W600 verbindet sich als TCP-**Client** damit. Diese Integration übernimmt dieselbe Richtung:

```text
Wärmepumpenregler ↔ W600 → lokaler HA-Listener → optionales Hersteller-TCP-Ziel
                         ← Antworten/Befehle ←
```

HA baut die getrennte ausgehende Herstellerverbindung nur bei eingeschalteter Weiterleitung und vorhandener W600-Sitzung auf. Leseanfragen und Parameterbefehle laufen über die bestehende W600-Verbindung zurück. Referenzwerte sind Listener-Port **8899** und Herstellerziel **www.myheatpump.com:18899**. Das sind konfigurierbare Standardwerte, keine allgemeingültigen Gerätevorgaben. Eine vom Hersteller eingehend aufgebaute Verbindung und ein Cloud-Login sind nicht erforderlich.

## Eigenes erreichbares Ziel einstellen

Vor einer Änderung die bisherige W600-Betriebsart, Zieladresse, Zielport und zutreffende Herstellerhinweise sichern. Bei einem Modul mit dem Referenzprotokoll die erforderliche TCP-Client-Betriebsart beibehalten und als TCP-Gegenziel die erreichbare HA-Rechneradresse und deinen Listener-Port setzen. Menünamen, Firmware-Oberfläche, Verwaltungsadresse, Zugangsdaten, UART-Einstellungen und notwendige Geräte-Neustarts sind durch dieses Projekt **nicht belegt**. Die dokumentierten Bedienelemente deines Moduls verwenden; keine vermuteten Einstellungen anderer W600-Produkte kopieren. Die Integration konfiguriert das Modul nicht selbst.

Im gemeinsamen LAN die tatsächliche LAN-Adresse des HA-Rechners verwenden. Bei Docker den gewählten TCP-Port veröffentlichen oder ein geeignetes Host-Netzwerk nutzen; der HA-Webport veröffentlicht ihn nicht automatisch. Bei HAOS läuft der Listener im Core-Netzwerk; lokale Firewall und Routing prüfen. Bei geroutetem VPN müssen Hin- und Rückweg zwischen W600 und HA funktionieren. Bei einem getrennten TCP-Weiterleiter ist dessen erreichbare Adresse samt Port das W600-Ziel; der Weiterleiter muss an HA vermitteln. Es wird kein bestimmter VPN-/Weiterleitungsdienst und kein privater Netzwerkplan mitgeliefert.

Tests verwenden Loopback, Dokumentationsbereiche oder `.example`-Domains. Eigene Werte einsetzen; Dokumentationsadressen nicht am Gerät einstellen. `0.0.0.0` und `::` sind Bind-Adressen, keine Ziele. Ein Bind-Hostname muss eine lokale Schnittstelle bezeichnen und nicht den W600.

## Grenzen und Erreichbarkeit

Pro HA-Instanz werden ein Konfigurationseintrag und eine aktive W600-Sitzung unterstützt. Eine neue Sitzung ersetzt die alte. Der Listener besitzt kein TLS, Login oder Netzwerk-Quellfilter. Nur im vertrauenswürdigen Geräte-LAN/VPN betreiben und Clients per Firewall begrenzen. Niemals aus dem öffentlichen Internet weiterleiten. Herstellerverkehr wird ungefiltert vermittelt; Gerätekennungen und Herstellerbefehle können passieren. Die Integration ist kein verschlüsselter Tunnel.

Die Herstellerverbindung wird unabhängig vom W600 wiederhergestellt: Verbindungsversuch mit zehn Sekunden Zeitlimit und fünf Sekunden Wiederholungspause. Daten werden nicht für spätere Cloud-Zustellung gespeichert. Bei aktiver, aber ausgefallener Herstellerverbindung läuft lokale Dekodierung weiter; lokale Auto-Bestätigung wird nur bei bewusst deaktivierter Weiterleitung verwendet. Das Verhalten eines konkreten Geräts ohne Herstellerantwort ist hier nicht mit Hardware bestätigt.

Vor Deinstallation den zuvor gesicherten W600-Datenweg wiederherstellen. Netzwerkänderungen und physische Inbetriebnahme liegen bei der installierenden Person. Die Release-Prüfung kontaktiert keine echte Wärmepumpe und kein Herstellerziel.
