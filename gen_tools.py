from PyQt5.QtWidgets import QFrame
import os
import time
import traceback


class Tools:
    @staticmethod
    def msg_creator(*args):
        max_msg_length = max([len(arg) for arg in args])
        border = '-' * max_msg_length
        return '\n'.join([arg for arg in [border, *args, border]]) + '\n'

    @staticmethod
    def time_func(func):
        def timer(*args, **kwargs):
            start = time.process_time()
            try:
                result = func(*args, **kwargs)
            except Exception as e:
                print(e)
                print(traceback.print_exc())
            else:
                end = time.process_time()
                print(f"Time elapsed for {func.__name__}: {round(end - start, 3)} seconds\n")
                return result

        return timer

    @staticmethod
    def get_file_count(path, ignored_dirs):
        return sum(
            [len(files) if root.replace("\\", "/") not in ignored_dirs else -len(files) for root, _, files in
             os.walk(path)])
        # Root is formatted weirdly in os.walk().

    @staticmethod
    def get_base_folder(main_path, path):
        replaced_path = path.replace(main_path, "")[1:]
        # Remove empty text.
        base_split_path = [item for item in os.path.split(replaced_path) if item != '']
        return base_split_path[0]

    @staticmethod
    def counter_incrementor(counter, categ, amount):
        # Counter is a default dict with Counter
        counter[categ] += amount
        return categ

    @staticmethod
    def create_seperator():
        # From user kaveish.
        # https://stackoverflow.com/questions/10053839/how-does-designer-create-a-line-widget/10469098
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        return line

    @staticmethod
    def shorten_path(folder_path, show_dirs=1):
        split_path, folder = os.path.split(folder_path)
        path_drive = os.path.splitdrive(split_path)[0]
        secondary_dirs = []
        for i in range(show_dirs):
            secondary_split, secondary_dir = os.path.split(split_path)
            if secondary_dir == "":
                break
            secondary_dirs.append(secondary_dir)
            split_path = secondary_split
        return f"{path_drive}/.../{'/'.join(reversed(secondary_dirs))}/{folder}"

