import os
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
from itertools import accumulate
from collections import defaultdict, Counter

from gen_tools import Tools
# pd.set_option("display.max_rows", None, "display.max_columns", None)


class FileDf:

    def __init__(self):
        self.df = pd.DataFrame(columns=['Filename',
                                        'Folder',
                                        'Size',
                                        'Time Last Accessed', 'Time Last Modified', 'Time Created'])

    @staticmethod
    def convert_time(timestamp):
        return datetime.fromtimestamp(timestamp)

    @staticmethod
    def convert_bytes(time_bytes, size='MB'):
        sizes = {'KB': 1, 'MB': 2, 'GB': 3}
        return round(time_bytes / (1024 ** sizes.get(size, 2)), 2)

    def store_file_properties(self, file_path, folder):
        # TODO: Add reset to df on multiple sorts.
        stat_obj = os.stat(file_path)
        # Enumerates df entries. If no max (start of df) start at 1. Else add 1 on to it.
        self.df.loc[1 if pd.isnull(self.df.index.max()) else self.df.index.max() + 1] = \
            (os.path.split(file_path)[-1],  # file
             folder,  # folder
             self.convert_bytes(stat_obj[6]),  # file size
             *[self.convert_time(timestamp) for timestamp in stat_obj[7:]])  # times


class Plotter:
    """
    Have open a QMessageBox/QWidget with options to chose which plot to show.
    """

    def __init__(self, df, counter, total_chkd):
        self.df = df
        self.counter = {k: dict(v) for k, v in counter.items()}
        self.total_chkd = total_chkd

    @staticmethod
    def val_to_str(vals):
        def converter(pct):  # pct is percent
            total = int(round((pct / 100) * sum(vals)))
            return f"{round(pct, 1)} ({total})"

        return converter

    @staticmethod
    def annotate_bar(axes):
        for item in axes.patches:
            center_bar = item.get_x() + (item.get_width()/2)
            axes.annotate(text=str(item.get_height()), xy=(center_bar, item.get_height()),
                          xytext=(-3, 1), textcoords='offset points')

    def csize_time(self, time_mode='Time Last Modified'):
        """
            Plot line - cumulative size vs. time.
            Allow sorting by file type
        """
        # TODO: Take current Time setting.
        df = self.df.sort_values(time_mode)
        # Add column with prefix sum
        df.loc[:, 'Size'] = list(accumulate(list(df['Size'])))

        df.plot.line(x=time_mode, y='Size', xlabel='Time', ylabel='Size (MB)')
        plt.tight_layout()
        plt.show()

    def file_ext(self):
        """
            Plot pie/bar - file extensions
        """

        all_ext = [os.path.splitext(item)[1] for item in self.df['Filename']]
        ext_types = set(all_ext)
        ext_counts = [all_ext.count(ext) for ext in ext_types]
        ext_total = {ext: num for ext, num in zip(ext_types, ext_counts)}

        self.plot_counter(ext_total, 'pie', ylab='File Extensions')

    """
    Post-sort data.
    """

    def file_dist(self, main_path):
        """
            Plot bar - file distribution in folders.
            Take first nested folder among subfolders
        """
        dir_file_count = Counter()
        for root, dirs, files in os.walk(main_path, topdown=True):
            if root != main_path:
                # Get base path by removing main_path from root and taking first folder after.
                base_path = Tools.get_base_folder(main_path, root)
                dir_file_count[base_path] += len(files)

        # Convert to dict to avoid matplotlib errors with Counter object.
        dir_file_count = dict(dir_file_count)

        self.plot_counter(dir_file_count, 'bar', xlab='Folder Name', ylab='Number of Files')

    def file_types(self):
        """
            Plot bar - file types (sort categories)
        """
        self.plot_counter('File Types', 'pie', ylab='File Types')

    def file_time_valid(self):
        """
            Plot pie - number of files with valid date.
        """
        self.plot_counter('Valid Date', 'pie', ylab='Number of Files')

    def file_keywords(self):
        """
            Plot bar - keyword matches among files
        """
        self.plot_counter('Keywords', 'bar', xlab='Keywords', ylab='Times Found')

    def plot_counter(self, categ, graph_type, xlab=None, ylab=None):
        if isinstance(categ, dict):
            categ_dict = categ
        else:
            categ_dict = self.counter.get(categ, None)
        categ_labels = list(categ_dict.keys())
        categ_counts = list(categ_dict.values())

        df = pd.DataFrame(categ_counts, index=categ_labels, columns=[ylab])
        if graph_type == 'bar':
            ax = df.plot.bar(xlabel=xlab, ylabel=ylab)
            self.annotate_bar(ax)
        elif graph_type == 'pie':
            df.plot.pie(ylabel=ylab, startangle=90, autopct=self.val_to_str(categ_counts))

        plt.tight_layout()
        plt.show()