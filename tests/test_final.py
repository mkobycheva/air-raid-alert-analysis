import copy
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from airalerts.final import assert_frozen, train_mask, predict_frozen
from airalerts.features import observed_features
from airalerts.panel import build_panel


def test_log_reader_handles_mixed_folds_across_csv_chunks(tmp_path):
    from airalerts.evaluate import RESULT_COLUMNS
    from airalerts.final import read_log_keys
    import csv
    path=tmp_path/'results.csv'
    def row(fold):
        values={'run_id':'synthetic','model':'climatology','lead':'1','scope':'ALL','fold_id':fold}
        return [values.get(column,'') for column in RESULT_COLUMNS]
    with path.open('w',newline='') as stream:
        writer=csv.writer(stream);writer.writerow(RESULT_COLUMNS)
        writer.writerows([row('1')]*65536)
        writer.writerow(row('pooled'));writer.writerow(row('test'))
    actual=read_log_keys(path)
    assert len(actual)==65538
    assert actual.fold_id.iloc[0]=='1'
    assert actual.fold_id.iloc[-2:].tolist()==['pooled','test']


def test_frozen_contract_and_final_embargo():
    cfg=json.loads(Path('config/final_config.json').read_text())
    assert_frozen(cfg)
    changed=copy.deepcopy(cfg)
    changed['models']['24']['hyperparameters']['base_model']['hyperparameters']['calibration']['method']='Platt'
    with pytest.raises(ValueError):assert_frozen(changed)
    ts=pd.date_range('2026-07-01','2026-08-02',freq='h',inclusive='left',tz='UTC')
    frame=pd.DataFrame({'T':ts})
    for k in (0,1,2,3,4,5,6,12,24):
        frame[f'y_{k}']=True
        mask=train_mask(frame,pd.Timestamp('2025-12-01',tz='UTC'),pd.Timestamp('2026-08-01',tz='UTC'),25,k)
        assert frame.loc[mask,'T'].max()<pd.Timestamp('2026-08-01',tz='UTC')-pd.Timedelta(hours=25)
        assert (frame.loc[mask,'T']+pd.Timedelta(hours=k+1)).max()<=pd.Timestamp('2026-08-01',tz='UTC')


def test_final_feature_optin_and_future_perturbation():
    events=pd.DataFrame([('A','raion','2026-08-01 01:10','2026-08-02 03:00'),('B','raion','2026-08-02 01:00','2026-08-03 01:00')],columns=['oblast','level','started_at','finished_at'])
    for column in ['started_at','finished_at']:events[column]=pd.to_datetime(events[column],utc=True)
    panel=build_panel(events,'2026-08-01','2026-08-03',leads=(0,),day_windows=(),week_windows=(),alphas=(),oblasts=['A','B'])
    neighbors={'A':('B',),'B':('A',)}
    with pytest.raises(ValueError,match='reserved TEST'):observed_features(events,panel,neighbors)
    t=pd.Timestamp('2026-08-01 12:00',tz='UTC')
    actual=observed_features(events,panel,neighbors,include_long_memory=True,final_test=True)
    altered=events.loc[events.started_at.le(t)].copy();altered.loc[altered.finished_at.gt(t),'finished_at']=pd.NaT
    expected=observed_features(altered,panel,neighbors,include_long_memory=True,final_test=True)
    pd.testing.assert_frame_equal(actual.loc[actual['T'].eq(t)].reset_index(drop=True),expected.loc[expected['T'].eq(t)].reset_index(drop=True))


def test_frozen_hgb_uses_one_cap_and_predicts_once(monkeypatch):
    import airalerts.final as module
    cfg=json.loads(Path('config/final_config.json').read_text())
    called={}
    def choose(core,stop,columns,lr,depth,half,end,seed,caps):
        called['caps']=caps
        return {caps[0]:10},[{'iteration':10,'stop_brier':.2}]
    def fit(train,cal,rows,columns,lr,depth,n,half,end,seed):
        called['predictions']=called.get('predictions',0)+1
        return np.array([.2,.8]),np.array([.5])
    monkeypatch.setattr(module,'select_iterations',choose);monkeypatch.setattr(module,'refit',fit)
    monkeypatch.setattr(module,'chronological_tails',lambda *args,**kwargs:{'core':args[0],'stop':args[0],'fit':args[0],'cal':args[0]})
    train=pd.DataFrame({'T':pd.to_datetime(['2026-07-01'],utc=True)})
    p,fitted=predict_frozen(cfg['models']['24'],train,pd.DataFrame(index=[0,1]),24,pd.Timestamp('2026-07-30 23:00',tz='UTC'),42,np.array([.4,.6]))
    np.testing.assert_allclose(p,[.3,.7])
    assert called=={'caps':(300,),'predictions':1}
    assert fitted['iterations']==10 and fitted['ensemble_weight']==.5
