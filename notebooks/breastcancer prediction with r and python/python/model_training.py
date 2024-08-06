from os import environ

from numpy import mean
from pandas import read_csv
from xgboost import DMatrix, train


# Read environment variables
max_depth = int(environ.get('max_depth', '10'))
n_round = int(environ.get('n_round', '21'))
early_stopping_rounds = int(environ.get('early_stopping_rounds', '3'))

print('Loading training and test data')
train_set = read_csv("train.csv")
test_set = read_csv("test.csv")

# Remove labels
train_data = train_set.drop(columns=['diagnosis'])
test_data = test_set.drop(columns=['diagnosis'])

# Create targets
train_label = train_set['diagnosis'].apply(lambda x: 1 if x == "M" else 0).values
test_label = test_set['diagnosis'].apply(lambda x: 1 if x == "M" else 0).values

# Convert to matrices
train_matrix = train_data.values
test_matrix = test_data.values

# Create DMatrix
dtrain = DMatrix(data=train_matrix, label=train_label)
dtest = DMatrix(data=test_matrix, label=test_label)

print('Training model...')
breastcancer_model = train(
    params={
        'max_depth': max_depth,
        'objective': 'binary:logistic',
        'verbosity': 2,
        'early_stopping_rounds': early_stopping_rounds
    },
    dtrain=dtrain,
    num_boost_round=n_round,
    evals=[(dtest, 'test')]
)

# Predict and evaluate
pred = breastcancer_model.predict(dtest)
err = mean((pred > 0.5).astype(int) != test_label)
print(f"test-error= {err}")

print('Saving model')
breastcancer_model.save_model('model.bst')