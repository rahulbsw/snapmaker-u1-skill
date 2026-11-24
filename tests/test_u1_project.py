"""Project delivery, preservation and all-plate accounting contracts."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock
import zipfile
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import u1_project as project
import u1_slice as slicer


class ProjectTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def fixture(self, name='input.3mf', *, x=10, z=0, wall='4', plates=2, paint='1', count=2):
        path = self.root / name
        settings = {'wall_loops': wall, 'sparse_infill_density': '25%', 'layer_height': '0.2',
                    'mixed_filament_definitions': ['synthetic-calibrated-recipe'],
                    'filament_colour': ['#FF0000', '#FFFFFF'], 'wipe_tower_x': ['25']}
        items = ''.join(f'<item objectid="1" transform="1 0 0 0 1 0 0 0 1 {x+i*30} 10 {z}"/>' for i in range(count))
        model = f'<model xmlns="{project.CORE[1:-1]}" unit="millimeter"><resources><object id="1"><mesh><vertices><vertex x="0" y="0" z="0"/></vertices><triangles><triangle v1="0" v2="0" v3="0" paint_color="{paint}"/></triangles></mesh></object></resources><build>{items}</build></model>'
        native_plates = ''.join(f'<plate><metadata key="plater_id" value="{i+1}"/><metadata key="filament_maps" value="1 2"/><model_instance><metadata key="object_id" value="1"/></model_instance></plate>' for i in range(plates))
        with zipfile.ZipFile(path, 'w') as archive:
            archive.writestr('Metadata/project_settings.config', json.dumps(settings))
            archive.writestr('Metadata/model_settings.config', '<config><object id="1"><metadata key="extruder" value="1"/></object>'+native_plates+'</config>')
            archive.writestr('3D/3dmodel.model', model)
        return path

    def report(self, plates=2, grams=12, seconds=600, completed=True, path=None):
        return {'slice_completed': completed, 'plate_totals': {'plate_count': plates, 'filament_grams': grams,
                'duration_seconds': seconds, 'all_plates_sliced': completed},
                'artifacts': {'project': str(path or self.fixture()), 'report': 'internal/slicing.json'}}

    def test_xy_only_preservation_and_multi_material_recipe(self):
        source = self.fixture()
        moved = self.fixture('moved.3mf', x=80, plates=1)
        self.assertTrue(project.preservation_check(source, moved)['passed'])
        for name, change in [('weakened', {'wall':'2'}), ('lifted', {'z':1}),
                             ('paint', {'paint':'2'}), ('lost-part', {'count':1})]:
            with self.subTest(name=name):
                candidate = self.fixture(name+'.3mf', **change)
                self.assertFalse(project.preservation_check(source, candidate)['passed'])
        self.assertEqual(project.project_signature(source)['settings']['mixed_filament_definitions'], ['synthetic-calibrated-recipe'])

    def test_incompatible_plate_overrides_rejected(self):
        source = self.fixture()
        with zipfile.ZipFile(source) as archive:
            members = {name:archive.read(name) for name in archive.namelist()}
        members['Metadata/model_settings.config'] = members['Metadata/model_settings.config'].replace(b'value="1 2"', b'value="2 1"', 1)
        with zipfile.ZipFile(source, 'w') as archive:
            for name, data in members.items(): archive.writestr(name, data)
        with self.assertRaisesRegex(ValueError, 'different overrides'):
            project.project_signature(source)

    def test_composed_offsets_preserved_and_assembly_spacing_protected(self):
        def assembly(name, component_z, build_z, spacing):
            path = self.fixture(name, z=build_z)
            with zipfile.ZipFile(path) as archive:
                members = {name: archive.read(name) for name in archive.namelist()}
            model = ET.fromstring(members['3D/3dmodel.model'])
            ns = project.CORE
            obj = ET.SubElement(model.find(ns+'resources'), ns+'object', id='2')
            components = ET.SubElement(obj, ns+'components')
            for x in (0, spacing):
                ET.SubElement(components, ns+'component', objectid='1', transform=f'1 0 0 0 1 0 0 0 1 {x} 0 {component_z}')
            for item in model.findall(ns+'build/'+ns+'item'):
                item.set('objectid', '2')
            members['3D/3dmodel.model'] = ET.tostring(model)
            with zipfile.ZipFile(path, 'w') as archive:
                for name, data in members.items(): archive.writestr(name, data)
            return path
        source = assembly('assembly.3mf', 3, 0, 20)
        normalized = assembly('normalized.3mf', 0, 3, 20)
        moved_part = assembly('changed-spacing.3mf', 0, 3, 21)
        self.assertTrue(project.preservation_check(source, normalized)['passed'])
        self.assertFalse(project.preservation_check(source, moved_part)['passed'])

    def test_balanced_requires_non_worsening_time_material_and_plates(self):
        baseline = self.report()
        self.assertEqual(project.choose_layout(baseline, self.report(1, 10, 500))[0], 'combine')
        for candidate in [self.report(1, 13, 500), self.report(1, 10, 650), self.report(3, 10, 500), self.report(1, None, 500), self.report(completed=False)]:
            self.assertEqual(project.choose_layout(baseline, candidate)[0], 'keep')
        self.assertEqual(project.choose_layout(baseline, self.report(1, 10, 500), preserved=False)[0], 'keep')
        self.assertEqual(project.choose_layout(self.report(completed=False), self.report())[0], None)

    def test_explicit_objectives_allow_visible_time_material_tradeoff(self):
        baseline, candidate = self.report(), self.report(1, 15, 500)
        self.assertEqual(project.choose_layout(baseline,candidate,objective='time')[0], 'combine')
        self.assertEqual(project.choose_layout(baseline,candidate,objective='filament')[0], 'keep')
        self.assertEqual(project.choose_layout(baseline,candidate,objective='plates')[0], 'combine')

    def test_compact_delivery_and_rejected_candidate_retains_original(self):
        source = self.fixture()
        combined = self.fixture('combined.3mf', x=50, plates=1)
        original = source.read_bytes()
        for bad, expected in [(False, 'combine'), (True, 'keep')]:
            if bad: combined = self.fixture('bad.3mf', wall='2', plates=1)
            destination = self.root / str(bad)
            with mock.patch.object(slicer, 'slice_model', side_effect=[self.report(path=source), self.report(1, 10, 500, path=combined)]) as run:
                result = project.create_project([source], destination)
            self.assertEqual(result['selected_layout'], expected)
            self.assertEqual(set(p.name for p in destination.iterdir()), {'project.3mf', 'PRINT_CARD.md', '.work'})
            self.assertEqual(run.call_count, 2)
            self.assertTrue(run.call_args_list[0].kwargs['preserve_project'])
            self.assertFalse(run.call_args_list[0].kwargs['arrange'])
            self.assertTrue(run.call_args_list[1].kwargs['arrange'])
            self.assertEqual((destination/'project.3mf').read_bytes(), (combined if expected=='combine' else source).read_bytes())
            self.assertFalse(result['ready_to_print'])
        self.assertEqual(source.read_bytes(), original)

    def test_failure_stops_without_retry_or_stale_project(self):
        source, destination = self.fixture(), self.root/'failed'
        with mock.patch.object(slicer, 'slice_model', return_value=self.report(completed=False)) as run:
            result = project.create_project([source], destination)
        run.assert_called_once()
        self.assertIsNone(result['project'])
        self.assertFalse((destination/'project.3mf').exists())
        self.assertTrue((destination/'PRINT_CARD.md').exists())
        with mock.patch.object(slicer, 'slice_model') as run, self.assertRaisesRegex(ValueError, 'empty output'):
            project.create_project([source], destination)
        run.assert_not_called()

    def test_preprocessing_in_same_job_work_folder_is_kept(self):
        destination = self.root/'job'
        prepared = destination/'.work'/'prepared'
        prepared.mkdir(parents=True)
        master = prepared/'master.stl'
        master.write_bytes(b'original editable master placeholder')
        native = self.fixture()
        with mock.patch.object(slicer, 'slice_model', return_value=self.report(1, path=native)):
            result = project.create_project([master], destination)
        self.assertTrue(result['project'])
        self.assertEqual(master.read_bytes(), b'original editable master placeholder')
        self.assertEqual({p.name for p in destination.iterdir()}, {'project.3mf', 'PRINT_CARD.md', '.work'})

    def test_adaptive_layer_metadata_cannot_be_silently_dropped(self):
        source = self.fixture()
        with zipfile.ZipFile(source, 'a') as archive:
            archive.writestr('Metadata/layer_config_ranges.xml', '<ranges><range min_z="10" max_z="20" wall_loops="6"/></ranges>')
        lost = self.fixture('lost-layers.3mf')
        check = project.preservation_check(source, lost)
        self.assertFalse(check['passed'])
        self.assertIn('auxiliary', check['changed'])

    def test_all_plate_totals_deduplicate_external_copies_but_not_identical_plates(self):
        source = self.fixture()
        def code(i, embedded=True):
            return {'archive_member':f'Metadata/plate_{i}.gcode' if embedded else None,
                    'path':f'/work/plate_{i}.gcode', 'sha256':'same-for-both-plates',
                    'estimates':{'filament_grams_by_tool':[1,2], 'estimated_duration_seconds':60}}
        artifacts = [code(1,False), code(2,False), code(1), code(2)]
        totals = slicer.project_totals(source, artifacts)
        self.assertEqual(totals['plate_count'], 2)
        self.assertEqual(totals['filament_grams'], 6)
        self.assertEqual(totals['duration_seconds'], 120)
        self.assertTrue(totals['all_plates_sliced'])
        self.assertFalse(slicer.project_totals(source, [code(1)])['all_plates_sliced'])
        artifacts[-1]['estimates']['filament_grams_by_tool'] = None
        self.assertIsNone(slicer.project_totals(source, artifacts)['filament_grams'])

    def test_native_command_preserves_settings_and_disables_orientation(self):
        command = slicer.build_command('orca', self.fixture(), self.root/'run', arrange=True, preserve_project=True)
        self.assertNotIn('--load-settings', command)
        self.assertNotIn('--load-filaments', command)
        self.assertNotIn('--assemble', command)
        self.assertNotIn('--allow-newer-file=1', command)
        self.assertIn('--allow-rotations=0', command)
        self.assertEqual(command[command.index('--orient')+1], '0')
        self.assertEqual(command[command.index('--slice')+1], '0')

    def test_mac_seatbelt_refuses_native_execution_before_launch(self):
        source = self.root/'box.stl'
        source.write_bytes(b'inert fixture')
        with mock.patch.object(slicer.sys, 'platform', 'darwin'), mock.patch.dict(slicer.os.environ, {'CODEX_SANDBOX':'seatbelt'}), mock.patch.object(slicer.subprocess,'run') as run:
            with self.assertRaisesRegex(ValueError, 'AppKit/OpenGL'):
                slicer.slice_model(source,self.root/'out')
        run.assert_not_called()
        self.assertFalse((self.root/'out').exists())


if __name__ == '__main__':
    unittest.main()
