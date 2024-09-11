from ultralytics import YOLO


def convert_model(model_file_path='model.pt', opset=13):
    print('converting model')

    model = YOLO(model_file_path)
    model.export(format='onnx', imgsz=640, opset=opset)

    print('model converted')


if __name__ == '__main__':
    convert_model()
