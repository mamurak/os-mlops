from os import listdir, path, unlink
from shutil import rmtree

from caikit_nlp.text_generation import TextGeneration


models_cache_folder = '/models'


def convert():
    old_model = TextGeneration.bootstrap(models_cache_folder)
    _clean_folder(models_cache_folder)
    old_model.save(models_cache_folder)


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