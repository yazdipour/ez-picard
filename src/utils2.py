import os


def delete_files(path, filename_to_keep):
    # Delete all the files in the directory except for "test.sqlite"
    [os.remove(f'{path}/{file}')
     for file in os.listdir(path) if file != filename_to_keep]
