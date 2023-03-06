from pickle import load

from lightgbm import Booster
from pandas import DataFrame


def predict():
    print('Commencing offline scoring.')

    model = Booster(model_file='model.bst')
    features = load(open('features.pickle', 'rb'))

    y_prediction_probs = model.predict(features)

    y_prediction_data = DataFrame(
        y_prediction_probs,
        columns=['class A', 'class B', 'class C', 'class D']
    )

    y_prediction_data.reset_index(inplace=True)

    print(f'Prediction results: {y_prediction_data}')

    y_prediction_data.to_csv('predictions.csv')

    print('Offline scoring complete.')


if __name__ == '__main__':
    predict()
