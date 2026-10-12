import numpy as np
import pandas as pd
import pytest

from airalerts.hgb import chronological_tails, rates_from_fit, select_iterations, Platt
from airalerts.pooled import recency_weights


def test_inner_tails_are_chronological_and_embargoed():
    times = pd.date_range('2026-01-01','2026-03-01',freq='h',inclusive='left',tz='UTC')
    train = pd.DataFrame({'oblast':'A','T':times,'y_0':np.arange(len(times))%2,'y':np.arange(len(times))%2})
    end = pd.Timestamp('2026-03-01',tz='UTC')
    for k in (0,1,6,12,24):
        tails = chronological_tails(train,end,k)
        assert (tails['core']['T']+pd.Timedelta(hours=k+1)).max() <= tails['stop']['T'].min()
        assert (tails['fit']['T']+pd.Timedelta(hours=k+1)).max() <= tails['cal']['T'].min()
        assert tails['cal']['T'].max() < end
    changed = train.copy();changed['y_0']=1
    core,valid = rates_from_fit(tails['core'],changed)
    assert valid.base_rate.eq(tails['core'].y_0.mean()).all()


def test_hgb_stopping_and_train_only_platt():
    pytest.importorskip('sklearn',reason='Offline sklearn model tests run with Python 3.12')
    rng=np.random.default_rng(42)
    times=pd.date_range('2026-01-01',periods=240,freq='h',tz='UTC')
    x=rng.random(240);y=(x>.5).astype(float)
    data=pd.DataFrame({'oblast':'A','T':times,'active_now':x,'y_0':y,'y':y})
    core,stop=data.iloc[:160],data.iloc[185:]
    end=times[-1]+pd.Timedelta(hours=1)
    chosen,history=select_iterations(core,stop,('active_now',),.1,3,np.inf,end,42,caps=(10,20))
    assert chosen[10]<=10 and chosen[20]<=20
    assert len(history)==2
    p=np.clip(.2+.6*x,.01,.99)
    platt=Platt().fit(p[:160],y[:160],recency_weights(core,end,np.inf))
    fitted=platt.model.coef_.copy()
    actual=platt.predict(p[160:])
    assert np.all((actual>=0)&(actual<=1))
    np.testing.assert_array_equal(fitted,platt.model.coef_)
