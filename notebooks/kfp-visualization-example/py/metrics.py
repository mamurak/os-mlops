from json import dump
from pprint import pformat

import pandas as pd


def produce_metrics_artifacts():
    print('generating metrics artifacts.')
    _produce_confusion_matrix()
    _produce_custom_metrics()
    print('done')


def _produce_confusion_matrix():
    print('generating confusion matrix')
    matrix = [
        ['yummy', 'yummy', 10],
        ['yummy', 'not yummy', 2],
        ['not yummy', 'yummy', 6],
        ['not yummy', 'not yummy', 7]
    ]

    df = pd.DataFrame(matrix, columns=['target', 'predicted', 'count'])

    metadata = {
        "outputs": [
            {
                "type": "confusion_matrix",
                "format": "csv",
                "schema": [
                    {
                        "name": "target",
                        "type": "CATEGORY"
                    },
                    {
                        "name": "predicted",
                        "type": "CATEGORY"
                    },
                    {
                        "name": "count",
                        "type": "NUMBER"
                    }
                ],
                "source": df.to_csv(header=False, index=False),
                "storage": "inline",
                "labels": [
                    "yummy",
                    "not yummy"
                ]
            }
        ]
    }

    with open('mlpipeline-ui-metadata.json', 'w') as f:
        dump(metadata, f)

    print(f'stored confusion matrix: {pformat(metadata)}')


def _produce_custom_metrics():
    print('generating custom metrics')

    accuracy_score = 0.6
    roc_auc_score = 0.75

    metrics = {
        'metrics': [
            {
                'name': 'accuracy-score',
                'numberValue': accuracy_score,
                'format': 'PERCENTAGE'
            },
            {
                'name': 'roc-auc-score',
                'numberValue': roc_auc_score,
                'format': 'RAW'
            },
        ]
    }

    with open('mlpipeline-metrics.json', 'w') as f:
        dump(metrics, f)

    print(f'stored custom metrics: {pformat(metrics)}')


if __name__ == '__main__':
    produce_metrics_artifacts()