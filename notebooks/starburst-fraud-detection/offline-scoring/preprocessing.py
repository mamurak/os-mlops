from numpy import save
from pandas import read_parquet
from sklearn.preprocessing import RobustScaler


def preprocess(data_folder='./data'):
    print('preprocessing data')

    df = read_parquet(f'{data_folder}/data.parquet')

    rob_scaler = RobustScaler()

    df['scaled_amount'] = rob_scaler.fit_transform(
        df['amount'].values.reshape(-1, 1)
    )
    df['scaled_time'] = rob_scaler.fit_transform(
        df['time'].values.reshape(-1, 1)
    )
    df.drop(['time', 'amount'], axis=1, inplace=True)
    scaled_amount = df['scaled_amount']
    scaled_time = df['scaled_time']

    df.drop(['scaled_amount', 'scaled_time'], axis=1, inplace=True)
    df.insert(0, 'scaled_amount', scaled_amount)
    df.insert(1, 'scaled_time', scaled_time)

    save(f'{data_folder}/samples.npy', df.values)

    print('data processing done')


if __name__ == '__main__':
    preprocess(data_folder='/data')
