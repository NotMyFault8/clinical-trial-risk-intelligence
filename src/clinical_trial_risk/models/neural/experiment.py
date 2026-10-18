"""Versioned extension of the existing retrospective temporal experiment."""
import argparse
import importlib.metadata
import json
from pathlib import Path
import platform
import time
import joblib
import numpy as np
from scipy.special import logit
from sklearn.linear_model import LogisticRegression
from sklearn.isotonic import IsotonicRegression
from clinical_trial_risk.data.cohort import ROOT, digest
from clinical_trial_risk.models.train import load_data, probability, fit_family
from clinical_trial_risk.evaluation.prediction import metrics, cluster_intervals
from .preprocessing import Preprocessor
from .backends import NeuralEstimator

INPUTS = ['data/processed/baseline_features.parquet', 'data/processed/cohort_metadata.parquet',
          'data/processed/outcomes.parquet', 'configs/analysis_protocol.json', 'configs/neural_protocol.json']
CODE = ['src/clinical_trial_risk/models/train.py', 'src/clinical_trial_risk/features/build.py',
        'src/clinical_trial_risk/data/cohort.py', 'src/clinical_trial_risk/evaluation/prediction.py']
CODE += [str(p.relative_to(ROOT)) for p in sorted((ROOT/'src/clinical_trial_risk/models/neural').glob('*.py'))]


def fingerprints():
    return {name: digest(ROOT/name) for name in INPUTS+CODE}


def validate_splits(data):
    if data.nct_id.isna().any() or data.nct_id.duplicated().any():
        raise ValueError('Trial IDs must be present and unique across splits')
    if set(data.split) != {'train', 'tune', 'calibrate', 'test'}:
        raise ValueError('Expected four temporal partitions')
    for split in ['train', 'tune', 'calibrate', 'test']:
        frame = data[data.split == split]
        if set(frame.label) != {0, 1}:
            raise ValueError(f'{split}: binary classes required')
        years = set(frame.year)
        expected = {'train': {2018, 2019}, 'tune': {2020}, 'calibrate': {2020}, 'test': {2021}}[split]
        if not years <= expected:
            raise ValueError(f'{split}: unexpected temporal assignment')
    tune = data[data.split == 'tune']
    calibrate = data[data.split == 'calibrate']
    if set(tune.sponsor_cluster) & set(calibrate.sponsor_cluster):
        raise ValueError('Calibration and tuning sponsors overlap')


