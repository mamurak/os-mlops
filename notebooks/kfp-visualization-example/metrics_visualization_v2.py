# Copyright 2021 The Kubeflow Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import os

from kfp import dsl
from kfp.client import Client
from kfp.dsl import (component, Output, ClassificationMetrics, Metrics, HTML,
                     Markdown)

# In tests, we install a KFP package from the PR under test. Users should not
# normally need to specify `kfp_package_path` in their component definitions.
_KFP_PACKAGE_PATH = os.getenv('KFP_PACKAGE_PATH')


@component(
    packages_to_install=['scikit-learn'],
    base_image='python:3.9',
    kfp_package_path=_KFP_PACKAGE_PATH,
)
def digit_classification(metrics: Output[Metrics]):
    from sklearn import model_selection
    from sklearn.linear_model import LogisticRegression
    from sklearn import datasets

    # Load digits dataset
    iris = datasets.load_iris()

    # # Create feature matrix
    X = iris.data

    # Create target vector
    y = iris.target

    test_size = 0.33

    seed = 7
    kfold = model_selection.KFold(n_splits=10, random_state=seed, shuffle=True)

    model = LogisticRegression()
    scoring = 'accuracy'
    model_selection.cross_val_score(
        model, X, y, cv=kfold, scoring=scoring)

    X_train, X_test, y_train, y_test = model_selection.train_test_split(
        X, y, test_size=test_size, random_state=seed)
    model.fit(X_train, y_train)

    result = model.score(X_test, y_test)
    metrics.log_metric('accuracy', (result * 100.0))


@component(
    packages_to_install=['scikit-learn'],
    base_image='python:3.9',
    kfp_package_path=_KFP_PACKAGE_PATH,
)
def wine_classification(metrics: Output[ClassificationMetrics]):
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import roc_curve
    from sklearn.datasets import load_wine
    from sklearn.model_selection import train_test_split, cross_val_predict

    X, y = load_wine(return_X_y=True)
    # Binary classification problem for label 1.
    y = y == 1

    X_train, X_test, y_train, y_test = train_test_split(X, y, random_state=42)
    rfc = RandomForestClassifier(n_estimators=10, random_state=42)
    rfc.fit(X_train, y_train)
    y_scores = cross_val_predict(
        rfc, X_train, y_train, cv=3, method='predict_proba')
    cross_val_predict(rfc, X_train, y_train, cv=3, method='predict')
    fpr, tpr, thresholds = roc_curve(
        y_true=y_train, y_score=y_scores[:, 1], pos_label=True)

    # avoid inf thresholds
    epsilon = 1e-6
    thresholds = [1 - epsilon if t == float('inf') else t for t in thresholds]

    metrics.log_roc_curve(fpr, tpr, thresholds)


@component(
    packages_to_install=['scikit-learn'],
    base_image='python:3.9',
    kfp_package_path=_KFP_PACKAGE_PATH,
)
def iris_sgdclassifier(test_samples_fraction: float,
                       metrics: Output[ClassificationMetrics]):
    from sklearn import datasets, model_selection
    from sklearn.linear_model import SGDClassifier
    from sklearn.metrics import confusion_matrix

    iris_dataset = datasets.load_iris()
    train_x, test_x, train_y, test_y = model_selection.train_test_split(
        iris_dataset['data'],
        iris_dataset['target'],
        test_size=test_samples_fraction)

    classifier = SGDClassifier()
    classifier.fit(train_x, train_y)
    predictions = model_selection.cross_val_predict(
        classifier, train_x, train_y, cv=3)
    metrics.log_confusion_matrix(
        ['Setosa', 'Versicolour', 'Virginica'],
        confusion_matrix(
            train_y,
            predictions).tolist()  # .tolist() to convert np array to list.
    )


@component(
    kfp_package_path=_KFP_PACKAGE_PATH,)
def html_visualization(html_artifact: Output[HTML]):
    html_content = '<!DOCTYPE html><html><body><h1>Hello world</h1></body></html>'
    with open(html_artifact.path, 'w') as f:
        f.write(html_content)


@component(
    kfp_package_path=_KFP_PACKAGE_PATH,)
def markdown_visualization(markdown_artifact: Output[Markdown]):
    markdown_content = '''
## This should be rendered as a header
The following should be rendered as a table:

| Item | Quantity |
| ---- | -------- |
| Apples | 2 |
| Pears | 2.5 |
| **Total** | **4.5** |
    '''
    with open(markdown_artifact.path, 'w') as f:
        f.write(markdown_content)


@dsl.pipeline(name='metrics-visualization-pipeline')
def metrics_visualization_pipeline():
    wine_classification()
    iris_sgdclassifier(test_samples_fraction=0.3)
    digit_classification()
    html_visualization()
    markdown_visualization()


def submit(pipeline):
    namespace_file_path =\
        '/var/run/secrets/kubernetes.io/serviceaccount/namespace'
    with open(namespace_file_path, 'r') as namespace_file:
        namespace = namespace_file.read()

    kubeflow_endpoint =\
        f'https://ds-pipeline-dspa.{namespace}.svc:8443'

    sa_token_file_path = '/var/run/secrets/kubernetes.io/serviceaccount/token'
    with open(sa_token_file_path, 'r') as token_file:
        bearer_token = token_file.read()

    ssl_ca_cert =\
        '/var/run/secrets/kubernetes.io/serviceaccount/service-ca.crt'

    print(f'Connecting to Data Science Pipelines: {kubeflow_endpoint}')
    client = Client(
        host=kubeflow_endpoint,
        existing_token=bearer_token,
        ssl_ca_cert=ssl_ca_cert
    )
    result = client.create_run_from_pipeline_func(
        pipeline,
        arguments={},
        experiment_name='visualization-pipeline',
    )
    print(f'Starting pipeline run with run_id: {result.run_id}')


if __name__ == '__main__':
    submit(metrics_visualization_pipeline)