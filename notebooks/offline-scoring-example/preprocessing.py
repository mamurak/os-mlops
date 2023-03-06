from pandas import read_csv


def preprocess():
    print('Commencing data preprocessing.')

    raw_data = read_csv('raw_data.csv')

    features = _extract_features(raw_data)

    features.to_pickle('features.pickle')

    print('Data preprocessing done.')


def _extract_features(raw_data):
    '''This is where your preprocessing code goes.'''
    return raw_data


if __name__ == '__main__':
    preprocess()
