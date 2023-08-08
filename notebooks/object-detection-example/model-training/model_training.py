from os import environ
from shutil import move

from yolov5.train import run


def train_model(
        data_folder='./data', batch_size=0, epochs=0, base_model='yolov5m'):
    print('training model')

    batch_size = batch_size or int(environ.get('batch_size', 4))
    epochs = epochs or int(environ.get('epochs', 2))
    base_model = base_model or environ.get('base_model', 'yolov5m')

    run(
        data='configuration.yaml',
        weights=f'{base_model}.pt',
        epochs=epochs,
        batch_size=batch_size,
        freeze=[10],
        cache='disk',
    )

    move('yolov5/runs/train/exp/weights/best.pt', 'model.pt')

    print('model training done')


if __name__ == '__main__':
    train_model(data_folder='/data')
