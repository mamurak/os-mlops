from yolov5.train import run


def train_model():
    print('training model')

    run(
        data='configuration.yaml',
        weights='yolov5m.pt',
        epochs=50,
        batch_size=256,
        freeze=[10],
        cache='disk',
    )

    print('model training done')


if __name__ == '__main__':
    train_model()
