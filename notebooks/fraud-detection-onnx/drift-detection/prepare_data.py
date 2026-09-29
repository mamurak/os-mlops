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


def preprocess(df):
    rob_scaler = RobustScaler()
    df['scaled_amount'] = rob_scaler.fit_transform(
        df['Amount'].values.reshape(-1, 1)
    )
    df['scaled_time'] = rob_scaler.fit_transform(
        df['Time'].values.reshape(-1, 1)
    )
    df.drop(['Time', 'Amount', 'Class'], axis=1, inplace=True)
    return df[FEATURE_COLUMNS]


def to_kserve_payload(data, precision=6):
    rounded = np.round(data, precision)
    return {
        'inputs': [{
            'name': 'dense_input',
            'shape': list(rounded.shape),
            'datatype': 'FP32',
            'data': rounded.tolist(),
        }]
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
    df = preprocess(df)
    values = df.values.astype('float32')

    rng = np.random.default_rng(SEED)
    all_indices = np.arange(len(values))

    ref_indices = rng.choice(all_indices, size=REFERENCE_SIZE, replace=False)
    remaining = np.setdiff1d(all_indices, ref_indices)

    normal_indices = rng.choice(remaining, size=NORMAL_SIZE, replace=False)
    remaining = np.setdiff1d(remaining, normal_indices)

    drift_base_indices = rng.choice(remaining, size=DRIFT_SIZE, replace=False)
    drift_data = values[drift_base_indices].copy()

    feature_stds = values.std(axis=0)
    print('\nApplying drift:')
    for feat_name, shift_stdevs in DRIFT_SPEC.items():
        idx = FEATURE_COLUMNS.index(feat_name)
        offset = shift_stdevs * feature_stds[idx]
        drift_data[:, idx] += offset
        print(f'  {feat_name} (index {idx}): {shift_stdevs:+.0f} stdev = {offset:+.4f}')

    print('\nWriting JSON files:')
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    write_json(
        to_kserve_payload(values[ref_indices]),
        DATA_DIR / 'reference_data.json',
    )
    write_json(
        to_kserve_payload(values[normal_indices]),
        DATA_DIR / 'live_data_normal.json',
    )
    write_json(
        to_kserve_payload(drift_data),
        DATA_DIR / 'live_data_drift.json',
    )

    print('\nDone.')


if __name__ == '__main__':
    main()
