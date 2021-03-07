import os
import re
import shutil
import mimetypes
import logging
from datetime import datetime
from collections import Counter, defaultdict

from main_stats import FileDf, Plotter
from gui_stats import StatsUI
from gen_tools import Tools


class FolderFxs:
    FILE_MTYPE_KEY = {'application':
                          ({'subtype_patterns': ('ms_excel', 'spreadsheet'), 'categ': 'Spreadsheet'},
                           {'subtype_patterns': ('text', 'msword', 'wordprocessingml'), 'categ': 'Word Document'},
                           {'subtype_patterns': ('presentation', 'ms-powerpoint', 'presentationml'),
                            'categ': 'Presentation'},
                           {'subtype_patterns': ('pdf'), 'categ': 'PDF'},
                           {'subtype_patterns': (
                               'x-7z-compressed', 'zip', 'x-tar', 'vnd.rar', 'java-archive', 'gzip', 'x-bzip',
                               'x-bzip2', 'x-freearc'),
                               'categ': 'Archive'}),
                      'audio': {'subtype_patterns': (), 'categ': 'Audio'},
                      'video': {'subtype_patterns': (), 'categ': 'Video'},
                      'image': {'subtype_patterns': (), 'categ': 'Image'},
                      'text': {'subtype_patterns': (), 'categ': 'Text'}}

    TIME_MODES = {'Time Created': lambda file: os.stat(file).st_ctime,
                  'Time Modified': lambda file: os.stat(file).st_mtime,
                  'Time Accessed': lambda file: os.stat(file).st_atime}
    TIME_INTERVALS = {'Day': lambda datetime_obj: f'{datetime_obj.month}_{datetime_obj.day}_{datetime_obj.year}',
                      'Month': lambda datetime_obj: f'{datetime_obj.month}_{datetime_obj.year}',
                      'Year': lambda datetime_obj: f'{datetime_obj.year}'}

    def __init__(self, sort_settings):
        # Dict of tuples where index 0 is the order pos and index 1 holds the desired settings.
        self.sort_settings = sort_settings
        self.sort_results = defaultdict(Counter)

        # (pos, {Time Mode: ?, Time Interval: ?, Date Range: {Date start: ?, date end: ?})})
        if 'Date' in sort_settings:
            self.date_settings = sort_settings["Date"][1]

        # (pos, {Desc: ['Spreadsheet', 'Word Document', 'Presentation', 'PDF', 'Audio', 'Video', 'Image', 'Text', 'Archive']})
        if 'File Type' in sort_settings:
            self.ftype_settings = list(sort_settings['File Type'][1].values())[1]

        # (pos, {'Folder Name': [keywords], 'Ungrouped Keywords': []})
        if 'Keyword' in sort_settings:
            self.keyword_settings = sort_settings['Keyword'][1]

    def _date_folder(self, filename):
        datetime_obj = datetime.fromtimestamp(self.TIME_MODES[self.date_settings['Time Mode']](filename))

        start = datetime.strptime(self.date_settings['Date Range']['Starting Date'], "%m-%d-%Y")
        end = datetime.strptime(self.date_settings['Date Range']['Ending Date'], "%m-%d-%Y")

        if start < datetime_obj < end:
            self.sort_results['Valid Date']['Valid'] += 1
            return self.TIME_INTERVALS[self.date_settings['Time Interval']](datetime_obj)
        else:
            # Date not within range.
            self.sort_results['Valid Date']['Invalid'] += 1
            return None

    def _file_folder(self, filename):
        mtype, subtype = mimetypes.guess_type(filename)[0].split('/')
        # Ex. Word doc - ['application', 'msword']

        if isinstance(ftype_descs := self.FILE_MTYPE_KEY.get(mtype, None), tuple):
            for ftype in ftype_descs:
                # If any patterns in the looping ftype are found in the mimetypes subtype
                # - and -
                # the category is in the desired ftypes.
                # Return the categ as a string to be made into a folder.
                if any(re.search(pattern, subtype) for pattern in ftype['subtype_patterns']) and \
                        ftype['categ'] in self.ftype_settings:
                    self.sort_results["File Types"][ftype['categ']] += 1
                    return ftype['categ']
        elif isinstance(ftype_descs, dict):
            if ftype_descs['categ'] in self.ftype_settings:
                self.sort_results["File Types"][ftype_descs['categ']] += 1
                return ftype_descs['categ']
        else:
            if ftype_descs is None:
                raise Exception("Unknown mimetype.")
            # Custom types
            for ftype in self.ftype_settings:
                if re.search(ftype, os.path.splitext(filename)[1]):
                    self.sort_results["File Types"][ftype] += 1
                    return ftype

    def _keyword_folder(self, filename):
        for folder, words in self.keyword_settings.items():
            # Increments self.file_counter if match found and returns keyword. Othewise, returns None.
            word_finder = [Tools.counter_incrementor(self.sort_results['Keywords'], keyword, 1)
                           for keyword in words
                           if re.search(keyword, filename, re.IGNORECASE)]
            if folder != 'Ungrouped Keywords':
                # If any item in list comp has value, return folder.
                if any(word_finder):
                    return folder
            elif folder == 'Ungrouped Keywords':
                # If a file name contains multiple matching keywords, the last keyword will contain the file.
                # This is because any found keywords will be nested into a single path and the LAST keyword is
                # returned as the destination in _create_folders
                return word_finder

    def _order_fxs(self):
        # Callable functions.
        folder_names = {'Date': self._date_folder,
                        'File Type': self._file_folder,
                        'Keyword': self._keyword_folder}

        # Order of function operations.
        return [folder_names.get(option[0]) for option in sorted(self.sort_settings.items(), key=lambda x: x[1])]


