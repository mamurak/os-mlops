from os import environ, listdir, path, unlink
from shutil import rmtree
import yaml

from openimages.download import download_dataset


def ingest_data(data_folder='./data', limit=0):
    _clean_folder(data_folder)
    class_labels = _read_class_labels('configuration.yaml')

    print('Commencing data ingestion.')

    limit = limit or int(environ.get('sample_count', 100))
    download_folder = f'{data_folder}/download'

    download_dataset(
        download_folder,
        class_labels=class_labels,
        annotation_format='darknet',
        limit=limit
    )

    print('data ingestion done')


def _clean_folder(folder):
    print(f'Cleaning folder {folder}')

    for filename in listdir(folder):
        file_path = path.join(folder, filename)
        try:
            if path.isfile(file_path) or path.islink(file_path):
                unlink(file_path)
            elif path.isdir(file_path):
                rmtree(file_path)
        except Exception as e:
            print(f'Failed to delete {file_path}. Reason: {e}')


def _read_class_labels(configuration_file_path):
    with open(configuration_file_path, 'r') as config_file:
        config = yaml.load(config_file.read(), Loader=yaml.SafeLoader)

    class_labels = config['names']
    return class_labels


if __name__ == '__main__':
    ingest_data(data_folder='/data')
