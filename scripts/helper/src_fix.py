"""
Used to correct pip installing editable directories
bearing dashes instead of underscores
"""
import os
import shutil



def handle_error(func, path, exc_info):
    os.chmod(path, 0o755)
    os.utime(path, None)
    os.unlink(path)


if 'VIRTUAL_ENV' not in os.environ:
    raise Exception('No virtual environment active!')


path = f'{os.environ["VIRTUAL_ENV"]}\\src'
for subdir in os.listdir(path):
    old_path = f'{path}\\{subdir}'

    # Make path relative
    old_path = old_path.replace(f'{os.getcwd()}\\', '')

    if '-' in subdir:
        new_path = old_path.replace('-', '_')

        # Check if old path exists, and delete new path if so
        if os.path.exists(old_path) and os.path.exists(new_path):
            shutil.rmtree(new_path, onerror=handle_error)
            if os.path.exists(new_path):
                raise FileExistsError(f'Failed to remove {new_path}')

        print(f'Renaming {old_path} to {new_path}')
        os.rename(old_path, new_path)