class FileSort(FileDf):

    def __init__(self, path=None):
        super().__init__()
        self.path = path
        self.counter = defaultdict(Counter)
        self._shutdown = 0  # 0 for non-issue
        if path is not None:
            os.chdir(self.path)

        print(Tools.msg_creator(f"Current directory is {os.getcwd()}."))

    def _create_folders(self, folder_order, dest):
        final_paths = []
        if all(option is None or option == [] for option in folder_order):
            # All options unfilled. Return None.
            return None
        else:
            for folder in folder_order:
                if isinstance(folder, list):
                    for item in folder:
                        if item is not None:
                            dest = os.path.join(dest, item)
                            final_paths.append(dest)
                else:
                    if folder is not None:
                        # Start path needs to be changed to nest dirs as we loop through all dir names
                        # and build on previous dir (start_path) made.
                        dest = os.path.normpath(os.path.join(dest, folder))
                        final_paths.append(dest)

            for path in final_paths:
                if not os.path.exists(path):
                    logging.info(f"Folder ({os.path.normpath(path)}) created.")
                    os.makedirs(path)
                    self.counter['Sorted']['Folders'] += 1

            # Last entry in final_paths will be destination.
            # Filenames with multiple keywords will be placed in the last keyword path.
            return final_paths[-1]

    @staticmethod
    def _ignore_check(ign):
        if isinstance(ign, list):
            return set(ign)
        elif isinstance(ign, str):
            return {ign}
        else:
            return {None}

    # TODO: Implement show data functionality
    @Tools.time_func
    def sort_files(self, sort_settings, progress_sig=None, fin_sig=None,
                   ignore=None, in_place=False, show_data=False, log_sort=False):

        if log_sort:
            print('Logging sort.')
            sort_date = datetime.strftime(datetime.today(), "%m_%d_%y_%H_%M_%S")
            logging.basicConfig(filename=f"sort{sort_date}.log", filemode='w',
                                format="%(asctime)s - %(message)s", datefmt="%b-%d-%y %H:%M:%S",
                                level=logging.INFO)
            logging.info(f"Sort started in ({os.path.normpath(self.path)}).")
            logging.info(f"Parameters: {dict(sort_settings)}")
            logging.info(f"Ignored folders: {ignore}")
            logging.info(f"Sorting in-place: {in_place}\n")

        ignore = self._ignore_check(ignore)
        folder_fxs = FolderFxs(sort_settings)
        folder_order = folder_fxs._order_fxs()

        for root, dirs, files in os.walk(self.path, topdown=False):
            root = os.path.normpath(root)
            destination = (root if in_place else self.path)
            if any([os.path.samefile(item, root) if item else False for item in ignore]):
                logging.info(f'*Skipped sorting ({root}).')
            else:
                for file in files:
                    if self._shutdown == 1:
                        break
                    if show_data:
                        self.store_file_properties(os.path.join(root, file), root.replace(self.path, ""))

                    # Folder order is a list of folder names created from the folder functions.
                    # create_folders creates a list of folders (+paths) and returns the last folder as the destination path.
                    folder_names = [fx(filename=os.path.join(root, file)) for fx in folder_order]
                    final_dir = self._create_folders(folder_order=folder_names, dest=destination)

                    # Avoid trying to move files from the currently checking root dir to itself
                    # and if no folder created
                    # and if file exists in final_dir.
                    if root != final_dir and final_dir is not None and not os.path.exists(os.path.join(final_dir, file)):
                        # Ignored and no log made if logging.basicConfig not set. Can just leave in w/o conditional
                        logging.info(f"({file}) moved from ({root}) to ({final_dir})")
                        shutil.move(os.path.join(root, file), final_dir)
                        self.counter['Sorted']['Files'] += 1

                    # Counter which is used to signal that a file has been sorted and ProgressBar must be updated.
                    self.counter['Checked']['Files'] += 1
                    if progress_sig:
                        progress_sig.emit(self.counter['Checked']['Files'])

        # Signal that sorting is finished to ProgressBar
        # fin_sig(1) - emergency shutdown, fin_sig(0) - normal shutdown
        shutdown_msg = {1: "Sort ended prematurely.", 0: "Sort successfully finished."}
        if fin_sig:
            fin_sig.emit(self._shutdown)
        if log_sort:
            logging.info(shutdown_msg[self._shutdown])
            logging.info(f"{dict(self.counter)}")
            logging.shutdown()
        if show_data:
            graph = Plotter(df=self.df, counter=folder_fxs.sort_results, total_chkd=self.counter['Checked']['Files'])
            # graph_ui = StatsUI()
            # graph.csize_time()
            # graph.file_ext()

            graph.file_dist(self.path)
            # graph.file_types()
            # graph.file_time_valid()

        # Reset dataframe, shutdown, and counter.
        self._shutdown = 0
        super().__init__()
        self.counter = defaultdict(Counter)

    @Tools.time_func
    def unpack_folders(self, dest, ignore=None):
        ignore = self._ignore_check(ignore)

        for root, dirs, files in os.walk(self.path, topdown=False):
            if any([os.path.samefile(item, root) if item else False for item in ignore]):
                print(f'*Skipped unpacking {root}.\n')
            else:
                if root != self.path:
                    for file in files:
                        shutil.move(os.path.join(root, file), dest)
                        self.counter['Unpacked']['Files'] += 1
                    # os.rmdir only removes empty dirs.
                    os.rmdir(root)
                    self.counter['Unpacked']['Folders'] += 1

    def __str__(self):
        if self.counter == {}:
            return Tools.msg_creator("No files or folders altered.")
        else:
            return Tools.msg_creator(f"{dict(self.counter)}")


