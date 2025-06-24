#!/usr/bin/env python3
"""
Title: Modified macOS Downloader
Description: Enhanced version of corpnewt's downloader with GUI integration
Features:
  - GUI-compatible progress reporting
  - Cancellation support
  - Error handling improvements
  - Speed calculation
  - Byte-range resume support
Usage: Called internally by gibmacos_gui.py
Dependencies: requests, tqdm (optional)
License: 
  - Original: MIT (corpnewt/gibMacOS)
  - Modifications: MIT
Author: 
  - Original: corpnewt
  - Modifications: Anoop Kumar
Date:
  - Original: 26/09/2018 (DD/MM/YYYY)
  - Modifications: 24/06/2025 (DD/MM/YYYY)
"""

import os
import requests
import time

class Downloader:
    def __init__(self, skip_w=False, skip_q=False, skip_s=False, interactive=True):
        self.prog_len = 20
        self.last_percent = -1
        self.start_time = 0
        self.indent = 4
        self.total = -1
        self.interactive = interactive
        self.bytes_downloaded = 0
        self.resume_header = {}
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/11.1.2 Safari/605.1.15"
        }
        self.skip_w = skip_w
        self.skip_q = skip_q
        self.skip_s = skip_s

    def resize(self, prog_len):
        self.prog_len = prog_len

    def get_time_string(self, t):
        if t < 60:
            return "{: >2}s".format(int(t))
        elif t < 3600:
            return "{: >2}m {: >2}s".format(int(t // 60), int(t % 60))
        else:
            return "{: >2}h {: >2}m {: >2}s".format(int(t // 3600), int((t % 3600) // 60), int(t % 60))

    def get_size(self, size):
        if size < 1024:
            return "{: >3} B".format(size)
        elif size < 1024**2:
            return "{: >3.1f} KB".format(size / 1024)
        elif size < 1024**3:
            return "{: >3.1f} MB".format(size / 1024**2)
        elif size < 1024**4:
            return "{: >3.1f} GB".format(size / 1024**3)
        else:
            return "{: >3.1f} TB".format(size / 1024**4)

    def get_string(self, url, suppress_errors=False):
        try:
            req = requests.get(url, headers=self.headers)
            return req.content.decode("utf-8")
        except Exception as e:
            if not suppress_errors:
                print(f"Error getting string from {url}: {e}")
            return None

    def get_bytes(self, url, suppress_errors=False):
        try:
            req = requests.get(url, headers=self.headers)
            return req.content
        except Exception as e:
            if not suppress_errors:
                print(f"Error getting bytes from {url}: {e}")
            return None

    def stream_to_file(self, url, file_path, resume_bytes=0, total_bytes=-1, allow_resume=True, callback=None, cancel_event=None):
        try:
            self.bytes_downloaded = resume_bytes
            self.total = total_bytes
            self.start_time = time.time()
            
            if cancel_event and cancel_event.is_set():
                return None

            self.resume_header = {"Range": "bytes={}-".format(resume_bytes)} if allow_resume and resume_bytes > 0 else {}
            
            if self.total == -1 and allow_resume and resume_bytes > 0:
                try:
                    if cancel_event and cancel_event.is_set():
                        return None
                    self.total = int(requests.head(url, headers=self.headers).headers["Content-Length"])
                except:
                    pass

            if cancel_event and cancel_event.is_set():
                return None

            req = requests.get(url, headers={**self.headers, **self.resume_header}, stream=True, timeout=30)
            
            if self.total == -1:
                try: 
                    self.total = int(req.headers["Content-Length"])
                except: 
                    pass

            chunk_size = 1024 * 8  # Increased chunk size for better performance

            with open(file_path, "ab" if allow_resume else "wb") as f:
                for chunk in req.iter_content(chunk_size=chunk_size):
                    if cancel_event and cancel_event.is_set():
                        return None
                    if chunk:
                        f.write(chunk)
                        self.bytes_downloaded += len(chunk)
                        if callback:
                            callback(self.bytes_downloaded, self.total, self.start_time)
            return file_path
        
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 416 and allow_resume and resume_bytes > 0:
                print(f"Server returned 416. Retrying download from scratch for {os.path.basename(file_path)}.")
                if os.path.exists(file_path):
                    os.remove(file_path)
                return self.stream_to_file(url, file_path, resume_bytes=0, total_bytes=-1, allow_resume=False, callback=callback, cancel_event=cancel_event)
            else:
                print(f"Download failed due to HTTP error: {e}")
                return None
        except Exception as e:
            print(f"Download failed due to unexpected error: {e}")
            return None