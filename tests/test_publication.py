"""Distribution, localization and compatibility regressions with synthetic data."""
import asyncio
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from test_config_flow import FLOW, _input
from test_runtime import HeikoCoordinator
from heiko_w600.dashboard import build_dashboard
from heiko_w600.parameters import CATALOG
from heiko_w600.select import HeikoSelect

ROOT=Path(__file__).resolve().parents[1]
COMPONENT=ROOT/'custom_components/heiko_w600'

class PublicationTests(unittest.TestCase):
    def test_translation_key_and_enum_parity_for_complete_catalog(self):
        from tools.check_project import translation_keys
        en=json.loads((COMPONENT/'translations/en.json').read_text(encoding="utf-8"))
        de=json.loads((COMPONENT/'translations/de.json').read_text(encoding="utf-8"))
        self.assertEqual(translation_keys(en),translation_keys(de))
        for p in CATALOG:
            platform='sensor' if not p['writable'] else 'switch' if p['type']=='boolean' else 'select' if p['pageControl']=='select' else 'number'
            for lang in (en,de):
                item=lang['entity'][platform][f"setting_{p['settingIndex']:03d}"]
                self.assertTrue(item['name'])
                if platform=='select':self.assertEqual(set(item['state']),{f'option_{k}' for k in p['states']})

    def test_catalog_and_protocol_retained_after_line_ending_normalization(self):
        baseline=json.loads((ROOT/'tests/baseline.json').read_text(encoding="utf-8"))
        self.assertEqual(hashlib.sha256((COMPONENT/'parameters.json').read_bytes()).hexdigest(),baseline['catalog_sha256'])
        self.assertEqual(hashlib.sha256((COMPONENT/'protocol.py').read_bytes()).hexdigest(),baseline['protocol_sha256'])

    def test_bilingual_dashboard_excludes_disabled_and_foreign_entities(self):
        entities=[SimpleNamespace(unique_id='test_par04',entity_id='sensor.user_flow',name=None,original_name='Old name',config_entry_id='test',disabled_by=None),
                  SimpleNamespace(unique_id='test_setting_003',entity_id='select.disabled',config_entry_id='test',disabled_by='user'),
                  SimpleNamespace(unique_id='test_setting_000',entity_id='switch.foreign',config_entry_id='foreign',disabled_by=None)]
        for lang,label in [('en','Flow temperature'),('de','Vorlauftemperatur')]:
            dashboard=build_dashboard('test',entities,lang)
            rows=[row for view in dashboard['views'] for card in view['cards'] for row in card.get('entities',[])]
            self.assertTrue(rows)
            self.assertTrue(all(row['entity']=='sensor.user_flow' for row in rows))
            self.assertTrue(all(row['name']==label for row in rows))

    def test_custom_dashboard_name_is_preserved_in_both_languages(self):
        entry=SimpleNamespace(unique_id='test_par04',entity_id='sensor.user_flow',name='Custom flow',config_entry_id='test',disabled_by=None)
        for language in ('en','de'):
            dashboard=build_dashboard('test',[entry],language)
            rows=[row for view in dashboard['views'] for card in view['cards'] for row in card.get('entities',[])]
            self.assertTrue(all(row['name']=='Custom flow' for row in rows))

    def test_setup_cloud_choice_is_explicit_strict_and_legacy_enabled(self):
        self.assertTrue(FLOW.validate_config(_input())['upstream_enabled'])
        self.assertFalse(FLOW.validate_config(_input(upstream_enabled=False))['upstream_enabled'])
        for value in ('false',0,None):
            with self.assertRaises(FLOW.ConfigFlowValidationError): FLOW.validate_config(_input(upstream_enabled=value))

    def test_service_groups_have_bilingual_risk_warning(self):
        for language in ('en','de'):
            dashboard=build_dashboard('test',[],language)
            warning=next(card for card in dashboard['views'][1]['cards'] if card['type']=='markdown')
            self.assertTrue(warning['content'])

    def test_no_explicit_name_overrides_translation_keys(self):
        import ast
        for name in ('parameter_entity.py','switch.py','button.py','bridge_sensor.py'):
            tree=ast.parse((COMPONENT/name).read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node,ast.Assign):
                    self.assertFalse(any(isinstance(target,ast.Attribute) and target.attr=='_attr_name' or isinstance(target,ast.Name) and target.id=='_attr_name' for target in node.targets))

class PublicationAsyncTests(unittest.IsolatedAsyncioTestCase):
    async def test_options_edit_preserves_off_choice_without_legacy_input(self):
        flow=FLOW.HeikoOptionsFlow()
        flow.config_entry=SimpleNamespace(data=FLOW.validate_config(_input()),options={'upstream_enabled':False,'retained_option':'synthetic'})
        result=await flow.async_step_init(_input(stale_seconds='240'))
        self.assertFalse(result['data']['upstream_enabled'])
        self.assertEqual(result['data']['retained_option'],'synthetic')
        self.assertEqual(result['data']['stale_seconds'],240)

    async def test_select_tokens_and_legacy_service_alias_have_same_wire_code(self):
        writes=[]
        async def record(index,value): writes.append((index,value))
        coordinator=SimpleNamespace(settings={'setting_003':1.0},async_write_parameter=record)
        definition=next(p for p in CATALOG if p['settingIndex']==3)
        entity=HeikoSelect(coordinator,'synthetic',definition)
        self.assertEqual(entity.options,['option_0','option_1','option_2','option_3','option_4'])
        self.assertEqual(entity.current_option,'option_1')
        self.assertEqual(entity.unique_id,'synthetic_setting_003')
        await entity.async_select_option('option_1')
        await entity.async_select_option('Heizen')
        self.assertEqual(writes,[(3,1.0),(3,1.0)])

    async def test_actual_port_conflict_fails_with_safe_translation_key(self):
        from homeassistant.exceptions import ConfigEntryNotReady
        server=await asyncio.start_server(lambda r,w:w.close(),'127.0.0.1',0)
        entry=SimpleNamespace(data={'listen_host':'127.0.0.1','listen_port':server.sockets[0].getsockname()[1],'upstream_enabled':False},options={})
        coordinator=HeikoCoordinator(SimpleNamespace(),entry)
        try:
            with self.assertRaises(ConfigEntryNotReady) as raised:await coordinator.async_start()
            self.assertEqual(raised.exception.translation_key,'listener_unavailable')
            self.assertNotIn('127.0.0.1',str(raised.exception))
        finally:
            await coordinator.async_stop()
            server.close()
            await server.wait_closed()
