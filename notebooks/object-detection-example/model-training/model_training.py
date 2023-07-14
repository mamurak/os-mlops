from os import link, path
from pathlib import Path

from yolov5.train import run


def train_model(data_folder='./data'):
    print('training model')

    run(
        data='configuration.yaml',
        weights='yolov5m.pt',
        epochs=2,
        batch_size=2,
        freeze=[10],
        cache='disk',
    )

    print('model training done')


if __name__ == '__main__':
    train_model(data_folder='/data')
