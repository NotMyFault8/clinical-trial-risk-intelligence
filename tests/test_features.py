import numpy as np
import pandas as pd
import pytest
from clinical_trial_risk.features.build import age_years,build_features
from clinical_trial_risk.models.train import partition

def test_age_units_and_absence():
    assert age_years('18 Months')==1.5
    assert np.isnan(age_years('N/A'))

def test_future_columns_rejected():
    with pytest.raises(ValueError,match='Post-outcome'):
        build_features(pd.DataFrame({'overall_status':['Terminated']}))

def test_partition_is_stable():
    assert partition('sponsor a')==partition('sponsor a')
