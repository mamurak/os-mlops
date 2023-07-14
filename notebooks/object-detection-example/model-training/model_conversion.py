from yolov5.export import run


def validate_model():
    print('validating model')

    run(
        weights='yolov5/runs/train/exp/weights/best.pt',
        include='onnx',
        imgsz=(640, 640),
        opset=16,
    )

    print('model validated')


if __name__ == '__main__':
    validate_model()
