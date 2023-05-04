from joblib import dump
from pandas import read_parquet
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, RobustScaler, OneHotEncoder, FeatureHasher


def preprocess_data():
    print('preprocessing data')

    df = read_parquet('data.parquet')
    train, _ = train_test_split(df, random_state=43)

    def amap(s):
        return s.map(lambda x: {'merchant_id': str(x)})

    tt_xform = (
        'onehot',
        OneHotEncoder(
            handle_unknown='ignore',
            categories=[['online', 'contactless', 'chip_and_pin', 'manual', 'swipe']]
        ),
        ['trans_type']
    )

    mk_hasher = Pipeline([
        ('dictify', FunctionTransformer(amap, accept_sparse=True)),
        ('hasher', FeatureHasher(n_features=256, input_type='dict')),
    ])
    mu_xform = ('m_hashing', mk_hasher, 'merchant_id')
    xform_steps = [tt_xform, mu_xform]

    impute_and_scale = Pipeline([
        ('median_imputer', SimpleImputer(strategy="median")),
        ('interarrival_scaler', RobustScaler())
    ])
    ia_scaler = ('interarrival_scaler', impute_and_scale, ['interarrival'])
    amount_scaler = ('amount_scaler', RobustScaler(), ['amount'])

    scale_steps = [ia_scaler, amount_scaler]
    all_xforms = ColumnTransformer(transformers=(scale_steps + xform_steps))
    feature_pipeline = Pipeline([('feature_extraction', all_xforms)])

    feature_pipeline.fit(train)
    dump(feature_pipeline, open('feature_pipeline.joblib', 'wb'))

    print('data processing done')


if __name__ == '__main__':
    preprocess_data()
