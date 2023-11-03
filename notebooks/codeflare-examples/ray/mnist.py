# Copyright 2022 IBM, Red Hat
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# In[]
from os import environ
from datetime import datetime

from boto3 import client
import torch
from pytorch_lightning import LightningModule, Trainer
from pytorch_lightning.callbacks.progress import TQDMProgressBar
from torch import nn
from torch.nn import functional as F
from torch.utils.data import DataLoader, random_split
from torchmetrics import Accuracy
from torchvision import transforms
from torchvision.datasets import MNIST

PATH_DATASETS = environ.get("PATH_DATASETS", ".")
BATCH_SIZE = 256 if torch.cuda.is_available() else 64
model_object_prefix = environ.get('model_object_prefix', 'model')
s3_endpoint_url = environ.get('AWS_S3_ENDPOINT')
s3_access_key = environ.get('AWS_ACCESS_KEY_ID')
s3_secret_key = environ.get('AWS_SECRET_ACCESS_KEY')
s3_bucket_name = environ.get('AWS_S3_BUCKET')
hidden_size = int(environ.get('hidden_size', 64))
max_epochs = int(environ.get('max_epochs', 10))

print("prior to running the trainer")
print("MASTER_ADDR: is ", environ.get("MASTER_ADDR"))
print("MASTER_PORT: is ", environ.get("MASTER_PORT"))


class LitMNIST(LightningModule):
    def __init__(self, data_dir=PATH_DATASETS, hidden_size=64, learning_rate=2e-4):
        super().__init__()

        # Set our init args as class attributes
        self.data_dir = data_dir
        self.hidden_size = hidden_size
        self.learning_rate = learning_rate

        # Hardcode some dataset specific attributes
        self.num_classes = 10
        self.dims = (1, 28, 28)
        channels, width, height = self.dims
        self.transform = transforms.Compose(
            [
                transforms.ToTensor(),
                transforms.Normalize((0.1307,), (0.3081,)),
            ]
        )

        # Define PyTorch model
        self.model = nn.Sequential(
            nn.Flatten(),
            nn.Linear(channels * width * height, hidden_size),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_size, hidden_size),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_size, self.num_classes),
        )
        self.example_input_array = torch.randn(channels, width, height)

        self.val_accuracy = Accuracy()
        self.test_accuracy = Accuracy()

    def forward(self, x):
        x = self.model(x)
        return F.log_softmax(x, dim=1)

    def training_step(self, batch, batch_idx):
        x, y = batch
        logits = self(x)
        loss = F.nll_loss(logits, y)
        return loss

    def validation_step(self, batch, batch_idx):
        x, y = batch
        logits = self(x)
        loss = F.nll_loss(logits, y)
        preds = torch.argmax(logits, dim=1)
        self.val_accuracy.update(preds, y)

        # Calling self.log will surface up scalars for you in TensorBoard
        self.log("val_loss", loss, prog_bar=True)
        self.log("val_acc", self.val_accuracy, prog_bar=True)

    def test_step(self, batch, batch_idx):
        x, y = batch
        logits = self(x)
        loss = F.nll_loss(logits, y)
        preds = torch.argmax(logits, dim=1)
        self.test_accuracy.update(preds, y)

        # Calling self.log will surface up scalars for you in TensorBoard
        self.log("test_loss", loss, prog_bar=True)
        self.log("test_acc", self.test_accuracy, prog_bar=True)

    def configure_optimizers(self):
        optimizer = torch.optim.Adam(self.parameters(), lr=self.learning_rate)
        return optimizer

    ####################
    # DATA RELATED HOOKS
    ####################

    def prepare_data(self):
        # download
        print("Downloading MNIST dataset...")
        MNIST(self.data_dir, train=True, download=True)
        MNIST(self.data_dir, train=False, download=True)

    def setup(self, stage=None):
        # Assign train/val datasets for use in dataloaders
        if stage == "fit" or stage is None:
            mnist_full = MNIST(self.data_dir, train=True, transform=self.transform)
            self.mnist_train, self.mnist_val = random_split(mnist_full, [55000, 5000])

        # Assign test dataset for use in dataloader(s)
        if stage == "test" or stage is None:
            self.mnist_test = MNIST(
                self.data_dir, train=False, transform=self.transform
            )

    def train_dataloader(self):
        return DataLoader(self.mnist_train, batch_size=BATCH_SIZE)

    def val_dataloader(self):
        return DataLoader(self.mnist_val, batch_size=BATCH_SIZE)

    def test_dataloader(self):
        return DataLoader(self.mnist_test, batch_size=BATCH_SIZE)


def run_training():
    print(f'instantiating model with hidden size: {hidden_size}')

    model = LitMNIST(hidden_size=hidden_size)

    print("GROUP: ", int(environ.get("GROUP_WORLD_SIZE", 1)))
    print("LOCAL: ", int(environ.get("LOCAL_WORLD_SIZE", 1)))
    print(f'max epochs: {max_epochs}')

    # Initialize a trainer
    trainer = Trainer(
        accelerator="auto",
        # devices=1 if torch.cuda.is_available() else None,  # limiting got iPython runs
        max_epochs=max_epochs,
        callbacks=[TQDMProgressBar(refresh_rate=20)],
        num_nodes=int(environ.get("GROUP_WORLD_SIZE", 1)),
        devices=int(environ.get("LOCAL_WORLD_SIZE", 1)),
        strategy="ddp",
    )

    print('starting training')

    # Train the model ⚡
    trainer.fit(model)

    print('finished training')

    return model


def export_model(model):
    filepath = 'model.onnx'

    print(f'exporting model to {filepath}')

    model.to_onnx(filepath, export_params=True)

    print('model export complete')

    return filepath


def upload_model(model_filepath, model_object_prefix='model', version=''):
    s3_client = _initialize_s3_client(
        s3_endpoint_url=s3_endpoint_url,
        s3_access_key=s3_access_key,
        s3_secret_key=s3_secret_key
    )
    model_object_name = _generate_model_name(
        model_object_prefix, version=version
    )
    _do_upload(s3_client, model_object_name)

    model_object_name_latest = _generate_model_name(
        model_object_prefix, 'latest'
    )
    _do_upload(s3_client, model_object_name_latest, model_filepath)


def _initialize_s3_client(s3_endpoint_url, s3_access_key, s3_secret_key):
    print('initializing S3 client')
    s3_client = client(
        's3', aws_access_key_id=s3_access_key,
        aws_secret_access_key=s3_secret_key,
        endpoint_url=s3_endpoint_url,
    )
    return s3_client


def _generate_model_name(model_object_prefix, version=''):
    version = version if version else _timestamp()
    model_name = f'{model_object_prefix}-{version}.onnx'
    return model_name


def _timestamp():
    return datetime.now().strftime('%y%m%d%H%M')


def _do_upload(s3_client, object_name, filepath='model.onnx'):
    print(f'uploading model to {object_name}')
    try:
        s3_client.upload_file(filepath, s3_bucket_name, object_name)
    except:
        print(f'S3 upload to bucket {s3_bucket_name} at {s3_endpoint_url} failed!')
        raise
    print(f'model uploaded and available as "{object_name}"')


if __name__ == '__main__':
    model = run_training()
    model_filepath = export_model(model)
    upload_model(model_filepath, model_object_prefix)
