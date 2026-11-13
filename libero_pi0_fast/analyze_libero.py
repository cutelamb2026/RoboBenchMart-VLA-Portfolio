#!/usr/bin/env python3
"""Aggregate real LIBERO per-task rollout counts; no inferred results."""
import argparse, csv, json, math
from collections import defaultdict
from pathlib import Path

SUITES = ("libero_spatial", "libero_object", "libero_goal", "libero_10")

def wilson(k, n, z=1.959963984540054):
    if n <= 0: return None
    p = k / n
    den = 1 + z*z/n
    centre = (p + z*z/(2*n))/den
    margin = z*math.sqrt(p*(1-p)/n + z*z/(4*n*n))/den
    return [max(0., centre-margin), min(1., centre+margin)]

def summarize(rows):
    by_suite = defaultdict(list)
    observed = set()
    for row in rows:
        suite = row['suite'].strip()
        if suite not in SUITES: raise ValueError(f'Unknown suite: {suite!r}')
        task = int(row['task_id']); k = int(row['successes']); n=int(row['trials'])
        if task not in range(10): raise ValueError(f'task_id outside 0..9: {task}')
        if not (0 <= k <= n and n > 0): raise ValueError(f'invalid successes/trials for {suite}/{task}: {k}/{n}')
        key = (suite, task)
        if key in observed: raise ValueError(f'duplicate suite/task: {key}')
        observed.add(key)
        by_suite[suite].append({'task_id': task, 'successes': k, 'trials': n, 'success_rate': k/n, 'wilson_95': wilson(k,n)})
    result = {'suites':{}, 'overall':{}, 'caveat':'Trial-level independence and matching benchmark settings must be verified.'}
    total_k=total_n=0
    for suite in SUITES:
        items=sorted(by_suite[suite],key=lambda x:x['task_id'])
        k=sum(r['successes'] for r in items); n=sum(r['trials'] for r in items)
        total_k+=k;total_n+=n
        result['suites'][suite] = {'tasks_observed':len(items),'complete_ten_tasks':len(items)==10,
            'all_50_trials':len(items)==10 and all(r['trials']==50 for r in items),
            'successes':k, 'trials':n, 'pooled_success_rate':k/n if n else None,
            'mean_task_success_rate':sum(r['success_rate'] for r in items)/len(items) if items else None,
            'wilson_95_pooled':wilson(k,n), 'tasks':items}
    result['overall']={'successes':total_k,'trials':total_n,'pooled_success_rate':total_k/total_n if total_n else None,
        'complete_four_suites':all(result['suites'][s]['all_50_trials'] for s in SUITES),
        'wilson_95_pooled':wilson(total_k,total_n)}
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--input',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    with args.input.open(newline='',encoding='utf-8-sig') as f:
        rows=list(csv.DictReader(f))
    if not rows: raise SystemExit('No real experiment rows found. Fill the results CSV first.')
    result=summarize(rows)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f"Recorded {result['overall']['trials']} trials, {result['overall']['successes']} successes")
    for suite,r in result['suites'].items():
        if r['trials']:
            print(f"{suite}: {r['successes']}/{r['trials']} = {r['pooled_success_rate']:.2%}; tasks={r['tasks_observed']}, full50={r['all_50_trials']}")
    print(f'Report: {args.output}')
if __name__=='__main__': main()
