from os import environ
from shutil import move

from ultralytics import YOLO


def train_model(
        data_folder='./data', batch_size=4, epochs=1, base_model='yolov8n',
        configuration_path='configuration-local.yaml'):
    print('training model')

    batch_size = batch_size or int(environ.get('batch_size', 4))
    epochs = epochs or int(environ.get('epochs', 2))
    base_model = base_model or environ.get('base_model', 'yolov8n')

    model = YOLO(f'{base_model}.pt')
    model.train(
        data=configuration_path,
        epochs=epochs,
        batch=batch_size,
        freeze=10,
        cache='disk',
        exist_ok=True
    )

    move('runs/detect/train/weights/best.pt', 'model.pt')

    print('model training done')

    return model


if __name__ == '__main__':
    train_model(
        data_folder='/data', configuration_path='configuration-pipeline.yaml'
    )
