"""Framework layer (newly authored). No model weights or simulator bundled.

This wraps the user's existing RoboBenchMart evaluation clients, it does not
claim to solve the control/action adapter alignment or improve task success.
"""
from __future__ import annotations
import csv
import json
import hashlib
import math
import subprocess
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

@dataclass(frozen=True)
class Experiment:
    experiment_id: str
    model: str
    env_id: str
    scene_dir: str
    protocol: str
    num_traj: int
    max_horizon: int
    start_seed: int = 0
    robot_init_pose_start_seed: Optional[int] = None
    json_path: Optional[str] = None
    action_exec_cap: Optional[int] = None
    host: str = 'localhost'
    port: int = 8000
    client_script: str = 'scripts/eval_policy_client_custom.py'
    save_video: bool = False
    save_traj: bool = True
    checkpoint_id: str = 'UNVERIFIED'
    code_revision: str = 'UNVERIFIED'

    def validate(self):
        if not self.experiment_id or '/' in self.experiment_id or '\\' in self.experiment_id:
            raise ValueError('experiment_id must be a simple nonempty directory name')
        if self.model not in {'octo', 'pi05'}:
            raise ValueError('only experimentally supported models octo/pi05 are allowed')
        if self.protocol not in {'TRAIN', 'ROBO', 'UNSEEN', 'OOD', 'ATOMIC', 'COMPOSITE', 'DIAGNOSTIC'}:
            raise ValueError('invalid protocol')
        if self.num_traj <= 0 or self.max_horizon <= 0:
            raise ValueError('num_traj and max_horizon must be positive')
        if self.action_exec_cap is not None and self.action_exec_cap <= 0:
            raise ValueError('action_exec_cap must be positive')
        if not 1 <= self.port <= 65535:
            raise ValueError('invalid port')
        if self.protocol == 'TRAIN' and not self.json_path:
            raise ValueError('TRAIN requires a scene seed JSON to reproduce train arrangements')
        if self.protocol == 'ROBO' and self.robot_init_pose_start_seed is None:
            raise ValueError('ROBO requires a robot init pose seed')
        if self.client_script != 'scripts/eval_policy_client_custom.py':
            raise ValueError('framework currently supports atomic client only; composite stage runner requires separate adapter')
        return self

    def command(self):
        self.validate()
        cmd = ['python', self.client_script, '--env-id', self.env_id,
               '--scene-dir', self.scene_dir, '--eval-subdir', self.experiment_id,
               '--num-traj', str(self.num_traj), '--max-horizon', str(self.max_horizon),
               '--start-seed', str(self.start_seed), '--host', self.host, '--port', str(self.port)]
        if self.json_path: cmd += ['--json-path', self.json_path]
        if self.robot_init_pose_start_seed is not None:
            cmd += ['--robot-init-pose-start-seed', str(self.robot_init_pose_start_seed)]
        if self.action_exec_cap is not None:
            cmd += ['--max-exec-actions', str(self.action_exec_cap)]
        if self.save_video: cmd += ['--save-video']
        if self.save_traj: cmd += ['--save-traj']
        return cmd


def read_experiment(path):
    data = json.loads(Path(path).read_text(encoding='utf-8'))
    return Experiment(**data).validate()


def manifest_and_run(exp: Experiment, out_dir: Path, execute=False):
    """Always persist the exact command and config; dry-run by default."""
    exp.validate()
    out_dir.mkdir(parents=True, exist_ok=True)
    command = exp.command()
    payload = {'config': asdict(exp), 'command': command,
               'config_sha256': hashlib.sha256(json.dumps(asdict(exp), sort_keys=True).encode()).hexdigest(),
               'execution_requested': execute}
    (out_dir / 'manifest.json').write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    if not execute: return None
    with (out_dir / 'console.log').open('w', encoding='utf-8') as log:
        proc = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, check=False)
    (out_dir / 'returncode.txt').write_text(str(proc.returncode), encoding='utf-8')
    if proc.returncode != 0: raise RuntimeError(f'evaluation exited with {proc.returncode}; see console.log')
    return proc.returncode


def load_summary(path):
    required={'model','experiment','scene_group','episodes','successes','success_rate','total_steps'}
    with Path(path).open(newline='', encoding='utf-8-sig') as f:
        reader=csv.DictReader(f)
        if not required.issubset(reader.fieldnames or []):
            raise ValueError(f'missing summary columns: {sorted(required-set(reader.fieldnames or []))}')
        rows=[]
        for r in reader:
            n=int(r['episodes']); s=int(r['successes']); steps=int(r['total_steps'])
            if n <= 0 or not 0 <= s <= n or steps < 0:
                raise ValueError(f'invalid counts: {r}')
            rate=float(r['success_rate'])
            if not math.isclose(rate, s/n, abs_tol=1e-9):
                raise ValueError(f'inconsistent rate: {r}')
            rows.append({**r,'episodes':n,'successes':s,'total_steps':steps, 'success_rate':rate})
    return rows


def wilson_interval(successes: int, total: int, z=1.95996398454):
    """Two-sided Wilson interval; independent Bernoulli assumption."""
    if total<=0 or not 0<=successes<=total: raise ValueError('invalid counts')
    p=successes/total; den=1+z*z/total
    center=(p+z*z/(2*total))/den
    radius=z*math.sqrt(p*(1-p)/total+z*z/(4*total*total))/den
    return (0.0 if successes == 0 else max(0.0,center-radius)), (1.0 if successes == total else min(1.0,center+radius))


def group_report(rows, group='scene_group'):
    groups={}
    for row in rows:
        key=(row['model'], row.get(group,'UNKNOWN'))
        current=groups.setdefault(key, {'experiments':0,'episodes':0,'successes':0,'steps':0})
        current['experiments']+=1
        current['episodes']+=row['episodes']
        current['successes']+=row['successes']
        current['steps']+=row['total_steps']
    result=[]
    for (model,name),val in sorted(groups.items()):
        n,s=val['episodes'],val['successes']
        lo,hi=wilson_interval(s,n)
        result.append({'model':model,'group':name,**val,'observed_rate':s/n,
                       'wilson_95_low':lo,'wilson_95_high':hi})
    return result


def write_group_csv(rows,path):
    report=group_report(rows)
    dest=Path(path);dest.parent.mkdir(parents=True,exist_ok=True)
    with dest.open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=['model','group','experiments','episodes','successes','steps','observed_rate','wilson_95_low','wilson_95_high']);w.writeheader();w.writerows(report)
    return report
