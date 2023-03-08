from datetime import datetime
from os import getenv

import mlflow
import pandas as pd
from sklearn.metrics import brier_score_loss, roc_auc_score
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression


def get_labels():
    labels = load_breast_cancer().target
    return labels


def get_training_samples():
    training_set = load_breast_cancer()
    training_samples = training_set.data
    feature_names = training_set.feature_names
    return training_samples, feature_names


mlflow_server_endpoint = getenv('MLFLOW_SERVER_ENDPOINT', 'http://mlflow-server:80')
mlflow_experiment_name = getenv('MLFLOW_EXPERIMENT_NAME', 'test-experiment')
timestamp = datetime.now().strftime('%y%m%d%H%M%S')

mlflow.set_tracking_uri(mlflow_server_endpoint)
client = mlflow.tracking.MlflowClient()

try:
    experiment = mlflow.get_experiment_by_name(mlflow_experiment_name)
    experiment_id = experiment.experiment_id
except:
    print(f'Experiment "{mlflow_experiment_name}" does exists yet.'
          f'Creating experiment')
    experiment_id = mlflow.create_experiment(name = mlflow_experiment_name)

run_id = f'vrp-{mlflow_experiment_name}-{timestamp}'

active_run = mlflow.start_run(run_name = run_id,
                              experiment_id = experiment_id)

print(active_run.info.experiment_id)
print(mlflow.get_experiment(active_run.info.experiment_id).name)
print(mlflow.get_experiment(active_run.info.experiment_id).artifact_location)
print(active_run.info.lifecycle_stage)
print(active_run.info.status)
print(active_run.info.user_id)
print(active_run.info.run_id)
print(mlflow.tracking.get_tracking_uri())


y = pd.Series(get_labels(),name="Target")
training_samples, feature_names = get_training_samples()
X = pd.DataFrame(training_samples,columns=feature_names)

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.30, random_state=42
)
del (X,y)

pipe = Pipeline([
    ('scaler', StandardScaler()),
    ('estimator', LogisticRegression(
        penalty="l2", C=10.0, random_state=0, solver="liblinear"
    ))
])

pipe.fit(X_train,y_train)


brier = brier_score_loss(y_test, pipe.predict_proba(X_test)[:, 1])
roc = roc_auc_score(y_test, pipe.predict_proba(X_test)[:, 1])

mlflow.log_param("C", "10")
mlflow.log_param("Penalty", "l2")
mlflow.log_metric("brier", brier)
mlflow.log_metric("roc", roc)

mlflow.sklearn.log_model(
    pipe, "my_model",
    registered_model_name="sk-learn-random-forest-reg-model",
)

mlflow.end_run()
