"""Export a localized dashboard from the current entity registry, without saving it."""
import json
from pathlib import Path
from .parameters import CATALOG

_TEXT = json.loads(Path(__file__).with_name("dashboard_strings.json").read_text(encoding="utf-8"))
_ENTITIES = {language: json.loads(Path(__file__).with_name("translations").joinpath(f"{language}.json").read_text(encoding="utf-8"))["entity"] for language in ("en", "de")}


def build_dashboard(entry_id, entities, language="de"):
    """Resolve stable unique IDs, preserving renamed IDs and explicit custom names."""
    language = "de" if language == "de" else "en"
    text = _TEXT[language]
    ui = text["ui"]
    names = {key: value["name"] for platform in _ENTITIES[language].values() for key, value in platform.items()}
    registry = {item.unique_id: item for item in entities
                if item.config_entry_id == entry_id and not item.disabled_by}

    def rows(suffixes):
        result = []
        for suffix in suffixes:
            if not (item := registry.get(f"{entry_id}_{suffix}")):
                continue
            name = getattr(item, "name", None) or names.get(suffix) or getattr(item, "original_name", None) or suffix
            if name.casefold().startswith("heiko w600 "):
                name = name[len("HEIKO W600 "):]
            result.append({"entity": item.entity_id, "name": name})
        return result

    def card(title, entries):
        return {"type": "entities", "title": title, "show_header_toggle": False, "entities": entries}

    quick = [f"setting_{p['settingIndex']:03d}" for p in CATALOG if p['sectionName'] == 'Schnelleinstellungen']
    overview = [card(ui["connection"], rows(["connection_state", "upstream_enabled", "last_write_result", "realtime_age", "settings_age", "request_06", "request_07"])),
                card(ui["controls"], rows(quick)),
                card(ui["temperatures"], rows(["par04", "par05", "par07", "par24", "par36", "par01", "compressor_running", "par20", "par32", "par33", "par34", "par35"]))]
    parameter_cards = [card(ui["cloud"], rows(["upstream_enabled"])),
                       {"type": "markdown", "title": ui["risk_title"], "content": ui["risk_message"]}]
    for section in dict.fromkeys(p['sectionName'] for p in CATALOG):
        entries = rows([f"setting_{p['settingIndex']:03d}" for p in CATALOG if p['sectionName'] == section])
        if entries:
            title = text["sections"][section]
            if section not in ("Schnelleinstellungen", "Benutzereinstellungen", "Systeminformationen", "Ferienmodus", "Reduzierter Heizbetrieb"):
                title = "Service · " + title
            parameter_cards.append(card(title, entries))
    measurements = rows([f"par{i:02d}" for i in range(1, 44)] + ["compressor_running"])
    measurements = list({row["entity"]: row for row in measurements}.values())
    return {"title": ui["title"], "views": [
        {"title": ui["overview"], "path": "waermepumpe", "icon": "mdi:heat-pump", "cards": overview},
        {"title": ui["settings"], "path": "einstellungen", "icon": "mdi:tune", "cards": parameter_cards},
        {"title": ui["diagnosis"], "path": "messwerte", "icon": "mdi:chart-line", "cards": [
            card(ui["measurements"], measurements),
            card(ui["bridge"], rows(["connection_state", "upstream_enabled", "bytes_to_cloud", "bytes_to_unit", "frames_received", "last_write_result"]))]},
    ]}
