"""One-shot FINAL evaluation of the committed frozen configuration."""

from datetime import datetime, timezone
import fcntl
import hashlib
import json
from pathlib import Path
import subprocess

import numpy as np
import pandas as pd

from airalerts.evaluate import bootstrap_bss, log_result, metric_row, latest_results
from airalerts.features import observed_features, GROUP_A, GROUP_B, GROUP_L
from airalerts.hgb import chronological_tails, select_iterations, refit
from airalerts.io import load_official, valid_end
from airalerts.models import ReferenceModel
from airalerts.panel import build_panel
from airalerts.pooled import PooledLogistic, recency_weights

PREDICTIONS = Path('data/processed/predictions/final_test.csv.gz')
CHECKPOINT = Path('data/processed/predictions/final_checkpoint')
REPORT = Path('reports/model/final_test.md')


def train_mask(panel: pd.DataFrame, train_start: pd.Timestamp, test_start: pd.Timestamp,
               embargo: int, lead: int) -> pd.Series:
    if embargo < 25 or embargo < lead+1:
        raise ValueError('FINAL embargo must be >=25 and >=lead+1')
    return (panel['T'].ge(train_start) & panel['T'].lt(test_start-pd.Timedelta(hours=embargo)) &
            (panel['T']+pd.Timedelta(hours=lead+1)).le(test_start) & panel[f'y_{lead}'].notna())


def assert_frozen(config: dict) -> None:
    if config['official_variant']!='B' or config['embargo_hours']!=25 or config['test_start']!='2026-08-01':
        raise ValueError('Unexpected frozen protocol')
    if set(config['models'])!=set(map(str,[0,1,2,3,4,5,6,12,24])):
        raise ValueError('Require all nine frozen leads')
    for spec in config['models'].values():
        if not set(spec['features']) <= set(GROUP_A+GROUP_B+GROUP_L):
            raise ValueError('Unknown frozen feature')
        base = spec['hyperparameters']['base_model'] if spec['model'].startswith('ens_ses_') else spec
        if base['features']!=spec['features'] or base['half_life']!=spec['half_life']:
            raise ValueError('Ensemble/base feature or recency mismatch')
        if spec['model'].startswith('ens_ses_'):
            ses=spec['hyperparameters']['ses']['hyperparameters']
            if ses['alpha_candidates']!=[.01,.05,.1,.3,.6] or ses['warmup_days']!=56 or ses['trend'] or ses['seasonality']:
                raise ValueError('Frozen SES rule differs from reusable implementation')
            if spec['ensemble_weight'] not in (.25,.5,.75):raise ValueError('Unexpected frozen ensemble weight')
        hp=base['hyperparameters']
        if base['model'].startswith('hgb'):
            expected={'inner_embargo_hours':25,'method':'chronological TRAIN Brier','min_improvement':1e-5,
                      'patience_trees':30,'step_trees':10,'tail_days':14}
            if hp['early_stopping']!=expected or hp['calibration']['method']!='none' or hp['calibration_tail_days']!=14:
                raise ValueError('Unsupported frozen HGB fitting rule')
            for key,val in {'l2_regularization':0.,'max_bins':255,'max_leaf_nodes':31,'min_samples_leaf':20,'random_state':42}.items():
                if hp[key]!=val:raise ValueError('Frozen HGB defaults differ from reusable implementation')
        elif base['model'].startswith('logreg'):
            for key,val in {'class_weight':None,'max_iter':1000,'penalty':'l2','scaler':'TRAIN-only StandardScaler','solver':'lbfgs'}.items():
                if hp[key]!=val:raise ValueError('Frozen logistic defaults differ')
        else:raise ValueError('Unsupported frozen model')
        if 'fixed_long_memory' in hp:
            if hp['fixed_long_memory']!={'ewma_half_life_hours':336,'ewma_initial_level':0.,'ewma_origin':'2022-03-15T00:00:00+00:00','share_hours':672}:
                raise ValueError('Long-memory constants differ')


