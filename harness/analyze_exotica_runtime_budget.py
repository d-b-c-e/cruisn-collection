"""Measure saved admission occupancy separately from finite diagnostic budgets."""
import argparse
import json
from pathlib import Path
import re
from exotica_admissions import bounded_csv,verify


def analyze(directory):
    directory=Path(directory)
    path=directory/'stderr.log'
    if not path.is_file() or path.stat().st_size>16*1024*1024:
        raise ValueError('missing or oversized completion log')
    text=path.read_text(encoding='utf-8',errors='replace')
    start=re.findall(r'^MIDZ_MODEL_ENDPOINT=2 first=(\d+) last=(\d+) snapshot=(\d+)$',text,re.M)
    admit=re.findall(r'^MIDZ_MODEL_ADMIT_FIRST=(\d+)$',text,re.M)
    if len(start)!=1 or len(admit)!=1:raise ValueError('missing unique endpoint/admission scope')
    first,last,snapshot=map(int,start[0])
    trial=dict(mode='draw',first=first,last=last,snapshot=snapshot,admit_from=int(admit[0]))
    if re.findall(r'^MIDZ_ENDPOINT_MARKED=([01])$',text,re.M)==['1']:trial['scope']='marked'
    if 'MIDZ_ENDPOINT_EARLY=1' in text:trial['early']='endpoint'
    fields=('id','slot','epoch','generation','realm','section','source')
    originals=[{k:int(row[k]) for k in fields} for row in bounded_csv(directory/'exotica-endpoint-models.csv',65536)]
    ledger=verify(trial,text,directory,originals,measure_occupancy=True)
    def receipt(prefix):
        found=re.findall('^'+re.escape(prefix)+r' (.*)$',text,re.M)
        if len(found)!=1:raise ValueError('missing unique completion receipt: '+prefix)
        items=found[0].split();pairs=[x.split('=',1) for x in items]
        if any(len(p)!=2 or not p[1].isdigit() for p in pairs):raise ValueError('noninteger budget receipt')
        result={k:int(v) for k,v in pairs}
        if len(result)!=len(pairs) or result.get('complete')!=1:raise ValueError('incomplete budget receipt')
        return result
    life=receipt('MIDZ_LIFETIME_RESULT');endpoint=receipt('MIDZ_MODEL_ENDPOINT_RESULT')
    waiting=receipt('MIDZ_HOST_WAITING_RESULT');handover=receipt('MIDZ_HOST_HANDOVER_RESULT')
    early=receipt('MIDZ_ENDPOINT_EARLY_RESULT') if trial.get('early') else {'permissions':0}
    observations=[('lifetime journal rows',life['records'],200000),
        ('endpoint ticket journal IDs',endpoint['commits'],65536),
        ('admission packet journal',ledger['packets'],20000),
        ('admission journal bytes',ledger['bytes'],64*1024*1024),
        ('waiting scene journal',waiting['scenes'],20000),
        ('handover cohort journal bytes',handover['bytes'],64*1024*1024),
        ('early permission journal rows',early['permissions'],200000)]
    budgets=[dict(name=name,observed=value,diagnostic_cap=cap,remaining=cap-value,used_percent=100*value/cap)
             for name,value,cap in observations]
    if any(x['remaining']<0 for x in budgets):raise ValueError('captured totals exceed documented diagnostic caps')
    return dict(passed=True,source=str(directory),ledger=ledger,diagnostic_budgets=budgets,
        limit_scope='Caps from the September15 diagnostic implementation; not proposed production limits. '
                    'Observed map occupancy is not heap usage. No repeated-race or continuous-runtime guarantee, and no time-to-failure extrapolation.')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory',type=Path);parser.add_argument('--report',required=True,type=Path)
    args=parser.parse_args()
    if args.report.exists():raise ValueError('refusing to overwrite prior budget evidence')
    try:
        result=analyze(args.directory)
    except (ValueError,OSError,KeyError) as error:
        result=dict(passed=False,source=str(args.directory),error=str(error))
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))
    return 0 if result['passed'] else 1


if __name__=='__main__':raise SystemExit(main())
