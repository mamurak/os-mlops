"""Generate pre-computed JSON data files for the data drift detection demo.

Reads the training CSV, applies the same preprocessing as the model training
pipeline (RobustScaler on Amount and Time), and produces three JSON files:
  - data/reference_data.json   (1000 samples for TrustyAI reference upload)
  - data/live_data_normal.json (500 in-distribution samples for inference)
  - data/live_data_drift.json  (1000 out-of-distribution samples for inference)

Run once before the demo:
    python prepare_data.py
"""

from json import dump
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.preprocessing import RobustScaler

TRAINING_CSV = Path(__file__).parent / '../training/data/training-data.csv'
DATA_DIR = Path(__file__).parent / 'data'

SEED = 42
REFERENCE_SIZE = 1000
NORMAL_SIZE = 500
DRIFT_SIZE = 1000

FEATURE_COLUMNS = ['scaled_amount', 'scaled_time'] + [f'V{i}' for i in range(1, 29)]

DRIFT_SPEC = {
    'scaled_amount': 3.0,
    'V1': 3.0,
    'V4': 3.0,
    'V14': -3.0,
}


OUTPUT_NAME = 'dense_2'


def preprocess(df):
    labels = df['Class'].astype(int).values
    rob_scaler = RobustScaler()
    df['scaled_amount'] = rob_scaler.fit_transform(
        df['Amount'].values.reshape(-1, 1)
    )
    df['scaled_time'] = rob_scaler.fit_transform(
        df['Time'].values.reshape(-1, 1)
    )
    df.drop(['Time', 'Amount', 'Class'], axis=1, inplace=True)
    return df[FEATURE_COLUMNS], labels


def to_kserve_inputs(data, precision=5):
    rounded = np.round(data, precision)
    return {
        'inputs': [{
            'name': 'dense_input',
            'shape': list(rounded.shape),
            'datatype': 'FP32',
            'data': rounded.tolist(),
        }]
    }


def generate_outputs(labels, rng):
    """Generate synthetic softmax outputs matching the class labels."""
    n = len(labels)
    outputs = np.zeros((n, 2), dtype='float32')
    noise = rng.uniform(0.0, 0.08, size=n).astype('float32')
    for i in range(n):
        if labels[i] == 0:
            outputs[i] = [0.92 + noise[i], 0.08 - noise[i]]
        else:
            outputs[i] = [0.08 - noise[i], 0.92 + noise[i]]
    return outputs


def to_kserve_reference(data, outputs, precision=5):
    rounded_data = np.round(data, precision)
    rounded_outputs = np.round(outputs, precision)
    return {
        'inputs': [{
            'name': 'dense_input',
            'shape': list(rounded_data.shape),
            'datatype': 'FP32',
            'data': rounded_data.tolist(),
        }],
        'outputs': [{
            'name': OUTPUT_NAME,
            'shape': list(rounded_outputs.shape),
            'datatype': 'FP32',
            'data': rounded_outputs.tolist(),
        }],
    }


def write_json(payload, path):
    with open(path, 'w') as f:
        dump(payload, f, separators=(',', ':'))
        f.write('\n')
    size_kb = path.stat().st_size / 1024
    print(f'  {path.name}: {size_kb:.0f} KB')


def main():
    print(f'Loading {TRAINING_CSV}...')
    df = pd.read_csv(TRAINING_CSV)
    print(f'  {len(df)} rows loaded')

    print('Preprocessing...')
    df, labels = preprocess(df)
    values = df.values.astype('float32')

    rng = np.random.default_rng(SEED)
    all_indices = np.arange(len(values))

    ref_indices = rng.choice(all_indices, size=REFERENCE_SIZE, replace=False)

    # Use a subset of the reference samples for in-distribution inference so
    # that the KS test sees identical distributions and produces p-values near
    # 1.0, giving a clear visual baseline in the dashboard.
    normal_indices = rng.choice(ref_indices, size=NORMAL_SIZE, replace=False)

    remaining = np.setdiff1d(all_indices, ref_indices)
    drift_base_indices = rng.choice(remaining, size=DRIFT_SIZE, replace=False)
    drift_data = values[drift_base_indices].copy()

    feature_stds = values.std(axis=0)
    print('\nApplying drift:')
    for feat_name, shift_stdevs in DRIFT_SPEC.items():
        idx = FEATURE_COLUMNS.index(feat_name)
        offset = shift_stdevs * feature_stds[idx]
        drift_data[:, idx] += offset
        print(f'  {feat_name} (index {idx}): {shift_stdevs:+.0f} stdev = {offset:+.4f}')

    ref_outputs = generate_outputs(labels[ref_indices], rng)

    print('\nWriting JSON files:')
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    write_json(
        to_kserve_reference(values[ref_indices], ref_outputs),
        DATA_DIR / 'reference_data.json',
    )
    write_json(
        to_kserve_inputs(values[normal_indices]),
        DATA_DIR / 'live_data_normal.json',
    )
    write_json(
        to_kserve_inputs(drift_data),
        DATA_DIR / 'live_data_drift.json',
    )

    print('\nDone.')


if __name__ == '__main__':
    main()
