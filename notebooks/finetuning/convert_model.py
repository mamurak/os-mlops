from os import listdir, path, unlink
from shutil import rmtree

from caikit_nlp.modules.text_generation import TextGeneration


models_cache_folder = '/models'


def convert():
    model = TextGeneration.bootstrap(f'{models_cache_folder}/finetuned')
    # _clean_folder(models_cache_folder)
    model.save(f'{models_cache_folder}/caikit')


def _clean_folder(folder):
    print(f'Cleaning folder {folder}')

    for filename in listdir(folder):
        file_path = path.join(folder, filename)
        try:
            if path.isfile(file_path) or path.islink(file_path):
                unlink(file_path)
            elif path.isdir(file_path):
                rmtree(file_path)
        except Exception as e:
            print(f'Failed to delete {file_path}. Reason: {e}')


if __name__ == '__main__':
    convert()