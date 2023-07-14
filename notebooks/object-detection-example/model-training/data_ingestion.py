from os import environ

from openimages.download import download_dataset


def ingest_data(data_folder='./data', limit=100):
    print('ingesting data')

    limit = limit or int(environ.get('sample_count', 5))
    download_folder = f'{data_folder}/download'

    download_dataset(
        download_folder,
        class_labels=['Bicycle', 'Car', 'Traffic sign'],
        annotation_format='darknet',
        limit=limit
    )

    print('data ingestion done')


if __name__ == '__main__':
    ingest_data(data_folder='/data')
