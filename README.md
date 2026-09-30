[Deutsch](README.de.md) · **English**

# HEIKO W600 for Home Assistant

A **custom integration**, not a Supervisor app/add-on. It receives W600 TCP data in Home Assistant, exposes measurements and the complete reference settings catalog, and can optionally relay the connection to MyHeatPump. No separate server process or cloud account login is required.

**Status: 0.5.1, experimental.** Hardware communication and writes with this release have **not** been confirmed on a physical heat pump. The catalog originates from a HEIKO ioBroker adapter; this is not a manufacturer-certified compatibility list. Do not assume another controller or firmware supports every parameter. See [verification and limitations](docs/verification.md).

## Quick start

1. Open [Releases](https://github.com/Zorax24/home-assistant-heiko/releases), download `heiko_w600-ha-0.5.1.zip` and `SHA256SUMS`. Use the installation ZIP, not GitHub's source ZIP.
2. Create a Home Assistant backup and keep a copy of any existing `heiko_w600` folder and W600 destination settings.
3. Extract the installation ZIP. Copy its `custom_components/heiko_w600` folder into your Home Assistant configuration directory. The resulting file must be `/config/custom_components/heiko_w600/manifest.json`. Some editors show the configuration directory as `/homeassistant`. Do not add a second nested `custom_components` directory.
4. Restart Home Assistant yourself. Open **Settings → Devices & services → Add integration → HEIKO W600**.
5. Set a local listener address and free TCP port. The defaults are `0.0.0.0:8899`, meaning all local interfaces. Select **Forward to manufacturer cloud** deliberately; it defaults to enabled for existing behavior. Manufacturer reference defaults are `www.myheatpump.com:18899`. These defaults are not proof that your module uses that endpoint.
6. Configure the W600's existing TCP client connection to the **reachable LAN address of Home Assistant** and the selected listener port. The W600 initiates the connection. `0.0.0.0` is a bind address, never a W600 destination. See [network and W600 details](docs/network.md) before changing anything.
7. Wait for fresh measurements and settings. Controls remain unavailable without fresh validated settings. Follow the dashboard steps below.

You need file access to the HA configuration directory, permission to restart HA, a W600 using the reference TCP protocol, and a routed LAN/VPN path from W600 to the listener. A browser connection to HA port 8123 does not test the W600 listener. **Do not expose the listener or W600 management interface to the internet.**

## Features and daily use

- Flow/return, outdoor and hot-water temperatures, compressor and pump states, and further mapped measurements. Unknown, invalid and stale readings are not invented.
- A catalog of **128 named settings**, including **125 writable controls** and three read-only version values. The installed entity count can vary with registry settings; it is not a compatibility guarantee.
- Normal controls: power, operating mode, room and hot-water targets, heating-curve shifts. **All settings** also includes service and protection settings. These can affect frost protection, electrical loads, anti-legionella operation, valves, pumps and screed drying. Ask a qualified technician before changing them. Reference ranges do not prove a value is safe for your device.
- **Request measurements / Request settings** send explicit read requests. They do not set a parameter.
- Writes are serialized and require fresh settings. A requested value is only confirmed after a new matching CMD02 settings frame. A timeout means an **unknown device outcome**; inspect the current value before retrying.
- CRC checks, identity checks, freshness monitoring, bounded frame parsing, reconnect handling and privacy-restricted downloadable diagnostics.

The supported operating modes and the choice labels come from the catalog. Actual availability depends on the controller. This is not a `climate` thermostat integration and does not calculate COP or energy totals.

## Create your dashboard

1. Open **Settings → Tools → Actions** (called Developer tools on some HA versions).
2. Select **Generate heat-pump dashboard** / `heiko_w600.export_dashboard`.
3. Choose `en` or `de`, or omit the language to use the HA system language (other languages fall back to English). In YAML mode:

   ```yaml
   action: heiko_w600.export_dashboard
   data:
     language: en
   ```

4. Run the action and copy the YAML **inside the `yaml` response field**; omit its wrapper and remove the wrapper's two-space indentation.
5. Create a **new empty dashboard** under Settings → Dashboards. Edit it, open the dashboard menu → Raw configuration editor, paste the YAML and save.

The export reads your own entity registry, including renamed IDs. It skips disabled entities and preserves explicitly customized names. It **never writes or overwrites any dashboard**. The three views are Overview, All settings, and Measurements and diagnosis. Short labels replace repeated device prefixes. For another export language, generate it again; existing dashboard labels are static. Entity translations follow HA's language mechanisms.

## Manufacturer cloud switch

**Forward to MyHeatPump** appears in the dashboard and integration configuration entities. It is available even before the W600 connects, and the chosen state persists across restarts and option changes.

- **On:** relay the full W600 TCP byte stream to the configured manufacturer endpoint, and relay manufacturer responses and commands back to the device. This can include protocol device identifiers, measurements, operating states and settings. Manufacturer-originated commands may change the pump. The integration adds no account credentials and does not filter the raw stream by field. The reference TCP transport is not encrypted by this integration.
- **Off:** close/prevent the manufacturer socket. Valid local CMD01/CMD02 frames get local CMD03/CMD04 acknowledgements. Local readings, read requests and writes with fresh readback remain implemented. MyHeatPump's live remote functions stop receiving this stream; data already held by the manufacturer is not deleted. Physical behavior in this mode remains unverified for this release.

Switching forwarding does not itself set a pump parameter. The W600 socket is preserved. Existing installations keep their saved state; missing legacy state means **on**, matching 0.4.0. Nothing silently changes a configured cloud choice.

## Updates, backup, rollback and removal

Before updates, back up HA, export any customized dashboard, and keep the previous component folder. Review [CHANGELOG](CHANGELOG.md), especially the 0.5.1 automation state changes. Replace only `/config/custom_components/heiko_w600` with the complete new folder and restart HA. Do not delete/re-add the integration for routine updates: domain, config-entry IDs and entity unique IDs remain unchanged.

To roll back, restore the previous component folder (and dashboard if required), restart HA, and restore the HA backup if configuration changes also need reverting. To remove, first restore a working W600 destination if it depended on this listener, remove the integration in Devices & services, then remove its component folder and restart HA. Remove dashboard rows and automations that reference removed entities. Removing this integration does not undo pump parameters or delete manufacturer data.

## Troubleshooting and support

| Symptom | What to check |
|---|---|
| Waiting for heat pump | W600 TCP client destination, reachable local/VPN route, matching listener port and firewall rules. |
| Listener cannot start | Port already used, bind address absent on the HA host, or permission problem. Use a free port and matching W600 setting. |
| No measurements / unavailable | Connection alone is insufficient: fresh, correctly addressed, valid CMD01 and CMD02 data are required. Check data ages and counters. |
| Cloud unavailable | Check configured endpoint and outgoing TCP reachability. The local W600 session stays open, but while forwarding is enabled local auto-ACK is not substituted for the cloud. |
| Write not confirmed | Inspect fresh settings; do not repeatedly retry or assume the device stayed unchanged. |
| Integration absent after copying | Check the exact folder path, full package contents and HA logs; restart HA and refresh the browser cache. |

For support, provide HA version, integration version, non-identifying model/controller/firmware details if known, and **Download diagnostics** from the integration menu. Diagnostics omit configured hosts, ports, account/device IDs, raw frames and actual temperatures/settings; they include software version, freshness ages/counts and connection/cloud flags. Review every attachment before sharing. Do not post credentials, raw traffic, screenshots with private details, or full serial/MAC addresses. See [technical details and verification](docs/verification.md).

## Installation methods, HACS and license

**Manual ZIP installation is the supported installation method.** Use the installation package attached to a release and follow the quick start above. The repository includes `hacs.json` and follows the [HACS integration layout requirements](https://www.hacs.dev/docs/publish/integration/). **Installation through HACS has not been validated.** Inclusion in the HACS default list and Home Assistant Brands has not been completed. Repository metadata and a successful Hassfest check alone do not establish HACS installation support.

MIT licensed. See [LICENSE](LICENSE) and [THIRD_PARTY_NOTICES](THIRD_PARTY_NOTICES.md) for the ioBroker reference provenance. This project is independent of the manufacturer and makes no device certification claim. Developers: [reproducible build and tests](docs/development.md).
