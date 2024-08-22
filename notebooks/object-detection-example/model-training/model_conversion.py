from ultralytics import YOLO


def convert_model(model_file_path='model.pt'):
    print('converting model')

    model = YOLO(model_file_path)
    model.export(format='onnx', imgsz=640, opset=13)
    model.save('model.onnx')

    print('model converted')


if __name__ == '__main__':
    convert_model()
