from numpy import argmax, array, load
from onnxruntime import InferenceSession
from pandas import DataFrame


def predict(data_folder='./data'):
    print('Commencing offline scoring.')

    X = load(f'{data_folder}/samples.npy').astype('float32')

    session = InferenceSession('model.onnx')
    raw_results = session.run([], {'dense_input': X})[0]

    results = argmax(raw_results, axis=1)
    class_map_array = array(['no fraud', 'fraud'])
    mapped_results = class_map_array[results]

    print(f'Scored data set. Writing report.')

    column_names = [f'V{i}' for i in range(1, 31)]
    report = DataFrame(X, columns=column_names)
    report.insert(0, 'Prediction', mapped_results)

    report.to_csv(f'{data_folder}/predictions.csv')

    print('Wrote report. Offline scoring complete.')


if __name__ == '__main__':
    predict(data_folder='/data')
