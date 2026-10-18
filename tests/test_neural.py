"""Synthetic engineering checks, never evidence of clinical predictive value."""
import importlib.util
import joblib
import numpy as np
import pandas as pd
import pytest
from clinical_trial_risk.features.build import NUMERIC, CATEGORICAL
from clinical_trial_risk.models.neural.preprocessing import Preprocessor


def fixture_data():
    rows = []
    for split, year, n in [('train',2018,24), ('tune',2020,8), ('calibrate',2020,8), ('test',2021,8)]:
        for i in range(n):
            row = {c: float(i%4) for c in NUMERIC}
            row.update({c: 'a' if i%2 else 'b' for c in CATEGORICAL})
            row.update(nct_id=f'{split}-{i}', year=year, split=split, sponsor_cluster=f'{split}-{i//2}',
                       label=i%2, eligibility_text=('prior therapy required' if i%2 else 'healthy volunteers'))
            rows.append(row)
    return pd.DataFrame(rows)


def test_train_only_vocabulary_and_feature_allowlist():
    data = fixture_data()
    prep = Preprocessor(8,100).fit(data[data.split == 'train'])
    before = prep.transform(data)
    modified = data.copy()
    modified['label'] = 1-modified.label
    modified['why_stopped'] = 'outcome leaked'
    after = prep.transform(modified)
    for a,b in zip(before, after):
        np.testing.assert_array_equal(a,b)
    modified['eligibility_text'] = 'never_seen_word'
    assert (prep.transform(modified)[0][:,1] == 1).all()
    modified['eligibility_text'] = ''
    assert (prep.transform(modified)[0][:,0] == 2).all()
    assert (prep.transform(modified)[0][:,1:] == 0).all()


def test_split_guards():
    from clinical_trial_risk.models.neural.experiment import validate_splits
    data = fixture_data()
    validate_splits(data)
    broken = data.copy()
    broken.loc[broken.split == 'test','year'] = 2019
    with pytest.raises(ValueError, match='temporal'):
        validate_splits(broken)
    broken = data.copy()
    broken.loc[broken.split == 'calibrate','sponsor_cluster'] = 'tune-0'
    with pytest.raises(ValueError, match='overlap'):
        validate_splits(broken)
    broken = data.copy()
    broken.loc[broken.index[-1], 'nct_id'] = data.nct_id.iloc[0]
    with pytest.raises(ValueError, match='unique'):
        validate_splits(broken)


@pytest.mark.parametrize('backend',['torch','tensorflow'])
def test_training_padding_and_serialization(backend, tmp_path):
    if importlib.util.find_spec(backend) is None:
        pytest.skip(f'Install neural-{backend} extra')
    from clinical_trial_risk.models.neural.experiment import fit
    from clinical_trial_risk.models.train import probability
    data = fixture_data()
    config = {'seed':731,'max_length':8,'max_vocab':100,
              'architecture':{'width':8,'heads':2,'dropout':0.0},
              'training':{'epochs':3,'batch_size':8,'learning_rate':0.01,'patience':3}}
    bundle, summary = fit(data, backend, config)
    assert len(summary['history']) >= 2
    assert np.isfinite([h['train_bce'] for h in summary['history']]).all()
    model = bundle['estimator']
    test = data[data.split == 'test']
    p = probability(bundle,test)
    assert np.isfinite(p).all() and ((p>=0)&(p<=1)).all()
    path = tmp_path/'model.joblib'
    joblib.dump(bundle,path)
    restored = joblib.load(path)
    np.testing.assert_allclose(probability(restored,test),p,atol=1e-6)
    # Changing future labels/text must not change fitted weights/calibration.
    altered = data.copy()
    altered.loc[altered.split == 'test','label'] = 1-altered.loc[altered.split == 'test','label']
    altered.loc[altered.split == 'test','eligibility_text'] = 'future secret'
    other, _ = fit(altered, backend, config)
    np.testing.assert_allclose(probability(other,test),p,atol=1e-6)
    ids,s = model.preprocessor.transform(test.iloc[:2])
    if backend == 'torch':
        import torch
        model._network.eval()
        with torch.no_grad():
            full = model._network(torch.as_tensor(ids), torch.as_tensor(s)).numpy()
            short = model._network(torch.as_tensor(ids[:,:4]), torch.as_tensor(s)).numpy()
    else:
        full = model._network((ids,s),training=False).numpy()
        short = model._network((ids[:,:4],s),training=False).numpy()
    np.testing.assert_allclose(full,short,atol=1e-5)
    blank = test.copy()
    blank['eligibility_text'] = ''
    assert np.isfinite(model.predict_proba(blank)).all()


def test_comparative_command_roundtrip(tmp_path, monkeypatch):
    """Exercise train -> freeze -> compare -> overwrite guard without AACT data."""
    if any(importlib.util.find_spec(b) is None for b in ['torch','tensorflow']):
        pytest.skip('Full comparison needs both optional frameworks')
    import json
    import sys
    from clinical_trial_risk.models.neural import experiment
    from clinical_trial_risk.models import train
    data = fixture_data()
    data['snapshot_date'] = data.year.astype(str)+'-09-01'
    config = {'seed':731,'max_length':8,'max_vocab':100,
              'architecture':{'width':8,'heads':2,'dropout':0.0},
              'training':{'epochs':2,'batch_size':8,'learning_rate':0.01,'patience':2},
              'bootstrap_replicates':20,'interpretation':'Synthetic engineering fixture only'}
    for name in experiment.INPUTS+experiment.CODE:
        path = tmp_path/name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('synthetic fixture')
    (tmp_path/'configs/neural_protocol.json').write_text(json.dumps(config))
    (tmp_path/'configs/analysis_protocol.json').write_text(json.dumps({'logistic_C':[1.0]}))
    monkeypatch.setattr(experiment,'ROOT',tmp_path)
    monkeypatch.setattr(train,'ROOT',tmp_path)
    monkeypatch.setattr(experiment,'load_data',lambda: data)
    for backend in ['torch','tensorflow']:
        monkeypatch.setattr(sys,'argv',['experiment','train','--backend',backend])
        experiment.main()
    monkeypatch.setattr(sys,'argv',['experiment','evaluate'])
    experiment.main()
    report = json.loads((tmp_path/'artifacts/neural/neural-v1/evaluation.json').read_text())
    assert set(report['models']) == {'torch','tensorflow','structured_logistic','structured_tfidf'}
    assert report['automatic_promotion'] is False
    assert not (tmp_path/'artifacts/model_registry.json').exists()
    with pytest.raises(FileExistsError,match='already exists'):
        experiment.main()