if __name__ == '__main__':
    """
    --------------------------------------------------------------------------
    Can sort by three ways, 
        time_(a - accessed, m - modified, c - created)day, month, or year, 
            ex. time_amonth, sorting by the month the file was last accessed
        file_type,
            ex. Mimetypes (audio, application, image, video, text, etc.),
        phrase_(any number of items delimited by '+')
        
    Ignore folders in sorting or unpacking with ignore argument.
        Must be foldernames in a list or single foldername.
    --------------------------------------------------------------------------
    """

    """
    SORT 1 - 11 files. All images. Ignore folder, "EEMB 157CL Project".
    """
    # start_folder = os.path.join(os.getcwd(), 'Microscope Stuff')

    # sort_1 = FileSort(path=start_folder)
    # sort_1.sort_files(sort_settings=['file_type', 'phrase_Worm+Euglena+Crustacean'], ignore=['EEMB 157CL Project'])
    # sort_1.unpack_folders(dest=start_folder, ignore=['EEMB 157CL Project'])
    # print(sort_1)

    """
    SORT 1 - 532 files. Image and video.
    """
    start_folder = os.path.join(os.getcwd(), 'Pictures')

    settings = {
        'Keyword': (
            1, {'Non-Pictures': ['Flute', 'Letter', 'Humidity'], 'Ungrouped Keywords': ['conidia', 'jar', 'view']})}
    sort_2 = FileSort(path=start_folder)
    sort_2.sort_files(sort_settings=settings)
    # sort_2.unpack_folders(dest=start_folder)
    print(sort_2)
