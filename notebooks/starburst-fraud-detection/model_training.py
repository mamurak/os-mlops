from joblib import dump, load
from pandas import read_parquet
from sklearn.metrics import classification_report
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline


def train_model_pipeline():
    print('training model')

    df = read_parquet('data.parquet')
    train, test = train_test_split(df, random_state=43)

    feature_pipeline = _load_feature_pipeline()
    model = _train_model(train, feature_pipeline)

    predictions = model.predict(feature_pipeline.fit_transform(test))
    print(classification_report(test.label.values, predictions))

    pipeline = Pipeline([
        ('features', feature_pipeline),
        ('model', model)
    ])
    pipeline.fit(train, y = train["label"])
    dump(pipeline, open('model.joblib', 'wb'))

    print('model training done')


def _load_feature_pipeline():
    with open('feature_pipeline.joblib', 'rb') as inputfile:
        feature_pipeline = load(inputfile)
    return feature_pipeline


def _train_model(train, feature_pipeline):
    fraud_frequency = train[train["label"] == "fraud"]["timestamp"].count() / train["timestamp"].count()
    train.loc[train["label"] == "legitimate", "weights"] = fraud_frequency
    train.loc[train["label"] == "fraud", "weights"] = (1 - fraud_frequency)

    model = LogisticRegression(max_iter=500)

    svecs = feature_pipeline.fit_transform(train)
    model.fit(svecs, train["label"], sample_weight=train["weights"])
    return model


if __name__ == '__main__':
    train_model_pipeline()
