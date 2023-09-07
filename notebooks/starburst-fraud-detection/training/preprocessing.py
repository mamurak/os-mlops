from pandas import read_parquet
from imblearn.over_sampling import SMOTE
from numpy import save
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import RobustScaler


def preprocess_data(data_folder='./data'):
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

    X = df.drop('label', axis=1)
    y = df['label']
    sss = StratifiedKFold(n_splits=5, random_state=None, shuffle=False)

    for train_index, test_index in sss.split(X, y):
        print("Train:", train_index, "Test:", test_index)
        original_Xtrain = X.iloc[train_index]
        original_ytrain = y.iloc[train_index]

    original_Xtrain = original_Xtrain.values
    original_ytrain = original_ytrain.values

    sm = SMOTE(sampling_strategy='minority', random_state=42)
    Xsm_train, ysm_train = sm.fit_resample(original_Xtrain, original_ytrain)

    save(f'{data_folder}/training_samples.npy', Xsm_train)
    save(f'{data_folder}/training_labels.npy', ysm_train.astype(int))

    print('data processing done')


if __name__ == '__main__':
    preprocess_data(data_folder='/data')
