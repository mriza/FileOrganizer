import os
import shutil
import threading
import tkinter as tk
from tkinter import filedialog, ttk, messagebox

# Common file extensions to list as options
FILE_TYPES = [
    '.txt', '.pdf', '.docx', '.md', '.py', '.csv', '.json', '.xml'
]

class FileContextReader(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('File Context Reader')
        self.geometry('600x400')

        # Variables for GUI state
        self.folder_path = tk.StringVar()
        self.extension_vars = {ext: tk.BooleanVar(value=False) for ext in FILE_TYPES}
        self.select_all_var = tk.BooleanVar(value=False)
        self.include_subfolders = tk.BooleanVar(value=True)
        # Option to categorize files based on their content
        self.create_categories = tk.BooleanVar(value=False)

        self._build_gui()

    def _build_gui(self):
        frame = ttk.Frame(self)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Folder selection
        folder_frame = ttk.LabelFrame(frame, text='Folder Selection')
        folder_frame.pack(fill=tk.X, pady=5)
        ttk.Button(folder_frame, text='Select Folder', command=self._select_folder).pack(side=tk.LEFT)
        ttk.Label(folder_frame, textvariable=self.folder_path).pack(side=tk.LEFT, padx=5)

        # File type selection
        types_frame = ttk.LabelFrame(frame, text='File Types')
        types_frame.pack(fill=tk.X, pady=5)
        ttk.Checkbutton(types_frame, text='All', variable=self.select_all_var, command=self._toggle_all).grid(row=0, column=0, sticky=tk.W)
        for i, ext in enumerate(FILE_TYPES, start=1):
            ttk.Checkbutton(types_frame, text=ext, variable=self.extension_vars[ext]).grid(row=i//4, column=i%4, sticky=tk.W)

        # Options
        options_frame = ttk.LabelFrame(frame, text='Options')
        options_frame.pack(fill=tk.X, pady=5)
        ttk.Checkbutton(options_frame, text='Read Subfolders', variable=self.include_subfolders).pack(anchor=tk.W)
        ttk.Checkbutton(options_frame, text='Categorize by Content', variable=self.create_categories).pack(anchor=tk.W)

        # Controls frame holds the start button so it is always visible
        controls_frame = ttk.Frame(frame)
        controls_frame.pack(fill=tk.X, pady=5)
        ttk.Button(controls_frame, text='Start', command=self._start_thread).pack()

        # Progress information
        progress_frame = ttk.LabelFrame(frame, text='Progress')
        progress_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        self.progress = ttk.Progressbar(progress_frame, orient='horizontal', mode='determinate')
        self.progress.pack(fill=tk.X, padx=5, pady=5)
        self.log = tk.Text(progress_frame, height=10)
        self.log.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def _toggle_all(self):
        state = self.select_all_var.get()
        for var in self.extension_vars.values():
            var.set(state)

    def _select_folder(self):
        path = filedialog.askdirectory()
        if path:
            self.folder_path.set(path)

    def _start_thread(self):
        if not self.folder_path.get():
            messagebox.showerror('Error', 'Please select a folder first.')
            return
        thread = threading.Thread(target=self._process_files)
        thread.start()

    def _gather_files(self):
        selected_exts = [ext for ext, var in self.extension_vars.items() if var.get()]
        if not selected_exts and not self.select_all_var.get():
            messagebox.showerror('Error', 'Select at least one file type or choose All.')
            return []
        file_list = []
        for root, dirs, files in os.walk(self.folder_path.get()):
            if not self.include_subfolders.get() and root != self.folder_path.get():
                continue
            for name in files:
                if self.select_all_var.get() or os.path.splitext(name)[1] in selected_exts:
                    file_list.append(os.path.join(root, name))
        return file_list

    def _process_files(self):
        files = self._gather_files()
        if not files:
            return
        self.progress.config(maximum=len(files))
        self.progress['value'] = 0
        self.log.delete('1.0', tk.END)

        for idx, path in enumerate(files, start=1):
            try:
                with open(path, 'r', errors='ignore') as f:
                    content = f.read()
                self._log(f'Read {os.path.basename(path)} ({len(content)} characters)')
                if self.create_categories.get():
                    self._move_to_category(path, content)
            except Exception as e:
                self._log(f'Error reading {path}: {e}')
            self.progress['value'] = idx
        self._log('Completed.')

    def _move_to_category(self, path, content):
        """Move file to a context-based category folder."""
        category = self._detect_category(content)
        target_dir = os.path.join(self.folder_path.get(), f'{category}_files')
        os.makedirs(target_dir, exist_ok=True)
        try:
            shutil.move(path, os.path.join(target_dir, os.path.basename(path)))
            self._log(f'Moved {path} to {target_dir}')
        except Exception as e:
            self._log(f'Error moving {path}: {e}')

    def _detect_category(self, content):
        """Determine category name based on file content."""
        if not content.strip():
            return 'empty'
        if '\x00' in content:
            return 'binary'
        text = content.lower()
        if any(kw in text for kw in ('def ', 'class ', 'import ')):
            return 'code'
        if any(kw in text for kw in ('data', 'value', 'number')):
            return 'data'
        if any(kw in text for kw in ('todo', 'note', 'meeting')):
            return 'notes'
        return 'other'

    def _log(self, message):
        self.log.insert(tk.END, message + '\n')
        self.log.see(tk.END)

if __name__ == '__main__':
    app = FileContextReader()
    app.mainloop()
