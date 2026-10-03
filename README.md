[Deutsch](README.de.md) · **English**

# HEIKO W600 for Home Assistant

**Vibe-coded:** This project was developed with AI coding assistants. Automated checks do not replace review or testing with your actual heat pump. See [verification and limitations](docs/verification.md).

A **custom integration**, not a Supervisor app/add-on. It receives W600 TCP data in Home Assistant, exposes measurements and the complete reference settings catalog, and can optionally relay the connection to MyHeatPump. No separate server process or cloud account login is required.

**Status: 0.6.0, experimental.** **Physical communication and selected writes have been confirmed on a HEIKO Thermal 9 with W600:** live measurements, a mode change with fresh settings readback, and a subsequent heat-pump response were observed. This confirms the tested functions on one installation; it is not acceptance of every parameter or a separate hardware test of the 0.6.0 package. The catalog originates from a HEIKO ioBroker adapter; this is not a manufacturer-certified compatibility list. Do not assume another controller or firmware supports every parameter. See [verification and limitations](docs/verification.md).

## Languages

English, German and Polish are included for setup, options, entity labels/choices, messages and dashboard exports. Home Assistant uses its system language for default entity names; explicit custom names are preserved. Choose `pl` in the `heiko_w600.export_dashboard` action for a Polish dashboard. Existing dashboards have static labels and are not replaced automatically. Translation files follow the [official HA mechanism](https://developers.home-assistant.io/docs/internationalization/custom_integration/).

## Installation

### Add the repository in HACS — prepared for public availability

This route is prepared for a publicly accessible repository; it is **not yet an installation-tested release path**. HACS must already be installed. HACS cannot use private repositories, even when you can access them on GitHub ([official FAQ](https://hacs.dev/docs/faq/private_repositories/)). Until that requirement and the remaining HACS checks are met, use the three-step ZIP method below.

[![Open repository in HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Zorax24&repository=home-assistant-heiko&category=integration)

Or add it manually:

1. Open **HACS → ⋮ → Custom repositories**.
2. Paste `https://github.com/Zorax24/home-assistant-heiko`, choose **Integration**, and click **Add**.
3. Open **HEIKO W600**, download it, then restart Home Assistant.
4. Open **Settings → Devices & services → Add integration → HEIKO W600**.

No Supervisor add-on repository is needed. A HACS listing is not required for the custom-repository route, but repository availability and an actual HACS installation test still need checking.

### Install now without HACS — three steps

Make a Home Assistant backup first. If updating, keep the previous component folder.

1. [Download the installation ZIP](https://github.com/Zorax24/home-assistant-heiko/releases/download/v0.6.0/heiko_w600-ha-0.6.0.zip) and extract it.
2. Copy its `custom_components/heiko_w600` folder into `/config/custom_components/` on your Home Assistant host.
3. Restart Home Assistant, then click [Add HEIKO W600](https://my.home-assistant.io/redirect/config_flow_start/?domain=heiko_w600) or use **Settings → Devices & services → Add integration**.

The final path is `/config/custom_components/heiko_w600/manifest.json`. Some editors call `/config` `/homeassistant`. Use the installation ZIP, not GitHub's source ZIP. A checksum is available under [Releases](https://github.com/Zorax24/home-assistant-heiko/releases).

## Connect the heat pump

1. In the integration setup, keep the listener defaults `0.0.0.0` and TCP port `8899` if that port is free. Choose deliberately whether to forward to MyHeatPump.
2. Set the W600's existing TCP client destination to your Home Assistant host's **reachable LAN/VPN address** and port `8899` (or your chosen port). Save the previous W600 destination before changing it.
3. Wait for fresh measurements and settings, then [create your dashboard](#create-your-dashboard).

The W600 opens the connection. `0.0.0.0` is never its destination; HA's web port `8123` is a different service. **Do not expose the listener to the internet.** The manufacturer reference endpoint is `www.myheatpump.com:18899`, configurable in setup. Check [network and W600 details](docs/network.md) if your module's settings differ, you use Docker/VPN, or no data arrives.

Requirements: Home Assistant 2026.9.4 or newer (tested with 2026.9.4), a W600 using the reference TCP protocol, and a working LAN/VPN route. The ZIP method also requires access to the HA configuration directory. Controls remain unavailable until fresh validated settings arrive.

## Features and daily use

- Flow/return, outdoor and hot-water temperatures, compressor and pump states, and further mapped measurements. Unknown, invalid and stale readings are not invented.
- A catalog of **128 named settings**, including **125 writable controls** and three read-only version values. The installed entity count can vary with registry settings; it is not a compatibility guarantee.
- Normal controls: power, operating mode, room and hot-water targets, heating-curve shifts. **All settings** also includes service and protection settings. These can affect frost protection, electrical loads, anti-legionella operation, valves, pumps and screed drying. Ask a qualified technician before changing them. Reference ranges do not prove a value is safe for your device.
- **Request measurements / Request settings** send explicit read requests. They do not set a parameter.
- Writes are serialized and require fresh settings. A requested value is only confirmed after a new matching CMD02 settings frame. A timeout means an **unknown device outcome**; inspect the current value before retrying.
- CRC checks, identity checks, freshness monitoring, bounded frame parsing, reconnect handling and privacy-restricted downloadable diagnostics.

The supported operating modes and the choice labels come from the catalog. Actual availability depends on the controller. This is not a `climate` thermostat integration and does not calculate COP or energy totals.

Pump/compressor status uses **On/Off**. **Unavailable** means there is no fresh valid reading, not that the device is off. Function/enable switches describe permission to operate; they do not prove that heating or a pump is currently running. Existing exported dashboard labels are static; regenerate the export after an update to apply revised names. Explicit custom names are preserved.

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

**MyHeatPump forwarding** appears in the dashboard and integration configuration entities. It is available even before the W600 connects, and the chosen state persists across restarts and option changes.

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

**Manual ZIP installation is the supported installation method.** Use the installation package attached to a release and follow the three steps above. The repository includes `hacs.json` and follows the [HACS integration layout requirements](https://www.hacs.dev/docs/publish/integration/). **Installation through HACS has not been validated.** Inclusion in the HACS default list and Home Assistant Brands has not been completed. Repository metadata and a successful Hassfest check alone do not establish HACS installation support.

MIT licensed. See [LICENSE](LICENSE) and [THIRD_PARTY_NOTICES](THIRD_PARTY_NOTICES.md) for the ioBroker reference provenance. This project is independent of the manufacturer and makes no device certification claim. Developers: [reproducible build and tests](docs/development.md).
