from joblib import load
from numpy import savetxt
from pandas import read_pickle


def predict():
    print('Commencing offline scoring.')

    model = load(open('model.joblib', 'rb'))
    X_all = read_pickle('features.pickle')

    predictions = model.predict(X_all)

    print(f'Prediction results: {predictions}')

    savetxt('predictions.csv', predictions, delimiter=',')

    print('Offline scoring complete.')


if __name__ == '__main__':
    predict()
