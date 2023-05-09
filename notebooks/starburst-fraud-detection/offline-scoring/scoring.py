from joblib import load
from pandas import read_parquet


def predict(data_folder='./data'):
    print('Commencing offline scoring.')

    model = load(open('model.joblib', 'rb'))
    features = read_parquet(f'{data_folder}/data.parquet')

    predictions = model.predict(features)

    print(f'Prediction results: {predictions}')

    predictions.to_csv(f'{data_folder}/predictions.csv')

    print('Offline scoring complete.')


if __name__ == '__main__':
    predict(data_folder='/data')
