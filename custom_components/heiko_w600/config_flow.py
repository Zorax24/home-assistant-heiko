"""UI configuration flow for the HEIKO W600 integration."""

from __future__ import annotations

import ipaddress
import re
from collections.abc import Mapping
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult

from .const import (
    CONF_LISTEN_HOST,
    CONF_LISTEN_PORT,
    CONF_STALE_SECONDS,
    CONF_UPSTREAM_HOST,
    CONF_UPSTREAM_PORT,
    DEFAULT_LISTEN_HOST,
    DEFAULT_LISTEN_PORT,
    DEFAULT_STALE_SECONDS,
    DEFAULT_UPSTREAM_HOST,
    DEFAULT_UPSTREAM_PORT,
    DOMAIN,
    INTEGRATION_TITLE,
    INSTANCE_UNIQUE_ID,
    MAX_STALE_SECONDS,
    MAX_TCP_PORT,
    MIN_STALE_SECONDS,
    MIN_TCP_PORT,
)

_HOST_LABEL = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")


class ConfigFlowValidationError(ValueError):
    """A translated, safe configuration validation error."""

    def __init__(self, error_code: str) -> None:
        """Initialize the error with a translation key."""
        super().__init__(error_code)
        self.error_code = error_code


def _normalize_host(value: object, error_code: str) -> str:
    """Validate an IP address or hostname without resolving or contacting it."""
    if not isinstance(value, str):
        raise ConfigFlowValidationError(error_code)

    host = value.strip()
    if not host or len(host) > 253 or "%" in host:
        raise ConfigFlowValidationError(error_code)

    try:
        return ipaddress.ip_address(host).compressed
    except ValueError:
        pass

    if any(character in host for character in "/\\:@?#[]"):
        raise ConfigFlowValidationError(error_code)

    hostname = host[:-1] if host.endswith(".") else host
    try:
        ascii_hostname = hostname.encode("idna").decode("ascii").lower()
    except UnicodeError as err:
        raise ConfigFlowValidationError(error_code) from err

    if not ascii_hostname or len(ascii_hostname) > 253:
        raise ConfigFlowValidationError(error_code)

    labels = ascii_hostname.split(".")
    if any(
        not label or len(label) > 63 or not _HOST_LABEL.fullmatch(label)
        for label in labels
    ):
        raise ConfigFlowValidationError(error_code)

    # Numeric dotted strings are ambiguous when they are not valid IP addresses.
    if all(label.isdecimal() for label in labels):
        raise ConfigFlowValidationError(error_code)

    return ascii_hostname


def _parse_integer(
    value: object,
    *,
    error_code: str,
    minimum: int,
    maximum: int,
) -> int:
    """Parse a decimal integer and enforce an inclusive range."""
    if isinstance(value, bool):
        raise ConfigFlowValidationError(error_code)

    if isinstance(value, int):
        parsed = value
    elif isinstance(value, str) and re.fullmatch(r"[0-9]+", value.strip()):
        parsed = int(value.strip(), 10)
    else:
        raise ConfigFlowValidationError(error_code)

    if not minimum <= parsed <= maximum:
        raise ConfigFlowValidationError(error_code)

    return parsed


def validate_config(user_input: Mapping[str, Any]) -> dict[str, str | int | bool]:
    """Return only validated, non-secret listener and upstream settings."""
    if not isinstance(user_input, Mapping):
        raise ConfigFlowValidationError("invalid_input")

    if type(user_input.get("upstream_enabled", True)) is not bool:
        raise ConfigFlowValidationError("invalid_upstream_enabled")

    return {
        "upstream_enabled": user_input.get("upstream_enabled", True),
        CONF_LISTEN_HOST: _normalize_host(
            user_input.get(CONF_LISTEN_HOST), "invalid_listen_host"
        ),
        CONF_LISTEN_PORT: _parse_integer(
            user_input.get(CONF_LISTEN_PORT),
            error_code="invalid_listen_port",
            minimum=MIN_TCP_PORT,
            maximum=MAX_TCP_PORT,
        ),
        CONF_UPSTREAM_HOST: _normalize_host(
            user_input.get(CONF_UPSTREAM_HOST), "invalid_upstream_host"
        ),
        CONF_UPSTREAM_PORT: _parse_integer(
            user_input.get(CONF_UPSTREAM_PORT),
            error_code="invalid_upstream_port",
            minimum=MIN_TCP_PORT,
            maximum=MAX_TCP_PORT,
        ),
        CONF_STALE_SECONDS: _parse_integer(
            user_input.get(CONF_STALE_SECONDS),
            error_code="invalid_stale_seconds",
            minimum=MIN_STALE_SECONDS,
            maximum=MAX_STALE_SECONDS,
        ),
    }


CONFIG_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_LISTEN_HOST, default=DEFAULT_LISTEN_HOST): str,
        vol.Required(CONF_LISTEN_PORT, default=str(DEFAULT_LISTEN_PORT)): str,
        vol.Required(CONF_UPSTREAM_HOST, default=DEFAULT_UPSTREAM_HOST): str,
        vol.Required(CONF_UPSTREAM_PORT, default=str(DEFAULT_UPSTREAM_PORT)): str,
        vol.Required(CONF_STALE_SECONDS, default=str(DEFAULT_STALE_SECONDS)): str,
        vol.Required("upstream_enabled", default=True): bool,
    }
)


class HeikoW600ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Set up one HEIKO W600 config entry per Home Assistant instance."""

    VERSION = 1

    @staticmethod
    def async_get_options_flow(config_entry):
        return HeikoOptionsFlow()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Collect validated TCP listener, upstream, and freshness settings."""
        await self.async_set_unique_id(INSTANCE_UNIQUE_ID)
        self._abort_if_unique_id_configured()

        if self._async_current_entries():
            return self.async_abort(reason="already_configured")

        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                config = validate_config(user_input)
            except ConfigFlowValidationError as err:
                errors["base"] = err.error_code
            else:
                return self.async_create_entry(
                    title=INTEGRATION_TITLE,
                    data=config,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=CONFIG_SCHEMA,
            errors=errors,
        )


class HeikoOptionsFlow(config_entries.OptionsFlowWithReload):
    """Edit transport options without deleting the device and its entities."""

    async def async_step_init(self, user_input=None):
        errors = {}
        if user_input is not None:
            try:
                data = validate_config(user_input)
            except ConfigFlowValidationError as err:
                errors["base"] = err.error_code
            else:
                if "upstream_enabled" not in user_input:
                    data["upstream_enabled"] = self.config_entry.options.get("upstream_enabled", self.config_entry.data.get("upstream_enabled", True))
                return self.async_create_entry(title="", data={**self.config_entry.options, **data})
        current = {**self.config_entry.data, **self.config_entry.options}
        schema_fields = {vol.Required(key, default=str(value)): str
                             for key, value in current.items()
                             if key in (CONF_LISTEN_HOST, CONF_LISTEN_PORT,
                                        CONF_UPSTREAM_HOST, CONF_UPSTREAM_PORT,
                                        CONF_STALE_SECONDS)}
        schema_fields[vol.Required("upstream_enabled", default=current.get("upstream_enabled", True))] = bool
        schema = vol.Schema(schema_fields)
        return self.async_show_form(step_id="init", data_schema=schema, errors=errors)