def predict_frozen(spec: dict, train: pd.DataFrame, rows: pd.DataFrame, lead: int,
                   train_end: pd.Timestamp, seed: int, ses: np.ndarray):
    """No validation/test tuning; only frozen TRAIN fitting rules are invoked."""
    ensemble=spec['model'].startswith('ens_ses_')
    base=spec['hyperparameters']['base_model'] if ensemble else spec
    columns=tuple(base['features']); hp=base['hyperparameters']; half=float(base['half_life'])
    fitted={'base_model':base['model'],'train_n':len(train),'train_max_T':str(train['T'].max())}
    if base['model'].startswith('logreg'):
        weights=None if np.isinf(half) else recency_weights(train,train_end,half)
        model=PooledLogistic(columns,hp['C'],seed).fit(train,weights)
        p=model.predict_proba(rows,lead)
        fitted['C']=hp['C']
    else:
        tails=chronological_tails(train,train_end,lead,25)
        iterations,history=select_iterations(tails['core'],tails['stop'],columns,hp['learning_rate'],hp['max_depth'],
                                            half,train_end,seed,caps=(hp['max_iter'],))
        n=iterations[hp['max_iter']]
        p,_=refit(tails['fit'],tails['cal'],rows,columns,hp['learning_rate'],hp['max_depth'],n,half,train_end,seed)
        fitted.update(iterations=n,stopping_history=history,actual_fit_n=len(tails['fit']),
                      actual_fit_max_T=str(tails['fit']['T'].max()),calibration='none')
    if ensemble:
        weight=spec['ensemble_weight']
        p=weight*p+(1-weight)*ses
        fitted['ensemble_weight']=weight
    if not np.isfinite(p).all() or ((p<0)|(p>1)).any():
        raise ValueError('Pipeline bug: invalid FINAL probabilities')
    return p,fitted


def _atomic_json(path: Path, value: dict):
    tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n');tmp.replace(path)


def run(config_path: Path=Path('config/final_config.json'), official_path: Path=Path('data/raw/official_data_en.csv')):
    commit=subprocess.check_output(['git','log','-1','--format=%H','--',str(config_path)],text=True).strip()
    print('Frozen config commit:',commit,flush=True)
    committed=subprocess.check_output(['git','show',f'{commit}:{config_path.as_posix()}'])
    if committed!=config_path.read_bytes():raise ValueError('Config differs from committed bytes')
    config=json.loads(committed);assert_frozen(config)
    import sklearn
    versions={'python':__import__('sys').version.split()[0],'numpy':np.__version__,'pandas':pd.__version__,'sklearn':sklearn.__version__}
    if versions!=config['versions']:raise ValueError('Runtime versions differ from frozen validation environment')
    if hashlib.sha256(official_path.read_bytes()).hexdigest()!=config['inputs_sha256']['official']:
        raise ValueError('Raw input differs from freeze')
    CHECKPOINT.mkdir(parents=True,exist_ok=True)
    with (CHECKPOINT/'lock').open('w') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        return _run_locked(config,config_path,official_path,commit)


