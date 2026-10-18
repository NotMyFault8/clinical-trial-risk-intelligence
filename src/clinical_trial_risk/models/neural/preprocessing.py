"""Train-only preprocessing with an explicit baseline feature allowlist."""
from collections import Counter
import re
import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from clinical_trial_risk.features.build import NUMERIC, CATEGORICAL


def tokens(text):
    return re.findall(r"\w+|[^\w\s]", str(text).lower())


class Preprocessor:
    def __init__(self, max_length=256, max_vocab=12000):
        if max_length < 2 or max_vocab < 3:
            raise ValueError('Token limits must leave room for special tokens')
        self.max_length, self.max_vocab = max_length, max_vocab

    def fit(self, frame):
        counts = Counter(t for text in frame.eligibility_text.fillna('') for t in tokens(text))
        # PAD=0, UNK=1, CLS=2. Stable frequency/lexical tie-breaking.
        ordered = sorted(counts, key=lambda t: (-counts[t], t))[:self.max_vocab-3]
        self.vocabulary = {t: i+3 for i, t in enumerate(ordered)}
        self.structured = ColumnTransformer([
            ('numeric', make_pipeline(SimpleImputer(strategy='median', add_indicator=True,
                keep_empty_features=True), StandardScaler()), NUMERIC),
            ('category', OneHotEncoder(handle_unknown='ignore', sparse_output=False), CATEGORICAL),
        ], sparse_threshold=0)
        self.structured.fit(frame)
        return self

    def transform(self, frame):
        ids = np.zeros((len(frame), self.max_length), dtype=np.int64)
        ids[:, 0] = 2  # Guarantees a valid attention key even for empty text.
        for row, text in enumerate(frame.eligibility_text.fillna('')):
            sequence = [self.vocabulary.get(t, 1) for t in tokens(text)[:self.max_length-1]]
            ids[row, 1:1+len(sequence)] = sequence
        structured = self.structured.transform(frame).astype(np.float32)
        if not np.isfinite(structured).all():
            raise ValueError('Non-finite structured features')
        return ids, structured

    def text_audit(self, frame):
        sequences = [tokens(t) for t in frame.eligibility_text.fillna('')]
        total = sum(map(len, sequences))
        return {'records': len(frame), 'empty': sum(not s for s in sequences),
                'truncated': sum(len(s) > self.max_length-1 for s in sequences),
                'unknown_token_fraction': sum(t not in self.vocabulary for s in sequences for t in s)/max(1,total)}
