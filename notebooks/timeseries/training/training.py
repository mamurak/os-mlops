from os import environ
from time import time

from joblib import dump
import mlflow
from mlflow import (
    log_metric, set_experiment, set_tracking_uri, start_run
)
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import f1_score, classification_report


mlflow_tracking_uri = environ.get('mlflow-tracking-uri')
mlflow_experiment = environ.get('mlflow_experiment')
environ['AWS_ACCESS_KEY_ID'] = environ.get('mlflow-s3-access-key')
environ['AWS_SECRET_ACCESS_KEY'] = environ.get('mlflow-s3-secret-key')
environ['MLFLOW_S3_ENDPOINT_URL'] = environ.get('mlflow-s3-endpoint-url')
tree_depth = int(environ.get('tree_depth', '2'))


def run_training():
    set_tracking_uri(mlflow_tracking_uri)
    set_experiment(mlflow_experiment)
    mlflow.sklearn.autolog()
    with start_run():
        X_all = pd.read_pickle('features.pickle')
        y_all = pd.read_pickle('labels.pickle')

        X_train, X_test, y_train, y_test = train_test_split(
            X_all, y_all, test_size=0.33, random_state=42
        )

        print("Training set has {} samples.".format(X_train.shape[0]))
        print("Testing set has {} samples.".format(X_test.shape[0]))

        print("Anomaly rate of the training set: {:.2f}%"
              .format(100 * (y_train == 1).mean()))
        print("Anomaly rate of the testing set: {:.2f}%"
              .format(100 * (y_test == 1).mean()))

        my_random_seed = 42

        model = DecisionTreeClassifier(
            random_state=my_random_seed,
            max_depth=tree_depth,
        )

        _train_predict(model, X_train, y_train, X_test, y_test)
        print(classification_report(y_test, model.predict(X_test)))
        print('-'*52)

        filename = 'model.joblib'
        dump(model, open(filename, 'wb'))

        f1_score_ = f1_score(y_test, model.predict(X_test))
        log_metric('f1_score', f1_score_)


def _train_predict(clf, X_train, y_train, X_test, y_test):
    ''' Train and predict using a classifer based on F1 score. '''

    # Indicate the classifier and the training set size
    print("Training a {} using a training set size of {}. . ."
          .format(clf.__class__.__name__, len(X_train)))

    # Train the classifier
    _train_classifier(clf, X_train, y_train)

    # Print the results of prediction for both training and testing
    print("F1 score for training set: {:.4f}."
          .format(_predict_labels(clf, X_train, y_train)))
    print("F1 score for test set: {:.4f}."
          .format(_predict_labels(clf, X_test, y_test)))


def _train_classifier(clf, X_train, y_train):
    ''' Fits a classifier to the training data. '''

    # Start the clock, train the classifier, then stop the clock
    start = time()
    clf.fit(X_train, y_train)
    end = time()

    # Print the results
    print("Trained model in {:.4f} seconds".format(end - start))


def _predict_labels(clf, features, target):
    ''' Makes predictions using a fit classifier based on F1 score. '''

    # Start the clock, make predictions, then stop the clock
    start = time()
    y_pred = clf.predict(features)
    end = time()

    # Print and return results
    print("Made predictions in {:.4f} seconds.".format(end - start))
    return f1_score(target.values, y_pred)


if __name__ == '__main__':
    run_training()