def _run_locked(config,config_path,official_path,commit):
    state_path=CHECKPOINT/'state.json'
    if state_path.exists():
        state=json.loads(state_path.read_text())
        if state['status']=='complete':raise ValueError('FINAL already completed; refusing another prediction run')
        if state['config_sha256']!=hashlib.sha256(config_path.read_bytes()).hexdigest():raise ValueError('Checkpoint config mismatch')
        pending=state.get('predicting_lead')
        if pending is not None and not (CHECKPOINT/f'lead_{pending}.csv.gz').exists():
            raise ValueError('Interrupted prediction has no checkpoint; stop, do not predict that lead again')
    else:
        if PREDICTIONS.exists() or REPORT.exists():raise ValueError('FINAL outputs already exist')
        existing=pd.read_csv('reports/model/results.csv',usecols=['fold_id'],dtype=str)
        if existing.fold_id.eq('test').any():raise ValueError('Existing TEST log; refusing prediction run')
        state={'status':'started','config_sha256':hashlib.sha256(config_path.read_bytes()).hexdigest(),
               'commit':commit,'run_id':datetime.now(timezone.utc).strftime('final-%Y%m%dT%H%M%S%f'),
               'created_at':datetime.now(timezone.utc).isoformat(),'fitted':{},
               'runner_sha256':hashlib.sha256(Path(__file__).read_bytes()+Path('src/airalerts/features.py').read_bytes()).hexdigest()}
        _atomic_json(state_path,state)
    official=load_official(official_path)
    raw_end=valid_end(official);end=raw_end.floor('h')
    start=pd.Timestamp(config['train_start'],tz='UTC');test=pd.Timestamp(config['test_start'],tz='UTC')
    train_end=test-pd.Timedelta(hours=25)
    events=official.loc[official.started_at.lt(end)].copy()
    panel=build_panel(events,start,end,variant='B',day_windows=(),week_windows=(),history_days=56)
    observed=observed_features(events,panel,include_long_memory=True,final_test=True)
    if observed[['oblast','T']].equals(panel[['oblast','T']]) is False:raise ValueError('Panel/feature alignment differs')
    # Verify the new authorised end cannot change the frozen pre-TEST history.
    from airalerts.ladder import read_panel
    old=read_panel(Path('data/processed/panel.csv.gz'))
    known=panel.loc[panel['T'].lt(train_end)]
    columns=['state',*[c for c in old if c.startswith('ses_') or c.startswith('y_')]]
    joined=known[['oblast','T',*columns]].merge(old[['oblast','T',*columns]],on=['oblast','T'],suffixes=('_new','_old'),validate='one_to_one')
    if len(joined)!=len(known):raise ValueError('Frozen TRAIN history keys differ')
    for column in columns:
        np.testing.assert_allclose(joined[column+'_new'].to_numpy(dtype=float),joined[column+'_old'].to_numpy(dtype=float),atol=1e-12,rtol=0)
    cache=Path('data/processed/ladder_features_long.csv.gz')
    if cache.exists():
        old_features=pd.read_csv(cache,parse_dates=['T'])
        columns=[c for c in GROUP_A+GROUP_B+GROUP_L if c!='base_rate']
        joined=observed.loc[observed['T'].lt(train_end),['oblast','T',*columns]].merge(old_features[['oblast','T',*columns]],on=['oblast','T'],suffixes=('_new','_old'),validate='one_to_one')
        if len(joined)!=len(known):raise ValueError('Frozen TRAIN feature keys differ')
        for column in columns:
            np.testing.assert_allclose(joined[column+'_new'],joined[column+'_old'],atol=1e-12,rtol=0)
    print('Frozen TRAIN labels, SES levels and cached as-of features match before any TEST prediction',flush=True)
    for col in GROUP_A+GROUP_B+GROUP_L:
        if col!='base_rate':panel[col]=observed[col].to_numpy()
    state.update(test_start=str(test),test_end=str(end),trimmed_end_unfloored=str(raw_end),train_end=str(train_end))
    _atomic_json(state_path,state)
    for k in sorted(map(int,config['models'])):
        part=CHECKPOINT/f'lead_{k}.csv.gz'
        if part.exists():continue
        tr=train_mask(panel,start,test,25,k)
        ev=panel['T'].ge(test)&panel[f'y_{k}'].notna()&(panel['T']+pd.Timedelta(hours=k+1)).le(end)
        train,rows=panel.loc[tr].copy(),panel.loc[ev].copy()
        assert (train['T']+pd.Timedelta(hours=k+1)).max()<=test
        assert train['T'].max()<train_end
        rates=train.groupby('oblast').y_0.mean()
        target_rates=train.groupby('oblast')[f'y_{k}'].mean()
        for frame in [train,rows]:
            frame['base_rate']=frame.oblast.map(rates);frame['y']=frame[f'y_{k}'].astype(float)
        pred=rows[['oblast','T','y']].copy()
        refs={}
        for column,name in [('clim','climatology'),('persistence','persistence_prob'),('ses','ses')]:
            model=ReferenceModel(name,(k,),(),(),(.01,.05,.1,.3,.6)).fit(train)
            refs[column]=model
        state['predicting_lead']=k;_atomic_json(state_path,state)
        for column,model in refs.items():pred[column]=model.predict_proba(rows,k)
        spec=config['models'][str(k)]
        pred['p'],fitted=predict_frozen(spec,train,rows,k,train_end,config['seed'],pred.ses.to_numpy())
        fitted['ses_alpha']=refs['ses'].params[k]['chosen']
        pred['lead']=k;pred['model']=spec['model'];pred['run_id']=state['run_id'];pred['git_commit']=commit
        pred['train_positive_rate']=pred.oblast.map(target_rates)
        pred['flagged']=(pred.train_positive_rate<config['flag_thresholds']['low'])|(pred.train_positive_rate>config['flag_thresholds']['high'])
        tmp=part.with_suffix('.tmp')
        pred.to_csv(tmp,index=False,compression={'method':'gzip','mtime':0});tmp.replace(part)
        state['fitted'][str(k)]=fitted;state['predicting_lead']=None;_atomic_json(state_path,state)
        print(f'Lead {k}: frozen fit and single TEST prediction saved; scores not inspected',flush=True)
    parts=[pd.read_csv(CHECKPOINT/f'lead_{k}.csv.gz',parse_dates=['T']) for k in sorted(map(int,config['models']))]
    pred=pd.concat(parts,ignore_index=True)
    pred.to_csv(PREDICTIONS,index=False,compression={'method':'gzip','mtime':0})
    evaluate(pred,config,state)
    state['status']='complete';_atomic_json(state_path,state)


