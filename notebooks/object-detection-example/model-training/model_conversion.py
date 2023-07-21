from yolov5.export import run


def convert_model(model_file_path='model.pt'):
    print('converting model')

    run(
        weights=model_file_path,
        include=['onnx'],
        imgsz=(640, 640),
        opset=13,
    )

    print('model converted')


if __name__ == '__main__':
    convert_model()
