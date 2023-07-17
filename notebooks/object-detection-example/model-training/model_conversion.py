from yolov5.export import run


def convert_model():
    print('converting model')

    run(
        weights='model.pt',
        include=['onnx'],
        imgsz=(640, 640),
        opset=16,
    )

    print('model converted')


if __name__ == '__main__':
    convert_model()