def fit(data, backend, config):
    validate_splits(data)
    train, tune, calibrate = [data[data.split == s] for s in ['train', 'tune', 'calibrate']]
    prep = Preprocessor(config['max_length'], config['max_vocab']).fit(train)
    model = NeuralEstimator(backend, prep, seed=config['seed'], **config['architecture'])
    model.initialize(prep.transform(train)[1].shape[1])
    start = time.perf_counter()
    history = model.fit_epochs(train, tune, **config['training'])
    p = model.predict_proba(calibrate)[:, 1]
    platt = LogisticRegression(C=1e6, max_iter=1000).fit(
        logit(np.clip(p, 1e-7, 1-1e-7)).reshape(-1, 1), calibrate.label.astype(int))
    iso = IsotonicRegression(out_of_bounds='clip').fit(p, calibrate.label)
    bundle = {'estimator': model, 'platt': platt, 'isotonic': iso,
              'family': f'{backend}_transformer', 'training_ids': train.nct_id.tolist(),
              'tuning_ids': tune.nct_id.tolist(), 'calibration_ids': calibrate.nct_id.tolist()}
    summary = {'backend': backend, 'best_epoch': model.best_epoch, 'history': history,
               'chosen_tuning_AP': max(h['tuning_AP'] for h in history),
               'seconds': time.perf_counter()-start,
               'text_audit': {s: prep.text_audit(data[data.split == s]) for s in ['train','tune','calibrate']},
               'environment': {'python': platform.python_version(), backend: importlib.metadata.version(backend)},
               'config': config, 'calibration': 'Platt on separate calibration sponsors',
               'interpretation': 'Supervised small Transformer; no pretrained LLM or LLM fine-tuning'}
    return bundle, summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['train', 'evaluate'])
    parser.add_argument('--backend', choices=['torch', 'tensorflow'], default='torch')
    parser.add_argument('--run', default='neural-v1')
    args = parser.parse_args()
    if not args.run or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_' for c in args.run):
        parser.error('--run must be a simple run name')
    output = ROOT/'artifacts/neural'/args.run
    config = json.loads((ROOT/'configs/neural_protocol.json').read_text())
    data = load_data()
    validate_splits(data)
    if args.action == 'train':
        target = output/args.backend
        target.mkdir(parents=True, exist_ok=False)
        manifest = fingerprints()
        bundle, summary = fit(data, args.backend, config)
        bundle['input_and_code_sha256'] = manifest
        joblib.dump(bundle, target/'model.joblib')
        summary['model_sha256'] = digest(target/'model.joblib')
        summary['input_and_code_sha256'] = manifest
        (target/'training.json').write_text(json.dumps(summary, indent=2, allow_nan=False)+'\n')
        # Save the complete installed environment with each real run.
        packages = {d.metadata['Name']: d.version for d in importlib.metadata.distributions() if d.metadata['Name']}
        (target/'environment.json').write_text(json.dumps(packages, indent=2, sort_keys=True)+'\n')
        print(target/'training.json')
        return
    # Both frameworks must be frozen before this comparative evaluation.
    result_path = output/'evaluation.json'
    if result_path.exists():
        raise FileExistsError('Evaluation already exists; do not overwrite frozen evidence')
    bundles, summaries = {}, {}
    for backend in ['torch', 'tensorflow']:
        target = output/backend
        summary = json.loads((target/'training.json').read_text())
        if summary['model_sha256'] != digest(target/'model.joblib'):
            raise ValueError('Model artifact changed')
        if summary['input_and_code_sha256'] != fingerprints():
            raise ValueError('Input, protocol or code changed since training')
        bundles[backend] = joblib.load(target/'model.joblib')
        summaries[backend] = summary
    # Refit existing baselines using their original train/tune/calibration protocol.
    # Separate output avoids replacing the original research artifacts.
    variant = f'neural-{args.run}'
    if (ROOT/'artifacts/models'/variant).exists():
        raise FileExistsError('Baseline extension artifacts already exist; inspect interrupted run')
    protocol = json.loads((ROOT/'configs/analysis_protocol.json').read_text())
    for family in ['structured_logistic', 'structured_tfidf']:
        fit_family(data, family, protocol, variant)
        bundles[family] = joblib.load(ROOT/'artifacts/models'/variant/(family+'.joblib'))
    test = data[data.split == 'test'].copy()
    predictions, results = {}, {}
    for name, bundle in bundles.items():
        used = bundle['training_ids']+bundle['calibration_ids']+bundle.get('tuning_ids', [])
        if set(used) & set(test.nct_id):
            raise ValueError('Holdout contamination')
        predictions[name] = probability(bundle, test)
        results[name] = {mode: metrics(test.label, probability(bundle, test, mode)) for mode in ['raw', 'platt']}
    report = {'models': results, 'neural_training': summaries,
              'input_and_code_sha256': fingerprints(),
              'uncertainty': cluster_intervals(test.label.to_numpy(dtype=int), predictions,
                  test.sponsor_cluster.to_numpy(), reps=config['bootstrap_replicates']),
              'interpretation': config['interpretation'], 'automatic_promotion': False}
    for name, p in predictions.items():
        test[name] = p
    test[['nct_id', 'snapshot_date', 'label', 'sponsor_cluster']+list(predictions)].to_parquet(output/'predictions.parquet', index=False)
    with result_path.open('x') as f:
        f.write(json.dumps(report, indent=2, allow_nan=False)+'\n')
    print(result_path)


if __name__ == '__main__':
    main()