def read_log_keys(path: Path) -> pd.DataFrame:
    """Avoid chunked dtype inference for mixed numeric/text fold identifiers."""
    return pd.read_csv(path, usecols=['run_id','model','lead','scope','fold_id'],
                       low_memory=False, dtype={'run_id':str,'model':str,'lead':int,'scope':str,'fold_id':str})


def finish_saved(config_path: Path=Path('config/final_config.json')) -> None:
    """Evaluate existing checkpoints only; no refitting or prediction calls."""
    state_path=CHECKPOINT/'state.json'
    state=json.loads(state_path.read_text())
    if state['status']=='complete':raise ValueError('FINAL already evaluated')
    committed=subprocess.check_output(['git','show',f"{state['commit']}:{config_path.as_posix()}"])
    if config_path.read_bytes()!=committed or hashlib.sha256(committed).hexdigest()!=state['config_sha256']:
        raise ValueError('Frozen config/checkpoint mismatch')
    config=json.loads(committed);assert_frozen(config)
    leads=sorted(map(int,config['models']))
    if sorted(map(int,state['fitted']))!=leads or state.get('predicting_lead') is not None:
        raise ValueError('Prediction checkpoints incomplete; refusing any prediction rerun')
    with (CHECKPOINT/'lock').open('w') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        pred=pd.read_csv(PREDICTIONS,parse_dates=['T'],low_memory=False)
        parts=pd.concat([pd.read_csv(CHECKPOINT/f'lead_{k}.csv.gz',parse_dates=['T'],low_memory=False) for k in leads],ignore_index=True)
        pd.testing.assert_frame_equal(pred,parts,check_dtype=False,check_exact=False,rtol=0,atol=1e-14)
        if pred.duplicated(['oblast','T','lead']).any() or set(pred.lead)!=set(leads):
            raise ValueError('Invalid saved prediction keys')
        if set(pred.run_id)!={state['run_id']} or set(pred.git_commit)!={state['commit']}:
            raise ValueError('Saved prediction provenance mismatch')
        start,end=pd.Timestamp(state['test_start']),pd.Timestamp(state['test_end'])
        if pred['T'].lt(start).any() or (pred['T']+pd.to_timedelta(pred.lead+1,unit='h')).gt(end).any():
            raise ValueError('Saved target windows exceed TEST bounds')
        for column in ['p','clim','persistence','ses','y']:
            if not np.isfinite(pred[column]).all() or not pred[column].between(0,1).all():
                raise ValueError('Invalid saved probability/label')
        if not pred.y.isin([0,1]).all():raise ValueError('Nonbinary TEST labels')
        print(f"Evaluating {len(pred)} saved prediction rows; no refitting or new predictions",flush=True)
        evaluate(pred,config,state)
        state['status']='complete';state['evaluation_recovered']=True
        _atomic_json(state_path,state)


