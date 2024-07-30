from kfp.dsl import component, Dataset, Input, Output


runtime_image = 'quay.io/mmurakam/runtimes:fraud-detection-v2.1.0'


@component(base_image=runtime_image)
def preprocess(
        raw_data: Input[Dataset], training_samples: Output[Dataset],
        training_labels: Output[Dataset]):
    from pickle import dump

    from imblearn.over_sampling import SMOTE
    from pandas import read_csv
    from sklearn.model_selection import StratifiedKFold
    from sklearn.preprocessing import RobustScaler

    print('Preprocessing data.')

    df = read_csv(raw_data.path)

    rob_scaler = RobustScaler()

    df['scaled_amount'] = rob_scaler.fit_transform(
        df['Amount'].values.reshape(-1, 1)
    )
    df['scaled_time'] = rob_scaler.fit_transform(
        df['Time'].values.reshape(-1, 1)
    )
    df.drop(['Time', 'Amount'], axis=1, inplace=True)
    scaled_amount = df['scaled_amount']
    scaled_time = df['scaled_time']

    df.drop(['scaled_amount', 'scaled_time'], axis=1, inplace=True)
    df.insert(0, 'scaled_amount', scaled_amount)
    df.insert(1, 'scaled_time', scaled_time)

    X = df.drop('Class', axis=1)
    y = df['Class']
    sss = StratifiedKFold(n_splits=5, random_state=None, shuffle=False)

    for train_index, test_index in sss.split(X, y):
        print("Train:", train_index, "Test:", test_index)
        original_Xtrain = X.iloc[train_index]
        original_ytrain = y.iloc[train_index]

    original_Xtrain = original_Xtrain.values
    original_ytrain = original_ytrain.values

    sm = SMOTE(sampling_strategy='minority', random_state=42)
    Xsm_train, ysm_train = sm.fit_resample(original_Xtrain, original_ytrain)

    with open(training_samples.path, 'wb') as samples_file:
        dump(Xsm_train, samples_file)
    with open(training_labels.path, 'wb') as labels_file:
        dump(ysm_train, labels_file)

    print('data processing done')