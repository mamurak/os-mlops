from os import environ, listdir, path, unlink
from shutil import move, rmtree

from yolov5.train import run


def train_model(
        data_folder='./data', batch_size=0, epochs=0, base_model='yolov5m',
        configuration_path='configuration-local.yaml'):
    print('training model')

    batch_size = batch_size or int(environ.get('batch_size', 4))
    epochs = epochs or int(environ.get('epochs', 2))
    base_model = base_model or environ.get('base_model', 'yolov5m')

    _clean_folder('yolov5/runs')
    run(
        data=configuration_path,
        weights=f'{base_model}.pt',
        epochs=epochs,
        batch_size=batch_size,
        freeze=[10],
        cache='disk',
        exists_ok=True
    )

    move('yolov5/runs/train/exp/weights/best.pt', 'model.pt')

    print('model training done')


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
    train_model(
        data_folder='/data', configuration_path='configuration-pipeline.yaml'
    )
