"""Constants for the HEIKO W600 integration."""

from typing import Final

DOMAIN: Final = "heiko_w600"
INTEGRATION_TITLE: Final = "HEIKO W600"
INSTANCE_UNIQUE_ID: Final = "heiko_w600_single_instance"

CONF_LISTEN_HOST: Final = "listen_host"
CONF_LISTEN_PORT: Final = "listen_port"
CONF_UPSTREAM_HOST: Final = "upstream_host"
CONF_UPSTREAM_PORT: Final = "upstream_port"
CONF_STALE_SECONDS: Final = "stale_seconds"

DEFAULT_LISTEN_HOST: Final = "0.0.0.0"
DEFAULT_LISTEN_PORT: Final = 8899
DEFAULT_UPSTREAM_HOST: Final = "www.myheatpump.com"
DEFAULT_UPSTREAM_PORT: Final = 18899
DEFAULT_STALE_SECONDS: Final = 180

MIN_TCP_PORT: Final = 1
MAX_TCP_PORT: Final = 65535
MIN_STALE_SECONDS: Final = 30
MAX_STALE_SECONDS: Final = 3600
