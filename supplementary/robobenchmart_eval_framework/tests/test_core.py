import csv
import json
import tempfile
import unittest
from pathlib import Path
from rbm_eval.core import Experiment, load_summary, group_report, manifest_and_run, wilson_interval

class CoreTests(unittest.TestCase):
    def setUp(self):
        self.exp=Experiment(experiment_id='test01', model='pi05', env_id='Env', scene_dir='scene', protocol='UNSEEN', num_traj=3, max_horizon=50)
    def test_command_and_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)
            self.assertIsNone(manifest_and_run(self.exp,p))
            self.assertEqual(json.loads((p/'manifest.json').read_text())['config']['model'],'pi05')
            self.assertIn('--max-horizon', self.exp.command())
    def test_robo_requires_pose_seed(self):
        with self.assertRaises(ValueError):
            Experiment(**{**self.exp.__dict__,'protocol':'ROBO'}).validate()
    def test_train_requires_json(self):
        with self.assertRaises(ValueError):
            Experiment(**{**self.exp.__dict__,'protocol':'TRAIN'}).validate()
    def test_summary_audit(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'summary.csv'
            with p.open('w',newline='') as f:
                w=csv.DictWriter(f,fieldnames=['model','experiment','scene_group','episodes','successes','success_rate','total_steps'])
                w.writeheader();w.writerow({'model':'octo','experiment':'e1','scene_group':'g','episodes':10,'successes':0,'success_rate':0,'total_steps':100})
            rows=load_summary(p);report=group_report(rows)
            self.assertEqual(report[0]['successes'],0)
            self.assertGreater(report[0]['wilson_95_high'],0)
    def test_bad_rate_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'a.csv'
            p.write_text('model,experiment,scene_group,episodes,successes,success_rate,total_steps\nocto,e,g,2,1,0.0,5\n')
            with self.assertRaises(ValueError):load_summary(p)
    def test_wilson(self):
        a,b=wilson_interval(0,10)
        self.assertEqual(a,0)
        self.assertTrue(0.2<b<0.4)

if __name__=='__main__':unittest.main()
