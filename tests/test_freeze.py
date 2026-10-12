import numpy as np
import pandas as pd
import pytest

from airalerts.freeze import descriptor, ensemble_probability, validate_predictions


def test_ensemble_fixed_grid_and_config_no_fold_coefficients():
    a=np.array([.1,.9]);b=np.array([.3,.7])
    np.testing.assert_allclose(ensemble_probability(a,b,.25),[.25,.75])
    with pytest.raises(ValueError): ensemble_probability(a,b,.6)
    params={'features':['active_now'],'half_life':14,'learning_rate':.05,'max_depth':3,'max_iter':300,
            'fold_iterations':{'1':40},'fold_calibration_coefficients':{'1':{'slope':2.}}}
    base=descriptor('hgb_platt',params)
    assert base['hyperparameters']['calibration']['method']=='Platt'
    assert 'fold_iterations' not in base['hyperparameters']
    assert 'fold_calibration_coefficients' not in base['hyperparameters']
    ensemble=descriptor('ens_ses_hgb_platt',{'base_model':'hgb_platt','base_params':params,'weight_learned':.75})
    assert ensemble['ensemble_weight']==.75
    assert ensemble['half_life']==14
    assert ensemble['hyperparameters']['base_model']['features']==['active_now']


def test_comparison_guard():
    pred=pd.DataFrame({'oblast':['A'],'T':pd.to_datetime(['2026-07-31 23:00'],utc=True),'fold_id':['4']})
    validate_predictions(pred,0)
    with pytest.raises(ValueError,match='guarded VALID'): validate_predictions(pred,1)
    pred['T']=pd.to_datetime(['2026-08-01'],utc=True)
    with pytest.raises(ValueError): validate_predictions(pred,0)
