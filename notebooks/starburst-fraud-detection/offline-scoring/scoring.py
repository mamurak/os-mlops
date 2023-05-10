from joblib import load
from pandas import concat, DataFrame, read_parquet


def predict(data_folder='./data'):
    print('Commencing offline scoring.')

    model = load(open('model.joblib', 'rb'))
    data = read_parquet(f'{data_folder}/data.parquet')

    feature_columns = [
        'user_id', 'amount', 'trans_type', 'foreign', 'interarrival'
    ]
    predictions = concat([
        data[['timestamp', 'transaction_id']],
        DataFrame(model.predict(data[feature_columns]), columns=['labels']),
    ], axis=1)

    print(f'Prediction results: {predictions}')

    predictions.to_csv(f'{data_folder}/predictions.csv', index=False)

    print('Offline scoring complete.')


if __name__ == '__main__':
    predict(data_folder='/data')
