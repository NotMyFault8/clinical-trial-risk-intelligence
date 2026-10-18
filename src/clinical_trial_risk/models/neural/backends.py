"""Native PyTorch and Keras implementations of a small fusion Transformer.

Same architecture and budget; initialization and kernels are framework-specific.
These are supervised encoders initialized from scratch, not pretrained LLMs.
"""
import numpy as np


def build_torch(vocab, structured_dim, length, width=32, heads=4, dropout=0.1):
    import torch
    from torch import nn

    class FusionTransformer(nn.Module):
        def __init__(self):
            super().__init__()
            self.token = nn.Embedding(vocab, width, padding_idx=0)
            self.position = nn.Embedding(length, width)
            layer = nn.TransformerEncoderLayer(width, heads, width*2, dropout,
                activation='gelu', batch_first=True, layer_norm_eps=1e-6)
            self.encoder = nn.TransformerEncoder(layer, 1, enable_nested_tensor=False)
            self.head = nn.Sequential(nn.Linear(width+structured_dim, 32), nn.ReLU(),
                                      nn.Dropout(dropout), nn.Linear(32, 1))

        def forward(self, ids, structured):
            valid = ids != 0
            h = self.token(ids) + self.position(torch.arange(ids.shape[1], device=ids.device))
            h = self.encoder(h, src_key_padding_mask=~valid)
            pooled = (h*valid.unsqueeze(-1)).sum(1)/valid.sum(1, keepdim=True)
            return self.head(torch.cat([pooled, structured], dim=1)).squeeze(-1)

    return FusionTransformer()


