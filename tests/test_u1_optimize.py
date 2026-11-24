"""Constraints must reject a cheaper candidate that violates declared limits."""
import json
from pathlib import Path
import sys
import unittest
from unittest import mock
import zipfile
sys.path[:0] = [str(Path(__file__).resolve().parents[1]/'scripts'), str(Path(__file__).resolve().parent)]
import u1_optimize as optimize
import u1_project as project
import test_u1_project as project_fixtures


class OptimizeTests(unittest.TestCase):
    def setUp(self):
        self.fixture_case = project_fixtures.ProjectTests()
        self.fixture_case.setUp()
        self.addCleanup(self.fixture_case.doCleanups)
        self.root = self.fixture_case.root
        self.policy = {'minimum_walls': 4, 'minimum_infill_percent': 15, 'maximum_layer_height_mm': .2,
                       'infill_patterns': ['cubic'], 'infill_percentages': [], 'support_types': [], 'max_candidates': 2}
        self.policy_path = self.root/'constraints.json'
        self.policy_path.write_text(json.dumps(self.policy))
        self.policy = optimize.load_constraints(self.policy_path)

    def fixture(self, name, **changes):
        path = self.fixture_case.fixture(name, plates=1)
        with zipfile.ZipFile(path) as archive:
            members = {name: archive.read(name) for name in archive.namelist()}
        settings = json.loads(members['Metadata/project_settings.config'])
        settings.update(sparse_infill_pattern='gyroid', top_shell_layers='4', top_shell_thickness='0.8',
                        bottom_shell_layers='3', bottom_shell_thickness='0.6', enable_support='1', support_type='normal(auto)')
        settings.update(changes)
        members['Metadata/project_settings.config'] = json.dumps(settings)
        with zipfile.ZipFile(path, 'w') as archive:
            for name, data in members.items(): archive.writestr(name, data)
        return path

    def test_policy_refuses_typos_unbounded_search_and_unsafe_values(self):
        for changes in [{'minimum_walls':True}, {'minimum_infill_percent':-1}, {'maximum_layer_height_mm':float('nan')},
                        {'max_candidates':100}, {'speed':999}, {'infill_patterns':['unknown']}, {'infill_percentages':[5]},
                        {'support_types':['off']}]:
            with self.subTest(changes=changes):
                self.policy_path.write_text(json.dumps({**self.policy, **changes}))
                with self.assertRaises(ValueError): optimize.load_constraints(self.policy_path)

    def test_constraints_fail_for_weakened_walls_infill_layers_or_shells(self):
        baseline = self.fixture('base.3mf')
        self.assertTrue(optimize.constraint_check(baseline,self.policy)['passed'])
        for changes in [{'wall_loops':'2'}, {'sparse_infill_density':'10%'}, {'layer_height':'0.28'},
                        {'top_shell_layers':'1','top_shell_thickness':'0.2'}, {'bottom_shell_layers':'1','bottom_shell_thickness':'0.2'}]:
            with self.subTest(changes=changes):
                candidate = self.fixture('bad.3mf', **changes)
                self.assertFalse(optimize.constraint_check(candidate,self.policy,baseline=baseline)['passed'])

    def test_variant_preserves_recipe_source_and_removes_stale_gcode(self):
        source = self.fixture('base.3mf')
        with zipfile.ZipFile(source, 'a') as archive:
            archive.writestr('Metadata/plate_1.gcode','STALE_SYNTHETIC_CODE')
        original = source.read_bytes()
        target = optimize.write_variant(source, self.root/'variant.3mf', {'sparse_infill_pattern':'cubic'})
        self.assertEqual(source.read_bytes(), original)
        self.assertEqual(optimize.read_settings(target)['mixed_filament_definitions'], optimize.read_settings(source)['mixed_filament_definitions'])
        with zipfile.ZipFile(target) as archive:
            self.assertNotIn('Metadata/plate_1.gcode', archive.namelist())
        with self.assertRaises(ValueError): optimize.write_variant(source,self.root/'unsafe.3mf',{'post_process':'inert'})
        with self.assertRaises(ValueError): optimize.write_variant(source,source,{'sparse_infill_pattern':'cubic'})

    def test_global_constraints_do_not_claim_to_understand_object_overrides(self):
        source = self.fixture('base.3mf')
        with zipfile.ZipFile(source,'a') as archive:
            archive.writestr('Metadata/layer_heights_profile.txt','synthetic variable layer profile')
        check = optimize.constraint_check(source,self.policy)
        self.assertFalse(check['passed'])
        self.assertIn('adaptive/range', check['reasons'][0])
        source = self.fixture('plate-override.3mf')
        with zipfile.ZipFile(source) as archive:
            members = {name: archive.read(name) for name in archive.namelist()}
        members['Metadata/model_settings.config'] = members['Metadata/model_settings.config'].replace(b'<plate>', b'<plate><metadata key="wall_loops" value="1"/>', 1)
        with zipfile.ZipFile(source, 'w') as archive:
            for name, data in members.items(): archive.writestr(name, data)
        self.assertFalse(optimize.constraint_check(source,self.policy)['passed'])

    def test_bounded_candidates_choose_eligible_winner_and_report_actual_settings(self):
        source = self.fixture('base.3mf')
        candidate = self.fixture('candidate.3mf', sparse_infill_pattern='cubic')
        baseline_report = self.fixture_case.report(1, 12, 600, path=source)
        winner_report = self.fixture_case.report(1, 10, 500, path=candidate)
        with mock.patch.object(project.u1_slice, 'slice_model', side_effect=[baseline_report,winner_report]) as run:
            result = project.create_project([source],self.root/'job',plate_mode='keep',constraints_path=self.policy_path)
        self.assertEqual(run.call_count,2)
        self.assertEqual(result['selected_layout'],'infill-1')
        self.assertTrue(result['checks']['infill-1']['constraints']['passed'])
        self.assertEqual(result['effective_settings']['process']['sparse_infill_pattern'],'cubic')
        card = (self.root/'job'/'PRINT_CARD.md').read_text()
        self.assertIn('| Wall loops | 4 |',card)
        self.assertIn('Not checked',card)
        self.assertFalse(result['physical_strength_or_quality_tested'])

    def test_lower_price_cannot_override_failed_preservation(self):
        source = self.fixture('base.3mf')
        candidate = self.fixture('bad.3mf', sparse_infill_pattern='cubic', wall_loops='1')
        with mock.patch.object(project.u1_slice, 'slice_model', side_effect=[self.fixture_case.report(1,path=source),self.fixture_case.report(1,1,1,path=candidate)]):
            result = project.create_project([source],self.root/'job',plate_mode='keep',constraints_path=self.policy_path)
        self.assertEqual(result['selected_layout'],'keep')
        self.assertFalse(result['checks']['infill-1']['eligible'])
        self.assertIn('FAILED', (self.root/'job'/'PRINT_CARD.md').read_text())

    def test_native_export_must_retain_the_requested_alternative(self):
        source = self.fixture('base.3mf')
        # Slicer success with an unchanged pattern is not a tested cubic candidate.
        with mock.patch.object(project.u1_slice, 'slice_model', side_effect=[self.fixture_case.report(1,path=source), self.fixture_case.report(1,1,1,path=source)]):
            result = project.create_project([source],self.root/'job',plate_mode='keep',constraints_path=self.policy_path)
        self.assertEqual(result['selected_layout'],'keep')
        self.assertFalse(result['checks']['infill-1']['preservation']['passed'])
        self.assertIn('did not retain',result['checks']['infill-1']['preservation']['error'])

    def test_native_project_intent_overrides_are_not_silently_ignored(self):
        with self.assertRaisesRegex(ValueError,'retain their settings'):
            project.create_project([self.fixture('base.3mf')], self.root/'job', intent='strong')


if __name__ == '__main__':
    unittest.main()
