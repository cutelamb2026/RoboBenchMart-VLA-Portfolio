import argparse
from pathlib import Path
from .core import read_experiment, manifest_and_run, load_summary, write_group_csv

def main(argv=None):
    p=argparse.ArgumentParser(description='RoboBenchMart evaluation manifest and offline audit')
    subs=p.add_subparsers(dest='cmd',required=True)
    a=subs.add_parser('plan',help='write a reproducible command manifest without running')
    a.add_argument('config');a.add_argument('--out',default='artifacts/framework_runs')
    b=subs.add_parser('run',help='execute a validated atomic client; policy server must be running')
    b.add_argument('config');b.add_argument('--out',default='artifacts/framework_runs')
    c=subs.add_parser('audit',help='offline evaluation summary grouped by model and scene group')
    c.add_argument('summary');c.add_argument('--out',default='artifacts/framework_audit.csv')
    args=p.parse_args(argv)
    if args.cmd in ('plan','run'):
        exp=read_experiment(args.config)
        folder=Path(args.out)/exp.experiment_id
        manifest_and_run(exp,folder,execute=args.cmd=='run')
        print('manifest:',folder/'manifest.json')
    else:
        report=write_group_csv(load_summary(args.summary),args.out)
        print('output:',args.out,'groups:',len(report))
        print('WARNING: group totals include repeat runs and diagnostics; do not interpret as official benchmark scores.')

if __name__=='__main__':main()
