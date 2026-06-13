import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from typing import Callable
import threading

class LogFileHandler(FileSystemEventHandler):
    def __init__(self, file_path: str, callback: Callable[[str], None]):
        self.file_path = os.path.abspath(file_path)
        self.callback = callback
        self.last_position = 0
        self._setup_initial_position()
    
    def _setup_initial_position(self):
        if os.path.exists(self.file_path):
            with open(self.file_path, 'r', encoding='utf-8') as f:
                f.seek(0, 2)  # Go to end
                self.last_position = f.tell()
    
    def on_modified(self, event):
        if event.is_directory:
            return
        
        if os.path.abspath(event.src_path) == self.file_path:
            self._read_new_lines()
    
    def _read_new_lines(self):
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                f.seek(self.last_position)
                new_lines = f.readlines()
                self.last_position = f.tell()
                
                for line in new_lines:
                    if line.strip():
                        self.callback(line.strip())
        except Exception as e:
            print(f"Erreur lecture fichier: {e}")

class FileWatcher:
    def __init__(self, file_path: str, callback: Callable[[str], None]):
        self.file_path = file_path
        self.callback = callback
        self.observer = Observer()
        self.handler = LogFileHandler(file_path, callback)
        self._setup_watcher()
    
    def _setup_watcher(self):
        watch_dir = os.path.dirname(os.path.abspath(self.file_path))
        self.observer.schedule(self.handler, watch_dir, recursive=False)
    
    def start(self):
        self.observer.start()
        print(f"Surveillance du fichier: {self.file_path}")
    
    def stop(self):
        self.observer.stop()
        self.observer.join()