def evaluate(pred,config,state):
    results=[];intervals=[];regions=[]
    existing=read_log_keys(Path('reports/model/results.csv'))
    done=set(zip(existing.loc[existing.run_id.eq(state['run_id'])&existing.fold_id.eq('test')].lead,
                 existing.loc[existing.run_id.eq(state['run_id'])&existing.fold_id.eq('test')].scope))
    validation=latest_results(Path('reports/model/results.csv'))
    for k,frame in pred.groupby('lead'):
        scopes={'ALL':frame,'ALL_excl_flagged':frame.loc[~frame.flagged]}
        scopes.update(dict(tuple(frame.groupby('oblast'))))
        for scope,subset in scopes.items():
            metrics=metric_row(subset)
            cis={}
            for ref in ['clim','persistence','ses']:
                low,high=bootstrap_bss(subset,ref,config['seed'],config['bootstrap']['samples'],7)
                cis[ref]=(low,high)
                intervals.append({'lead':k,'scope':scope,'reference':ref,'low':low,'high':high})
            row={'run_id':state['run_id'],'git_commit':state['commit'],'created_at':state['created_at'],'model':config['models'][str(k)]['model'],
                 'params_json':json.dumps({'frozen':config['models'][str(k)],'fitted':state['fitted'][str(k)],'config_sha256':state['config_sha256'],'runner_sha256':state['runner_sha256']},sort_keys=True),
                 'seed':config['seed'],'train_start':config['train_start'],'fold_id':'test','eval_start':state['test_start'],'eval_end':state['test_end'],
                 'lead':int(k),'scope':scope,**metrics,'bss_ci_low':cis['clim'][0],'bss_ci_high':cis['clim'][1],'notes':'final'}
            if (k,scope) not in done:log_result(Path('reports/model/results.csv'),row)
            results.append(row)
            if scope=='ALL':
                val=validation.loc[validation.model.eq(row['model'])&validation.lead.eq(k)&validation.fold_id.eq('pooled')&validation.scope.eq('ALL')&validation.run_id.eq(config['models'][str(k)]['validation_run_id'])]
                if len(val)!=1:raise ValueError('Frozen validation row missing')
                values=val.iloc[0]
                row.update(validation_brier=values.brier,validation_ece=values.ece,
                           validation_bss_clim=values.bss_vs_clim,validation_bss_persistence=values.bss_vs_persistence,validation_bss_ses=values.bss_vs_ses)
            elif scope not in ('ALL_excl_flagged',):
                regions.append({'lead':k,'oblast':scope,'train_positive_rate':subset.train_positive_rate.iloc[0],
                                'flagged':bool(subset.flagged.iloc[0]),**metrics})
    rows=pd.DataFrame(results);ci=pd.DataFrame(intervals);reg=pd.DataFrame(regions)
    rows.to_csv('reports/model/final_test_metrics.csv',index=False)
    ci.to_csv('reports/model/final_test_bootstrap.csv',index=False);reg.to_csv('reports/model/final_test_per_oblast.csv',index=False)
    pooled=rows.loc[rows.scope.eq('ALL')].copy()
    lines=['# FINAL TEST — frozen configuration','',f"VERIFIED: config commit `{state['commit']}`; run `{state['run_id']}`. TEST UTC [{state['test_start']}, {state['test_end']}); independently trimmed source end {state['trimmed_end_unfloored']}, floored to the hour. Target windows beyond this end are excluded per lead. TRAIN T ends exclusively at {state['train_end']} (25-hour embargo). HGB retains the frozen inner tails and pre-calibration refit; fitted details are in final_test_metrics.csv.",'','VERIFIED: single prediction per lead; no TEST tuning or settings changes. Lead 0 is separate; 1–6 primary; 12/24 secondary. Seven-day paired circular UTC blocks, seed 42, 300 draws. All regions share sampled days. Flags come from FINAL TRAIN, not TEST. Luhanska, Crimea and Sevastopol excluded.','', '## Pooled TEST metrics and 95% CIs','']
    for _,row in pooled.iterrows():
        text=f"VERIFIED: lead {int(row.lead)}; n={int(row.n)}; Brier={row.brier:.5f}; ECE={row.ece:.5f}. "
        for ref,col in [('clim','bss_vs_clim'),('persistence','bss_vs_persistence'),('ses','bss_vs_ses')]:
            limits=ci.loc[ci.lead.eq(row.lead)&ci.scope.eq('ALL')&ci.reference.eq(ref)].iloc[0]
            text+=f"BSS vs {ref}={row[col]:.5f} [{limits.low:.5f}, {limits.high:.5f}]. "
        lines.extend([text,''])
    columns=['lead','brier','validation_brier','ece','validation_ece','bss_vs_clim','validation_bss_clim','bss_vs_persistence','validation_bss_persistence','bss_vs_ses','validation_bss_ses']
    lines.extend(['## Validation side-by-side','','```text',pooled[columns].to_string(index=False,float_format=lambda x:f'{x:.5f}'),'```',''])
    for _,row in pooled.iterrows():
        worse=[]
        if row.brier>row.validation_brier:worse.append('Brier')
        if row.ece>row.validation_ece:worse.append('ECE')
        for col,label in [('clim','BSS vs climatology'),('persistence','BSS vs persistence'),('ses','BSS vs SES')]:
            if row['bss_vs_'+('clim' if col=='clim' else col)]<row['validation_bss_'+col]:worse.append(label)
        lines.append(f"VERIFIED: lead {int(row.lead)} TEST is worse on {', '.join(worse) if worse else 'none of these point metrics'}. Different periods/base rates mean this is descriptive, not a paired significance test.")
    lines.extend(['','## Per-oblast TEST table','','```text',reg.to_string(index=False,float_format=lambda x:f'{x:.5f}'),'```','',
                  'VERIFIED: ALL_excl_flagged metrics and per-region CIs are in the CSVs. Existing artificial-close, prior exploratory TEST overlap, definition-break and incomplete-adjacency limitations remain. No re-tuning after TEST.'])
    REPORT.write_text('\n'.join(lines)+'\n')
    print(pooled[['lead','bss_vs_clim','bss_vs_persistence','bss_vs_ses','ece']].to_string(index=False),flush=True)
