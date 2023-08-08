from os import environ, listdir, path, unlink
from shutil import rmtree

from openimages.download import download_dataset

from classes import training_classes


def ingest_data(data_folder='./data', limit=0):
    _clean_folder(data_folder)

    print('Commencing data ingestion.')

    limit = limit or int(environ.get('sample_count', 100))
    download_folder = f'{data_folder}/download'

    download_dataset(
        download_folder,
        class_labels=training_classes,
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


if __name__ == '__main__':
    ingest_data(data_folder='/data')
