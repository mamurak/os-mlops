from joblib import load
from pandas import read_parquet


def predict(data_folder='./data'):
    print('Commencing offline scoring.')

    model = load(open('model.joblib', 'rb'))
    data = read_parquet(f'{data_folder}/data.parquet')

    feature_columns = [
        'user_id', 'amount', 'trans_type', 'foreign', 'interarrival'
    ]
    predictions = model.predict(data[feature_columns])

    data['labels'] = predictions

    print(f'Prediction results: {predictions}')

    data[['timestamp', 'transaction_id', 'labels']].to_csv(
        f'{data_folder}/predictions.csv', index=False
    )

    print('Offline scoring complete.')


if __name__ == '__main__':
    predict(data_folder='/data')
