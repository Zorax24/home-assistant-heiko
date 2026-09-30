[Deutsch](network.de.md) · **English**

# W600 connection and network

## Confirmed by source, not a hardware setup wizard

The reference adapter runs a TCP server. The W600 connects as a TCP **client** to that server. This integration implements the same direction:

```text
Heat-pump controller ↔ W600 → local HA listener → optional manufacturer TCP endpoint
                             ← replies/commands ←
```

HA initiates the separate outgoing manufacturer connection only while forwarding is enabled and a W600 session exists. Read requests/parameter commands return over the established W600 socket. The reference defaults are listener port **8899** and manufacturer endpoint **www.myheatpump.com:18899**. They are configurable defaults, not universal device requirements. There is no incoming connection required from the manufacturer and no cloud login flow.

## Configure your own reachable destination

Before a W600 change, record its existing connection mode, destination, port and any relevant vendor instructions. On a module using the referenced protocol, keep the required TCP-client mode and set its remote TCP destination to the reachable HA host address and your listener port. Menu names, W600 firmware UI, management address, login credentials, UART settings and required reboot steps are **not established by this project**. Use your module's documented controls; do not copy guessed defaults from unrelated W600 products. The HA integration cannot configure the module for you.

For a normal same-LAN installation, use your HA host's actual LAN address. With Docker, publish the selected TCP listener port or use an appropriate host network; do not assume HA's web port publishes it. With HAOS, the listener runs in Core's network environment; confirm local firewall/routing reachability. With a routed VPN, ensure W600-to-HA and return paths exist. If using a separate TCP relay, the module's destination is that reachable relay address and port, which must forward to HA. No particular relay/VPN product or private network layout is bundled.

Examples in tests use loopback, documentation ranges or `.example` domains. Substitute your own values. Do not configure documentation addresses on your device. `0.0.0.0` and `::` are bind addresses, not destinations. A bind hostname must resolve to a local interface, not the W600.

## Limits and exposure

One config entry and one active W600 session are supported per HA instance. A new session replaces the old one. The listener has no TLS, login or network-source allowlist; isolate it to the trusted device LAN/VPN and use firewall rules to limit clients. Never forward it from the public internet. Manufacturer traffic is relayed without rewriting/filtering; device identities and manufacturer commands can pass through. This is not a standalone encrypted tunnel.

Cloud reconnection is independent of W600 reconnection (10-second connect timeout, 5-second retry delay). Data is not queued for later cloud delivery. When forwarding is enabled but its connection is down, local decoding continues; local auto-ACK is only used when forwarding is deliberately disabled. How a particular device behaves without cloud responses is not hardware-proven here.

If removing the integration, restore the previously recorded W600 path first. Network changes and physical commissioning are the installer's responsibility; the release process does not contact any real pump or manufacturer endpoint.
