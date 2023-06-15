from joblib import dump
from pandas import read_parquet
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import RobustScaler, OneHotEncoder


def preprocess_data(data_folder='./data'):
    print('preprocessing data')

    df = read_parquet(f'{data_folder}/data.parquet')
    train, _ = train_test_split(df, random_state=43)

    tt_xform = (
        'onehot',
        OneHotEncoder(
            handle_unknown='ignore',
            categories=[[
                'online', 'contactless', 'chip_and_pin', 'manual', 'swipe'
            ]]
        ),
        ['trans_type']
    )

    impute_and_scale = Pipeline([
        ('median_imputer', SimpleImputer(strategy='median')),
        ('interarrival_scaler', RobustScaler())
    ])
    ia_scaler = ('interarrival_scaler', impute_and_scale, ['interarrival'])
    amount_scaler = ('amount_scaler', RobustScaler(), ['amount'])

    all_xforms = ColumnTransformer(
        transformers=([ia_scaler, amount_scaler, tt_xform])
    )
    feature_pipeline = Pipeline([('feature_extraction', all_xforms)])

    feature_columns = [
        'user_id', 'amount', 'trans_type', 'foreign', 'interarrival'
    ]
    feature_pipeline.fit(train[feature_columns])
    dump(feature_pipeline, open('feature_pipeline.joblib', 'wb'))

    print('data processing done')


if __name__ == '__main__':
    preprocess_data(data_folder='/data')
