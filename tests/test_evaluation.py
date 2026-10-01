import numpy as np
from clinical_trial_risk.evaluation.prediction import metrics,cluster_intervals

def test_perfect_ranking_and_probability_metrics():
    m=metrics([0,0,1,1],[.1,.2,.8,.9])
    assert m['roc_auc']==1 and m['average_precision']==1 and m['balanced_accuracy']==1
    assert np.isclose(m['brier'],.025)
    assert m['top_k']['0.2']['captured']==1

def test_cluster_bootstrap_is_paired_for_identical_predictions():
    y=np.array([0,1,0,1,0,1]);p=np.array([.2,.8,.3,.7,.4,.6])
    x=cluster_intervals(y,{'structured_logistic':p,'copy':p},np.array(['a','a','b','b','c','c']),reps=30)
    assert x['differences_from_structured_logistic']['copy']['average_precision']['ci95']==[0.,0.]
