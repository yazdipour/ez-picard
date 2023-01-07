import os
import shutil


def delete_folders(path, dir_to_keep):
    # get a list of all the subdirectories in the specified path
    subdirectories = [d for d in os.listdir(
        path) if os.path.isdir(os.path.join(path, d))]
    for subdir in subdirectories:
        if subdir == dir_to_keep:
            continue
        subdir_path = os.path.join(path, subdir)
        shutil.rmtree(subdir_path)
