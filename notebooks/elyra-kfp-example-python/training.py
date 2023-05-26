import json
from time import time

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import f1_score, classification_report
from joblib import dump


X_all = pd.read_pickle('features.pickle')
y_all = pd.read_pickle('labels.pickle')

tree_depth = 2

X_train, X_test, y_train, y_test = train_test_split(
    X_all, y_all, test_size=0.33, random_state=42
)

# Show the results of the split
print("Training set has {} samples.".format(X_train.shape[0]))
print("Testing set has {} samples.".format(X_test.shape[0]))

print("Anomaly rate of the training set: {:.2f}%"
      .format(100 * (y_train == 1).mean()))
print("Anomaly rate of the testing set: {:.2f}%"
      .format(100 * (y_test == 1).mean()))

def train_classifier(clf, X_train, y_train):
    ''' Fits a classifier to the training data. '''

    # Start the clock, train the classifier, then stop the clock
    start = time()
    clf.fit(X_train, y_train)
    end = time()

    # Print the results
    print("Trained model in {:.4f} seconds".format(end - start))


def predict_labels(clf, features, target):
    ''' Makes predictions using a fit classifier based on F1 score. '''

    # Start the clock, make predictions, then stop the clock
    start = time()
    y_pred = clf.predict(features)
    end = time()

    # Print and return results
    print("Made predictions in {:.4f} seconds.".format(end - start))
    return f1_score(target.values, y_pred)


def train_predict(clf, X_train, y_train, X_test, y_test):
    ''' Train and predict using a classifer based on F1 score. '''

    # Indicate the classifier and the training set size
    print("Training a {} using a training set size of {}. . ."
          .format(clf.__class__.__name__, len(X_train)))

    # Train the classifier
    train_classifier(clf, X_train, y_train)

    # Print the results of prediction for both training and testing
    print("F1 score for training set: {:.4f}."
          .format(predict_labels(clf, X_train, y_train)))
    print("F1 score for test set: {:.4f}."
          .format(predict_labels(clf, X_test, y_test)))

my_random_seed = 42

model = DecisionTreeClassifier(
    random_state=my_random_seed,
    max_depth=tree_depth,
)

train_predict(model, X_train, y_train, X_test, y_test)
print(classification_report(y_test, model.predict(X_test)))
print('-'*52)

filename = 'model.joblib'
dump(model, open(filename, 'wb'))

f1_score = f1_score(y_test, model.predict(X_test))
metrics = {
    'metrics': [
        {
            'name': 'tree depth',
            'numberValue': tree_depth,
            'format': 'RAW'
        },
        {
            'name': 'F1-score',
            'numberValue': f1_score,
            'format': 'PERCENTAGE'
        }
    ]
}

with open('mlpipeline-metrics.json', 'w') as f:
    json.dump(metrics, f)
