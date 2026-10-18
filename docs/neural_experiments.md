# PyTorch and TensorFlow Transformer extension

## Implemented scope

Two native, trainable text/structured fusion classifiers extend the existing
logistic, boosting, TF-IDF, frozen-embedding and LLM-feature experiments.
PyTorch uses `TransformerEncoder`; TensorFlow/Keras uses `MultiHeadAttention`
with residual connections, layer normalization and a feed-forward block.
Both use learned token/position embeddings, masked mean pooling and a binary
fusion head. They are small supervised encoders trained from scratch, **not
pretrained LLMs and not LLM fine-tuning**. Existing LLM extraction remains a
separately evaluated component with its existing release gate.

Research question: does a trainable contextual text representation improve
conditional resolved-outcome discrimination beyond structured logistic and
TF-IDF baselines? With only 1,107 training records in the saved primary cohort,
overfitting and negative incremental value are plausible. Adding frameworks is
an engineering capability, not evidence of better prediction.

## Reproduction

Python 3.12 is recommended. `requirements-neural-macos.lock` records the tested
macOS arm64 environment; it is separate from the core/Linux locks. The core application does not require either extra.
Install the relevant optional dependencies (or both to run the complete comparison):

```sh
python -m venv .venv
.venv/bin/python -m pip install -e '.[test,neural-torch,neural-tensorflow]'
.venv/bin/python -m pytest tests/test_neural.py -q
.venv/bin/python -m clinical_trial_risk.models.neural.experiment train --backend torch --run neural-v1
.venv/bin/python -m clinical_trial_risk.models.neural.experiment train --backend tensorflow --run neural-v1
.venv/bin/python -m clinical_trial_risk.models.neural.experiment evaluate --run neural-v1
```

Training requires the existing verified `data/processed/baseline_features.parquet`,
`cohort_metadata.parquet` and `outcomes.parquet`; reproduce them using the existing
source runbook. Tests use synthetic fixtures and need no AACT download.
`load_data` is reused, so cohort rules, feature construction and sponsor-based
2020 partitioning match the existing experiment. Extra embedding/LLM columns,
when present, are ignored by the explicit neural feature allowlist.

Each backend saves a joblib bundle, training history, environment inventory and
input/code fingerprints under `artifacts/neural/<run>/<backend>/`. Numeric
weights reconstruct native modules on loading. Use trusted joblib files only.
The experiment is CPU-oriented and bounded to a small model; it does not claim
distributed training, GPU acceleration, mixed precision or production serving.

Evaluation requires both frozen backend artifacts, verifies their hashes, refits
the two existing baselines under a separate variant, and saves comparative raw
and Platt-calibrated metrics, sponsor-cluster intervals and trial predictions in
the run directory. Existing reports, fitted baseline artifacts and API registry
are not overwritten. Existing-output guards reject accidental reruns. For an
interrupted run, inspect and preserve partial artifacts before selecting a new
run name; new names do not make repeated holdout inspection statistically valid.

## Controls and comparison limits

- Fit vocabulary, imputation, scaling and categorical levels on training only.
- Reserve PAD/UNK/CLS tokens; CLS provides a valid attention key for empty text.
- Mask padding in attention and pooling. Record empty text, truncation and OOV
  fractions. Long protocols are truncated to 255 tokens plus CLS; this can omit
  clinically relevant exclusions and is a documented limitation.
- Use training BCE, Adam and gradient clipping. Select checkpoints by tuning AP
  with fixed epoch/patience limits; fit Platt calibration on separate sponsors.
- Frameworks share architecture and training budgets, not identical kernels,
  initial weights or numeric outputs. One seed is an engineering starting point;
  seed sensitivity requires a prospectively specified follow-up protocol.
- Report AP, ROC-AUC, Brier, calibration bins, threshold metrics and top-K metrics
  using the existing evaluator; compute paired sponsor-cluster differences from
  structured logistic. These exploratory intervals are not multiplicity-adjusted
  confirmatory claims and condition on fitted models.
- The 2021 holdout was already examined in the original project. This extension
  is exploratory. An untouched future cohort is required for confirmation.
- Historical training-label maturity and resolved-outcome selection limitations
  still apply. There is no prospective clinical or operational validation.
- Do not promote a neural model to the API based on this extension automatically.
  The existing local evidence-report path and its release policy remain intact.

## Verification boundary

`tests/test_neural.py` checks training in each installed framework, finite empty
text inference, padding invariance, serialization/calibration round trips,
train-only vocabulary, future-label/text isolation and split rejection. Framework
extras are optional, so CI has a dedicated backend matrix to exercise both.
Real-data comparative metrics must come from the above commands; synthetic
checks must never be presented as clinical results.

## References

- [PyTorch TransformerEncoderLayer](https://docs.pytorch.org/docs/stable/generated/torch.nn.TransformerEncoderLayer.html)
- [TensorFlow MultiHeadAttention](https://www.tensorflow.org/api_docs/python/tf/keras/layers/MultiHeadAttention)

PyTorch key-padding masks mark ignored keys with True; Keras attention masks mark
permitted attention with True. The implementation applies the appropriate convention.
