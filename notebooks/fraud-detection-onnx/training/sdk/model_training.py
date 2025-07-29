from kfp.dsl import (component, Dataset, Input, Metrics,
                     Model, Output)


runtime_image = 'quay.io/mmurakam/runtimes:fraud-detection-v2.6.1'


@component(base_image=runtime_image)
def train_model(
        epoch_count: int, learning_rate: float,
        training_samples: Input[Dataset], training_labels: Input[Dataset],
        model: Output[Model], metrics: Output[Metrics],
        training_history: Output[Dataset]):
    from os import environ
    from pickle import dump, load

    environ['CUDA_VISIBLE_DEVICES'] = '-1'

    from keras.models import Sequential
    from keras.layers import Dense
    from keras.optimizers import Adam
    from onnx import save
    from tf2onnx import convert

    print('training model')

    with open(training_samples.path, 'rb') as samples_file:
        Xsm_train = load(samples_file)
    with open(training_labels.path, 'rb') as labels_file:
        ysm_train = load(labels_file)

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
    training_metrics = oversample_model.fit(
        Xsm_train,
        ysm_train,
        validation_split=0.2,
        batch_size=300,
        epochs=epoch_count,
        shuffle=True,
        verbose=2,
    )
    metrics_history = training_metrics.history
    accuracy = metrics_history['accuracy'][-1]
    metrics.log_metric('accuracy', accuracy)
    metrics_history['learning_rate'] = learning_rate
    metrics_history['epoch_count'] = epoch_count
    with open(training_history.path, 'wb') as outputfile:
        dump(metrics_history, outputfile)

    onnx_model, _ = convert.from_keras(oversample_model)
    save(onnx_model, model.path)