def build_tensorflow(vocab, structured_dim, length, width=32, heads=4, dropout=0.1):
    import tensorflow as tf
    layers = tf.keras.layers

    class FusionTransformer(tf.keras.Model):
        def __init__(self):
            super().__init__()
            self.token = layers.Embedding(vocab, width)
            self.position = layers.Embedding(length, width)
            self.attention = layers.MultiHeadAttention(heads, width//heads, dropout=dropout)
            self.drop1, self.drop2 = layers.Dropout(dropout), layers.Dropout(dropout)
            self.norm1, self.norm2 = layers.LayerNormalization(epsilon=1e-6), layers.LayerNormalization(epsilon=1e-6)
            self.ff = tf.keras.Sequential([layers.Dense(width*2, activation=tf.nn.gelu),
                                          layers.Dropout(dropout), layers.Dense(width)])
            self.head = tf.keras.Sequential([layers.Dense(32, activation='relu'),
                                            layers.Dropout(dropout), layers.Dense(1)])

        def call(self, inputs, training=False):
            ids, structured = inputs
            valid = tf.not_equal(ids, 0)
            h = self.token(ids) + self.position(tf.range(tf.shape(ids)[1]))
            # Keras True means permitted; PyTorch padding-mask True means ignored.
            a = self.attention(h, h, attention_mask=valid[:, None, :], training=training)
            h = self.norm1(h+self.drop1(a, training=training))
            h = self.norm2(h+self.drop2(self.ff(h, training=training), training=training))
            mask = tf.cast(valid[:, :, None], h.dtype)
            pooled = tf.reduce_sum(h*mask, 1)/tf.reduce_sum(mask, 1)
            return tf.squeeze(self.head(tf.concat([pooled, structured], 1), training=training), -1)

    model = FusionTransformer()
    model((np.full((1, length), 2, np.int64), np.zeros((1, structured_dim), np.float32)))
    return model


class NeuralEstimator:
    """Portable joblib adapter: serialize numeric weights, rebuild native modules.

    Only load artifacts from trusted sources (joblib uses pickle).
    """
    def __init__(self, backend, preprocessor, seed=731, width=32, heads=4, dropout=0.1):
        if backend not in {'torch', 'tensorflow'} or width % heads:
            raise ValueError('Unsupported backend or incompatible attention dimensions')
        self.backend, self.preprocessor, self.seed = backend, preprocessor, seed
        self.options = dict(width=width, heads=heads, dropout=dropout)

    def initialize(self, structured_dim):
        self.dim = structured_dim
        if self.backend == 'torch':
            import torch
            torch.manual_seed(self.seed)
            torch.set_num_threads(1)
        else:
            import tensorflow as tf
            tf.keras.utils.set_random_seed(self.seed)
            tf.config.experimental.enable_op_determinism()
        self._network = self._build()
        return self

    def _build(self):
        factory = build_torch if self.backend == 'torch' else build_tensorflow
        return factory(len(self.preprocessor.vocabulary)+3, self.dim,
                       self.preprocessor.max_length, **self.options)

    def get_weights(self):
        if self.backend == 'torch':
            return {k: v.detach().cpu().numpy().copy() for k,v in self._network.state_dict().items()}
        return self._network.get_weights()

    def set_weights(self, weights):
        if self.backend == 'torch':
            import torch
            self._network.load_state_dict({k: torch.as_tensor(v) for k,v in weights.items()})
        else:
            self._network.set_weights(weights)

    def __getstate__(self):
        state = self.__dict__.copy()
        state['weights'] = self.get_weights()
        state.pop('_network')
        return state

    def __setstate__(self, state):
        weights = state.pop('weights')
        self.__dict__.update(state)
        self._network = self._build()
        self.set_weights(weights)

    def predict_proba(self, frame):
        ids, structured = self.preprocessor.transform(frame)
        outputs = []
        for start in range(0, len(ids), 64):
            x, s = ids[start:start+64], structured[start:start+64]
            if self.backend == 'torch':
                import torch
                self._network.eval()
                with torch.no_grad():
                    p = torch.sigmoid(self._network(torch.as_tensor(x), torch.as_tensor(s))).numpy()
            else:
                import tensorflow as tf
                p = tf.sigmoid(self._network((x, s), training=False)).numpy()
            outputs.append(p)
        p = np.concatenate(outputs) if outputs else np.empty(0)
        return np.column_stack([1-p, p])

    def fit_epochs(self, train, tune, epochs=20, batch_size=32, learning_rate=0.001, patience=4):
        from sklearn.metrics import average_precision_score
        if epochs < 1 or batch_size < 1 or patience < 1 or learning_rate <= 0:
            raise ValueError('Training budgets must be positive')
        ids, structured = self.preprocessor.transform(train)
        y = train.label.to_numpy(dtype=np.float32)
        rng = np.random.default_rng(self.seed)
        if self.backend == 'torch':
            import torch
            optimizer = torch.optim.Adam(self._network.parameters(), lr=learning_rate)
        else:
            import tensorflow as tf
            optimizer = tf.keras.optimizers.Adam(learning_rate)
        best, stale, history, weights = -np.inf, 0, [], None
        for epoch in range(epochs):
            losses = []
            order = rng.permutation(len(y))
            for start in range(0, len(y), batch_size):
                idx = order[start:start+batch_size]
                if self.backend == 'torch':
                    self._network.train()
                    optimizer.zero_grad()
                    logits = self._network(torch.as_tensor(ids[idx]), torch.as_tensor(structured[idx]))
                    loss = torch.nn.functional.binary_cross_entropy_with_logits(logits, torch.as_tensor(y[idx]))
                    loss.backward()
                    torch.nn.utils.clip_grad_norm_(self._network.parameters(), 1.0)
                    optimizer.step()
                    value = loss.item()
                else:
                    with tf.GradientTape() as tape:
                        logits = self._network((ids[idx], structured[idx]), training=True)
                        loss = tf.reduce_mean(tf.nn.sigmoid_cross_entropy_with_logits(labels=y[idx], logits=logits))
                    grads = tape.gradient(loss, self._network.trainable_variables)
                    grads, _ = tf.clip_by_global_norm(grads, 1.0)
                    optimizer.apply_gradients(zip(grads, self._network.trainable_variables))
                    value = float(loss.numpy())
                if not np.isfinite(value):
                    raise ValueError('Non-finite training loss')
                losses.extend([value]*len(idx))
            ap = float(average_precision_score(tune.label, self.predict_proba(tune)[:, 1]))
            history.append({'epoch': epoch+1, 'train_bce': float(np.mean(losses)), 'tuning_AP': ap})
            if ap > best:
                best, stale, weights = ap, 0, self.get_weights()
                self.best_epoch = epoch+1
            else:
                stale += 1
            if stale >= patience:
                break
        self.set_weights(weights)
        return history
