import os
from os import environ, chmod, listdir, mkdir, path, unlink, walk
from shutil import chown, rmtree
import stat

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig


models_cache_folder = '/models'
model_id = environ.get('hf_model_id', 'Trelis/Llama-2-7b-chat-hf-sharded-bf16')
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16
)


def load_artifacts():
    _clean_folder(models_cache_folder)
    _create_folders(models_cache_folder)
    _download_files(models_cache_folder)
    _update_permissions(models_cache_folder)


def _clean_folder(folder):
    print(f'Cleaning folder {folder}')

    if path.isdir(folder):
        for filename in listdir(folder):
            file_path = path.join(folder, filename)
            try:
                if path.isfile(file_path) or path.islink(file_path):
                    unlink(file_path)
                elif path.isdir(file_path):
                    rmtree(file_path)
            except Exception as e:
                print(f'Failed to delete {file_path}. Reason: {e}')


def _create_folders(folder):
    for subfolder in ['raw', 'adapter', 'finetuned']:
        mkdir(f'{folder}/{subfolder}')


def _download_files(folder):
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForCausalLM.from_pretrained(
        model_id, quantization_config=bnb_config, device_map={"": 0}
    )
    model.save_pretrained(folder)
    tokenizer.save_pretrained(folder)


def _update_permissions(folder):
    print(f'Updating permissions within {folder}')
    for dirpath, dirnames, filenames in walk(folder):
        print(f'Applying permissions to {dirpath}')
        try:
            chown(dirpath, group=0)
            chmod(
                dirpath, os.stat(dirpath).st_mode | stat.S_IRGRP | stat.S_IWGRP
            )
        except PermissionError:
            print(f'Unable to change group ownership of {dirpath}. '
                  f'Skipping folder.')

        for filename in filenames:
            filepath = path.join(dirpath, filename)
            print(f'Applying permissions to {filepath}')
            try:
                chown(filepath, group=0)
                chmod(
                    filepath,
                    os.stat(filepath).st_mode | stat.S_IRGRP | stat.S_IWGRP
                )
            except PermissionError:
                print(f'Unable to change permissions of {filepath}. '
                      f'Skipping file.')


if __name__ == '__main__':
    load_artifacts()