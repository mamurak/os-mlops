from os import environ

environ['CUDA_VISIBLE_DEVICES'] = '-1'

from keras.models import Sequential
from keras.layers.core import Dense
from keras.optimizers import Adam
from numpy import load
from onnx import save
from tf2onnx import convert


def train_model(data_folder='./data'):
    print('training model')

    epoch_count = int(environ.get('epoch_count', '20'))
    learning_rate = float(environ.get('learning_rate', '0.001'))

    Xsm_train = load(f'{data_folder}/training_samples.npy')
    ysm_train = load(f'{data_folder}/training_labels.npy')
    n_inputs = Xsm_train.shape[1]

    oversample_model = Sequential([
        Dense(n_inputs, input_shape=(n_inputs, ), activation='relu'),
        Dense(32, activation='relu'),
        Dense(2, activation='softmax'),
    ])
    oversample_model.compile(
        Adam(learning_rate=learning_rate),
        loss='sparse_categorical_crossentropy',
        metrics=['accuracy'],
    )
    oversample_model.fit(
        Xsm_train,
        ysm_train,
        validation_split=0.2,
        batch_size=300,
        epochs=epoch_count,
        shuffle=True,
        verbose=2,
    )
    onnx_model, _ = convert.from_keras(oversample_model)
    save(onnx_model, 'model.onnx')


if __name__ == '__main__':
    train_model(data_folder='/data')
