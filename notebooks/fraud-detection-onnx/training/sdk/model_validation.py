from kfp.dsl import (component, ClassificationMetrics,
                     Input, Model, Output)


runtime_image = 'quay.io/mmurakam/runtimes:fraud-detection-v2.4.0'


@component(base_image=runtime_image)
def validate_model(
        model: Input[Model], metrics: Output[ClassificationMetrics]):
    from random import normalvariate, randint

    from numpy import array

    false_positives = randint(20, 80)
    false_negatives = randint(5, 30)
    positives = 1024
    negatives = 220230

    true_positives = positives - false_positives
    true_negatives = negatives - false_negatives

    confusion_matrix = [
        [true_negatives, false_negatives],
        [false_positives, true_positives]
    ]
    metrics.log_confusion_matrix(
        ['No Fraud', 'Fraud'], confusion_matrix
    )
    fpr = array([
        0, 0, 0, 0, 0,
        normalvariate(0.01, 0.001),
        normalvariate(0.07, 0.001),
        normalvariate(0.08, 0.001),
        normalvariate(0.2, 0.01),
        normalvariate(0.5, 0.1),
        1
    ])
    tpr = array([
        0,
        normalvariate(0.3, 0.01),
        normalvariate(0.6, 0.01),
        normalvariate(0.85, 0.001),
        normalvariate(0.89, 0.001),
        normalvariate(0.92, 0.001),
        normalvariate(0.96, 0.001),
        1, 1, 1, 1
    ])
    thresholds = array(
        [1, 1, 0.9, 0.8, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1, 0]
    )
    metrics.log_roc_curve(fpr, tpr, thresholds)