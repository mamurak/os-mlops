from pandas import read_csv


def preprocess(data_folder='./data'):
    print('Commencing data preprocessing.')

    raw_data = read_csv(f'{data_folder}/raw_data.csv')

    features = _extract_features(raw_data)

    features.to_pickle(f'{data_folder}/features.pickle')

    print('Data preprocessing done.')


def _extract_features(raw_data):
    '''This is where your preprocessing code goes.'''
    return raw_data


if __name__ == '__main__':
    preprocess(data_folder='/data')
