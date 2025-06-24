#!/usr/bin/env python3
"""
Title: GibMacOS Graphical Interface
Description: User-friendly GUI for macOS installer downloads
Features:
  - Catalog selection (Public Release/Beta/Developer)
  - Version filtering
  - Download progress tracking
  - Console log viewer
  - Sleep prevention (macOS)
  - Download directory selection
Usage: 
  - Primary: Launched via run_gui.py
  - Direct: python gibmacos_gui.py (after integration)
Dependencies: tkinter, requests, pyobjc (macOS only)
License: MIT
Author: YourName
Date: 24/06/2025 (DD/MM/YYYY)
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import sys
import threading
import queue
import json
import time
import re
from tkinter import scrolledtext
import webbrowser
import subprocess

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), "Scripts"))
from Scripts import downloader, utils, run, plist

class ProgramError(Exception):
    def __init__(self, message, title="Error"):
        super(Exception, self).__init__(message)
        self.title = title

class CancelledError(ProgramError):
    def __init__(self, message="Operation cancelled by user."):
        super().__init__(message, title="Operation Cancelled")

class GibMacOSBackend:
    def __init__(self, update_callback=None, progress_callback=None, cancel_event=None):
        self.d = downloader.Downloader(interactive=False)
        self.u = utils.Utils("gibMacOSGUI", interactive=False)
        self.r = run.Run()

        self.update_callback = update_callback
        self.progress_callback = progress_callback
        self.cancel_event = cancel_event

        self.settings_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "Scripts", "settings.json")
        self.settings = {}
        if os.path.exists(self.settings_path):
            try:
                self.settings = json.load(open(self.settings_path))
            except:
                pass

        self.prod_cache_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "Scripts", "prod_cache.plist")
        self.prod_cache = {}
        if os.path.exists(self.prod_cache_path):
            try:
                with open(self.prod_cache_path, "rb") as f:
                    self.prod_cache = plist.load(f)
                assert isinstance(self.prod_cache, dict)
            except:
                self.prod_cache = {}

        self.current_macos = self.settings.get("current_macos", 20)
        self.min_macos = 5
        self.current_catalog = self.settings.get("current_catalog", "publicrelease")
        self.find_recovery = self.settings.get("find_recovery", False)
        self.caffeinate_downloads = self.settings.get("caffeinate_downloads", True)
        self.catalog_data = None
        self.mac_prods = []
        
        self.save_local = self.settings.get("save_local", False)
        self.force_local = self.settings.get("force_local", False)
        self.print_urls = self.settings.get("print_urls", False)
        self.print_json = self.settings.get("print_json", False)

        self.catalog_suffix = {
            "public": "beta",
            "publicrelease": "",
            "customer": "customerseed",
            "developer": "seed"
        }
        self.mac_os_names_url = {
            "8": "mountainlion",
            "7": "lion",
            "6": "snowleopard",
            "5": "leopard"
        }
        self.version_names = {
            "tiger": "10.4",
            "leopard": "10.5",
            "snow leopard": "10.6",
            "lion": "10.7",
            "mountain lion": "10.8",
            "mavericks": "10.9",
            "yosemite": "10.10",
            "el capitan": "10.11",
            "sierra": "10.12",
            "high sierra": "10.13",
            "mojave": "10.14",
            "catalina": "10.15",
            "big sur": "11",
            "monterey": "12",
            "ventura": "13",
            "sonoma": "14",
            "sequoia": "15"
        }
        self.recovery_suffixes = (
            "RecoveryHDUpdate.pkg",
            "RecoveryHDMetaDmg.pkg"
        )
        self.caffeinate_process = None

        self.settings_to_save = (
            "current_macos",
            "current_catalog",
            "find_recovery",
            "caffeinate_downloads",
            "save_local",
            "force_local",
        )

    def _update_status(self, message):
        if self.update_callback:
            self.update_callback(message)

    def _update_progress(self, current, total, start_time):
        if self.progress_callback:
            self.progress_callback(current, total, start_time)

    def save_settings(self):
        for setting in self.settings_to_save:
            self.settings[setting] = getattr(self, setting, None)
        try:
            json.dump(self.settings, open(self.settings_path, "w"), indent=2)
        except Exception as e:
            raise ProgramError(
                "Failed to save settings to:\n\n{}\n\nWith error:\n\n - {}\n".format(self.settings_path, repr(e)),
                title="Error Saving Settings")

    def save_prod_cache(self):
        try:
            with open(self.prod_cache_path, "wb") as f:
                plist.dump(self.prod_cache, f)
        except Exception as e:
            raise ProgramError(
                "Failed to save product cache to:\n\n{}\n\nWith error:\n\n - {}\n".format(self.prod_cache_path, repr(e)),
                title="Error Saving Product Cache")

    def set_catalog(self, catalog):
        self.current_catalog = catalog.lower() if catalog.lower() in self.catalog_suffix else "publicrelease"

    def num_to_macos(self, macos_num, for_url=True):
        if for_url:
            return self.mac_os_names_url.get(str(macos_num), "10.{}".format(macos_num)) if macos_num <= 16 else str(macos_num - 5)
        return "10.{}".format(macos_num) if macos_num <= 15 else str(macos_num - 5)

    def macos_to_num(self, macos):
        try:
            macos_parts = [int(x) for x in macos.split(".")][:2 if macos.startswith("10.") else 1]
            if macos_parts[0] == 11:
                macos_parts = [10, 16]
        except:
            return None
        if len(macos_parts) > 1:
            return macos_parts[1]
        return 5 + macos_parts[0]

    def get_macos_versions(self, minos=None, maxos=None, catalog=""):
        if minos is None:
            minos = self.min_macos
        if maxos is None:
            maxos = self.current_macos
        if minos > maxos:
            minos, maxos = maxos, minos
        os_versions = [self.num_to_macos(x, for_url=True) for x in range(minos, maxos + 1)]
        if catalog:
            custom_cat_entry = os_versions[-1] + catalog
            os_versions.append(custom_cat_entry)
        return os_versions

    def build_url(self, **kwargs):
        catalog = kwargs.get("catalog", self.current_catalog).lower()
        catalog = catalog if catalog.lower() in self.catalog_suffix else "publicrelease"
        version = int(kwargs.get("version", self.current_macos))
        return "https://swscan.apple.com/content/catalogs/others/index-{}.merged-1.sucatalog".format(
            "-".join(reversed(self.get_macos_versions(self.min_macos, version, catalog=self.catalog_suffix.get(catalog, ""))))
        )

    def get_catalog_data(self):
        if self.cancel_event and self.cancel_event.is_set():
            raise CancelledError()

        url = self.build_url(catalog=self.current_catalog, version=self.current_macos)
        self._update_status(f"Downloading {self.current_catalog} catalog from:\n{url}")
        
        local_catalog = os.path.join(os.path.dirname(os.path.realpath(__file__)), "Scripts", "sucatalog.plist")
        
        if self.save_local:
            self._update_status(f"Checking for local catalog at:\n{local_catalog}")
            if os.path.exists(local_catalog) and not self.force_local:
                self._update_status(" - Found - loading...")
                try:
                    with open(local_catalog, "rb") as f:
                        self.catalog_data = plist.load(f)
                        assert isinstance(self.catalog_data, dict)
                    self._update_status("Catalog loaded from local file.")
                    return True
                except Exception as e:
                    self._update_status(f" - Error loading local catalog: {e}. Downloading instead...")
            elif self.force_local:
                self._update_status(" - Forcing re-download of local catalog...")
            else:
                self._update_status(" - Local catalog not found - downloading instead...")

        try:
            b = self.d.get_bytes(url, False)
            if self.cancel_event and self.cancel_event.is_set():
                raise CancelledError()
            self.catalog_data = plist.loads(b)
            self._update_status("Catalog downloaded successfully.")
        except Exception as e:
            self._update_status(f"Error downloading catalog: {e}")
            return False
        
        if self.save_local or self.force_local:
            self._update_status(f" - Saving catalog to:\n - {local_catalog}")
            try:
                with open(local_catalog, "wb") as f:
                    plist.dump(self.catalog_data, f)
                self._update_status("Catalog saved locally.")
            except Exception as e:
                self._update_status(f" - Error saving catalog: {e}")
                return False
        return True

    def get_installers(self, plist_dict=None):
        if not plist_dict:
            plist_dict = self.catalog_data
        if not plist_dict:
            return []
        mac_prods = []
        for p in plist_dict.get("Products", {}):
            if self.cancel_event and self.cancel_event.is_set():
                raise CancelledError()
            if not self.find_recovery:
                val = plist_dict.get("Products", {}).get(p, {}).get("ExtendedMetaInfo", {}).get("InstallAssistantPackageIdentifiers", {})
                if val.get("OSInstall", {}) == "com.apple.mpkg.OSInstall" or val.get("SharedSupport", "").startswith("com.apple.pkg.InstallAssistant"):
                    mac_prods.append(p)
            else:
                if any(x for x in plist_dict.get("Products", {}).get(p, {}).get("Packages", []) if x["URL"].endswith(self.recovery_suffixes)):
                    mac_prods.append(p)
        return mac_prods

    def get_build_version(self, dist_dict):
        build = version = name = "Unknown"
        try:
            dist_url = dist_dict.get("English", dist_dict.get("en", ""))
            assert dist_url
            dist_file = self.d.get_string(dist_url, False)
            assert isinstance(dist_file, str)
        except Exception as e:
            dist_file = ""
        build_search = "macOSProductBuildVersion" if "macOSProductBuildVersion" in dist_file else "BUILD"
        vers_search = "macOSProductVersion" if "macOSProductVersion" in dist_file else "VERSION"
        try:
            build = dist_file.split("<key>{}</key>".format(build_search))[1].split("<string>")[1].split("</string>")[0]
        except:
            pass
        try:
            version = dist_file.split("<key>{}</key>".format(vers_search))[1].split("<string>")[1].split("</string>")[0]
        except:
            pass
        try:
            name = re.search(r"<title>(.+?)</title>", dist_file).group(1)
        except:
            pass
        try:
            device_ids = re.search(r"var supportedDeviceIDs\s*=\s*\[([^]]+)\];", dist_file)[1]
            device_ids = list(set(i.lower() for i in re.findall(r"'([^',]+)'", device_ids)))
        except:
            device_ids = []
        return (build, version, name, device_ids)

    def get_dict_for_prods(self, prods, plist_dict=None):
        self._update_status("Scanning products after catalog download...")
        plist_dict = plist_dict or self.catalog_data or {}
        prod_list = []
        prod_keys = (
            "build",
            "date",
            "description",
            "device_ids",
            "installer",
            "product",
            "time",
            "title",
            "version",
        )

        def get_packages_and_size(plist_dict, prod, recovery):
            packages = []
            if recovery:
                packages = [x for x in plist_dict.get("Products", {}).get(prod, {}).get("Packages", []) if x["URL"].endswith(self.recovery_suffixes)]
            else:
                packages = plist_dict.get("Products", {}).get(prod, {}).get("Packages", [])
            size = self.d.get_size(sum([i["Size"] for i in packages]))
            return (packages, size)

        def prod_valid(prod, prod_list, prod_keys):
            if not isinstance(prod_list, dict) or not prod in prod_list or \
            not all(x in prod_list[prod] for x in prod_keys):
                return False
            if any(prod_list[prod].get(x, "Unknown") == "Unknown" for x in prod_keys):
                return False
            return True

        prod_changed = False
        for prod in prods:
            if self.cancel_event and self.cancel_event.is_set():
                raise CancelledError()
            if prod_valid(prod, self.prod_cache, prod_keys):
                prodd = {}
                for key in self.prod_cache[prod]:
                    prodd[key] = self.prod_cache[prod][key]
                prodd["packages"], prodd["size"] = get_packages_and_size(plist_dict, prod, self.find_recovery)
                prod_list.append(prodd)
                continue
            
            prodd = {"product": prod}
            try:
                url = plist_dict.get("Products", {}).get(prod, {}).get("ServerMetadataURL", "")
                assert url
                b = self.d.get_bytes(url, False)
                smd = plist.loads(b)
            except:
                smd = {}
            
            prodd["date"] = plist_dict.get("Products", {}).get(prod, {}).get("PostDate", "")
            prodd["installer"] = plist_dict.get("Products", {}).get(prod, {}).get("ExtendedMetaInfo", {}).get("InstallAssistantPackageIdentifiers", {}).get("OSInstall", {}) == "com.apple.mpkg.OSInstall"
            prodd["time"] = time.mktime(prodd["date"].timetuple()) + prodd["date"].microsecond / 1E6
            prodd["version"] = smd.get("CFBundleShortVersionString", "Unknown").strip()
            try:
                desc = smd.get("localization", {}).get("English", {}).get("description", "").decode("utf-8")
                desctext = desc.split('"p1">')[1].split("</a>")[0]
            except:
                desctext = ""
            prodd["description"] = desctext
            prodd["packages"], prodd["size"] = get_packages_and_size(plist_dict, prod, self.find_recovery)
            prodd["size"] = self.d.get_size(sum([i["Size"] for i in prodd["packages"]]))
            prodd["build"], v, n, prodd["device_ids"] = self.get_build_version(plist_dict.get("Products", {}).get(prod, {}).get("Distributions", {}))
            prodd["title"] = smd.get("localization", {}).get("English", {}).get("title", n)
            if v.lower() != "unknown":
                prodd["version"] = v
            prod_list.append(prodd)
            
            if smd or not plist_dict.get("Products", {}).get(prod, {}).get("ServerMetadataURL", ""):
                prod_changed = True
                temp_prod = {}
                for key in prodd:
                    if key in ("packages", "size"):
                        continue
                    if prodd[key] == "Unknown":
                        temp_prod = None
                        break
                    temp_prod[key] = prodd[key]
                if temp_prod:
                    self.prod_cache[prod] = temp_prod
        
        if prod_changed and self.prod_cache:
            try:
                self.save_prod_cache()
            except:
                pass
        
        prod_list = sorted(prod_list, key=lambda x: x["time"], reverse=True)
        return prod_list

    def start_caffeinate(self):
        if sys.platform.lower() == "darwin" \
        and self.caffeinate_downloads \
        and os.path.isfile("/usr/bin/caffeinate"):
            self.term_caffeinate_proc()
            self.caffeinate_process = subprocess.Popen(
                ["/usr/bin/caffeinate"],
                stderr=getattr(subprocess, "DEVNULL", open(os.devnull, "w")),
                stdout=getattr(subprocess, "DEVNULL", open(os.devnull, "w")),
                stdin=getattr(subprocess, "DEVNULL", open(os.devnull, "w"))
            )
        return self.caffeinate_process

    def term_caffeinate_proc(self):
        if self.caffeinate_process is None:
            return True
        try:
            if self.caffeinate_process.poll() is None:
                start = time.time()
                while self.caffeinate_process.poll() is None:
                    if time.time() - start > 10:
                        self._update_status(f"Timed out trying to terminate caffeinate process with PID {self.caffeinate_process.pid}!")
                        return False
                    self.caffeinate_process.terminate()
                    time.sleep(0.02)
        except:
            pass
        return True

    def download_prod(self, prod, download_dir, dmg=False):
        name = "{} - {} {} ({})".format(prod["product"], prod["version"], prod["title"], prod["build"]).replace(":", "").strip()
        full_download_path = os.path.join(download_dir, name)

        dl_list = []
        for x in prod["packages"]:
            if not x.get("URL", None):
                continue
            if dmg and not x.get("URL", "").lower().endswith(".dmg"):
                continue
            dl_list.append(x)
        
        if not len(dl_list):
            raise ProgramError("There were no files to download for this product.")

        if not os.path.isdir(full_download_path):
            os.makedirs(full_download_path)
        
        self.term_caffeinate_proc()
        
        failed_downloads = []
        for c, x in enumerate(dl_list, start=1):
            if self.cancel_event and self.cancel_event.is_set():
                raise CancelledError()

            url = x["URL"]
            file_name = os.path.basename(url)
            file_path = os.path.join(full_download_path, file_name)
            
            resume_bytes = 0
            if os.path.exists(file_path):
                resume_bytes = os.path.getsize(file_path)
            
            self._update_status(f"Downloading file {c} of {len(dl_list)}: {file_name} to {full_download_path}")

            try:
                self.start_caffeinate()
                result = self.d.stream_to_file(url, file_path, resume_bytes=resume_bytes, allow_resume=True, callback=self.progress_callback, cancel_event=self.cancel_event)
                if result is None:
                    if self.cancel_event and self.cancel_event.is_set():
                        raise CancelledError("Download cancelled by user.")
                    else:
                        raise Exception("Download failed or was interrupted (no specific error).")
                self._update_status(f"Successfully downloaded: {file_name}")
            except Exception as e:
                self._update_status(f"Failed to download {file_name}: {e}")
                failed_downloads.append(file_name)
            finally:
                self.term_caffeinate_proc()

        if failed_downloads:
            raise ProgramError(f"{len(failed_downloads)} files failed to download: {', '.join(failed_downloads)}", title="Download Failed")

class GibMacOSGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("gibMacOS GUI")
        self.geometry("800x600")
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self.download_queue = queue.Queue()
        self.after_id = None
        self.cancel_event = threading.Event()
        self.current_thread = None

        self.download_dir = os.path.join(os.path.expanduser("~"), "macOS Downloads")
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)

        self.backend = GibMacOSBackend(
            update_callback=self._queue_status_update,
            progress_callback=self._queue_progress_update,
            cancel_event=self.cancel_event
        )
        
        self.current_catalog_var = tk.StringVar(self)
        self.current_catalog_var.set(self.backend.current_catalog)
        self.max_macos_var = tk.StringVar(self)
        self.max_macos_var.set(self.backend.num_to_macos(self.backend.current_macos, for_url=False))
        self.find_recovery_var = tk.BooleanVar(self)
        self.find_recovery_var.set(self.backend.find_recovery)
        self.caffeinate_downloads_var = tk.BooleanVar(self)
        self.caffeinate_downloads_var.set(self.backend.caffeinate_downloads)
        self.download_dir_var = tk.StringVar(self)
        self.download_dir_var.set(self.download_dir)
        self.save_local_var = tk.BooleanVar(self)
        self.save_local_var.set(self.backend.save_local)
        self.force_local_var = tk.BooleanVar(self)
        self.force_local_var.set(self.backend.force_local)
        self.show_console_log_var = tk.BooleanVar(self)
        self.show_console_log_var.set(True)

        self.gui_products_data = []

        self._create_widgets()
        self._check_queue()
        self._refresh_products()

    def _on_close(self):
        if self.after_id:
            self.after_cancel(self.after_id)
        if self.current_thread and self.current_thread.is_alive():
            self.cancel_event.set()
            self.current_thread.join(timeout=2.0)
        self.destroy()

    def _queue_status_update(self, message):
        self.download_queue.put(("status", message))

    def _queue_progress_update(self, current_bytes, total_bytes, start_time):
        self.download_queue.put(("progress", (current_bytes, total_bytes, start_time)))

    def _queue_error_dialog(self, title, message):
        self.download_queue.put(("error", (title, message)))

    def _queue_info_dialog(self, title, message):
        self.download_queue.put(("info", (title, message)))

    def _queue_ui_state(self, enabled):
        self.download_queue.put(("ui_state", enabled))

    def _check_queue(self):
        try:
            while True:
                try:
                    msg_type, data = self.download_queue.get_nowait()
                    if msg_type == "status":
                        self.status_label.config(text=data)
                        self._write_to_console(f"STATUS: {data}")
                    elif msg_type == "progress":
                        current, total, start_time = data
                        self._update_progress_bar(current, total, start_time)
                    elif msg_type == "error":
                        messagebox.showerror(data[0], data[1])
                        self._write_to_console(f"ERROR: {data[0]} - {data[1]}")
                    elif msg_type == "info":
                        messagebox.showinfo(data[0], data[1])
                        self._write_to_console(f"INFO: {data[0]} - {data[1]}")
                    elif msg_type == "ui_state":
                        self._set_ui_state(data)
                    elif msg_type == "populate_products":
                        self._populate_product_tree(data)
                    self.download_queue.task_done()
                except queue.Empty:
                    break
        except Exception as e:
            print(f"Error processing queue: {e}")
        finally:
            self.after_id = self.after(100, self._check_queue)

    def _get_time_string(self, t):
        if t < 60:
            return "{: >2}s".format(int(t))
        elif t < 3600:
            return "{: >2}m {: >2}s".format(int(t // 60), int(t % 60))
        else:
            return "{: >2}h {: >2}m {: >2}s".format(int(t // 3600), int((t % 3600) // 60), int(t % 60))

    def _update_status_label(self, message):
        self.status_label.config(text=message)

    def _update_progress_bar(self, current, total, start_time):
        if total > 0:
            percent = (current / total) * 100
            self.progress_bar["value"] = percent
            
            elapsed_time = time.time() - start_time
            if elapsed_time > 0 and current > 0:
                speed = current / elapsed_time
                time_remaining = (total - current) / speed if speed > 0 else 0
                speed_str = self.backend.d.get_size(speed).replace("B", "B/s")
                eta_str = self._get_time_string(time_remaining)
                self.progress_bar_label.config(text=f"{percent:.2f}% ({self.backend.d.get_size(current)} / {self.backend.d.get_size(total)}) - {speed_str} - ETA {eta_str}")
            else:
                self.progress_bar_label.config(text=f"{percent:.2f}% ({self.backend.d.get_size(current)} / {self.backend.d.get_size(total)})")
        else:
            self.progress_bar["value"] = 0
            self.progress_bar_label.config(text="")

    def _write_to_console(self, message):
        self.console_text.config(state=tk.NORMAL)
        self.console_text.insert(tk.END, message + "\n")
        self.console_text.see(tk.END)
        self.console_text.config(state=tk.DISABLED)

    def _create_widgets(self):
        self.menubar = tk.Menu(self)
        self.config(menu=self.menubar)

        self.file_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="File", menu=self.file_menu)
        self.file_menu.add_command(label="Open Download Directory", command=self._open_download_dir)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", command=self._on_close)

        self.help_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Help", menu=self.help_menu)
        self.help_menu.add_command(label="How to Use", command=self._show_how_to_use)
        self.help_menu.add_command(label="About", command=self._show_about)

        self.settings_frame = ttk.LabelFrame(self, text="Settings", padding="10")
        self.settings_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

        self.products_frame = ttk.LabelFrame(self, text="Available macOS Products", padding="10")
        self.products_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.bottom_panel_frame = ttk.Frame(self)
        self.bottom_panel_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.bottom_panel_frame.grid_rowconfigure(0, weight=0)
        self.bottom_panel_frame.grid_rowconfigure(1, weight=1)
        self.bottom_panel_frame.grid_columnconfigure(0, weight=1)

        self.status_frame = ttk.LabelFrame(self.bottom_panel_frame, text="Status", padding="10")
        self.status_frame.grid(row=0, column=0, sticky=tk.NSEW)

        self.console_log_frame = ttk.LabelFrame(self.bottom_panel_frame, text="Console Log", padding="10")
        self.console_text = scrolledtext.ScrolledText(self.console_log_frame, wrap=tk.WORD, height=10, state=tk.DISABLED)
        self.console_text.pack(fill=tk.BOTH, expand=True)
        if self.show_console_log_var.get():
            self.console_log_frame.grid(row=1, column=0, sticky=tk.NSEW)

        ttk.Label(self.settings_frame, text="Catalog:").grid(row=0, column=0, padx=5, pady=2, sticky=tk.W)
        self.catalog_dropdown = ttk.OptionMenu(
            self.settings_frame, self.current_catalog_var, self.current_catalog_var.get(),
            *list(self.backend.catalog_suffix.keys()), command=self._on_catalog_change
        )
        self.catalog_dropdown.grid(row=0, column=1, padx=5, pady=2, sticky=tk.W)

        ttk.Label(self.settings_frame, text="Max macOS Version:").grid(row=1, column=0, padx=5, pady=2, sticky=tk.W)
        self.max_macos_entry = ttk.Entry(self.settings_frame, textvariable=self.max_macos_var, width=10)
        self.max_macos_entry.grid(row=1, column=1, padx=5, pady=2, sticky=tk.W)
        self.max_macos_entry.bind("<Return>", self._on_max_macos_change)

        self.checkboxes_frame = ttk.Frame(self.settings_frame)
        self.checkboxes_frame.grid(row=0, column=2, rowspan=2, padx=10, pady=2, sticky=tk.W)
        
        self.find_recovery_checkbox = ttk.Checkbutton(
            self.checkboxes_frame, text="Find Recovery Only", variable=self.find_recovery_var,
            command=self._on_find_recovery_toggle
        )
        self.find_recovery_checkbox.grid(row=0, column=0, padx=5, sticky=tk.W)

        self.caffeinate_checkbox = ttk.Checkbutton(
            self.checkboxes_frame, text="Caffeinate Downloads (macOS only)",
            variable=self.caffeinate_downloads_var, command=self._on_caffeinate_toggle
        )
        self.caffeinate_checkbox.grid(row=1, column=0, padx=5, sticky=tk.W)
        if sys.platform != "darwin":
            self.caffeinate_checkbox.config(state=tk.DISABLED)

        self.save_local_checkbox = ttk.Checkbutton(
            self.checkboxes_frame, text="Save Catalog Locally",
            variable=self.save_local_var, command=self._on_save_local_toggle
        )
        self.save_local_checkbox.grid(row=0, column=1, padx=5, sticky=tk.W)

        self.force_local_checkbox = ttk.Checkbutton(
            self.checkboxes_frame, text="Force Local Catalog Re-download",
            variable=self.force_local_var, command=self._on_force_local_toggle
        )
        self.force_local_checkbox.grid(row=1, column=1, padx=5, sticky=tk.W)

        self.show_console_checkbox = ttk.Checkbutton(
            self.checkboxes_frame, text="Show Console Log",
            variable=self.show_console_log_var, command=self._toggle_console_log
        )
        self.show_console_checkbox.grid(row=0, column=2, padx=5, sticky=tk.W)

        ttk.Label(self.settings_frame, text="Download Directory:").grid(row=2, column=0, padx=5, pady=2, sticky=tk.W)
        self.download_dir_entry = ttk.Entry(self.settings_frame, textvariable=self.download_dir_var, width=50, state=tk.DISABLED)
        self.download_dir_entry.grid(row=2, column=1, columnspan=2, padx=5, pady=2, sticky=(tk.W, tk.E))
        self.browse_dir_button = ttk.Button(self.settings_frame, text="Browse", command=self._browse_download_dir)
        self.browse_dir_button.grid(row=2, column=3, padx=5, pady=2, sticky=tk.W)

        self.buttons_frame = ttk.Frame(self.settings_frame)
        self.buttons_frame.grid(row=3, column=0, columnspan=4, pady=5, sticky=tk.W)

        ttk.Button(self.buttons_frame, text="Refresh Products", command=self._refresh_products).pack(side=tk.LEFT, padx=5)
        
        self.set_su_button = ttk.Button(
            self.buttons_frame, text="Set SU CatalogURL", command=self._set_su_catalog,
            state=tk.NORMAL if sys.platform == "darwin" else tk.DISABLED
        )
        self.set_su_button.pack(side=tk.LEFT, padx=5)

        self.clear_su_button = ttk.Button(
            self.buttons_frame, text="Clear SU CatalogURL", command=self._clear_su_catalog,
            state=tk.NORMAL if sys.platform == "darwin" else tk.DISABLED
        )
        self.clear_su_button.pack(side=tk.LEFT, padx=5)
        
        self.download_button = ttk.Button(self.buttons_frame, text="Download Selected", command=self._download_selected, state=tk.DISABLED)
        self.download_button.pack(side=tk.LEFT, padx=5)

        self.cancel_button = ttk.Button(self.buttons_frame, text="Cancel", command=self._cancel_operation, state=tk.DISABLED)
        self.cancel_button.pack(side=tk.LEFT, padx=5)

        self.product_tree = ttk.Treeview(self.products_frame, columns=("Name", "Version", "Build", "Size", "Product ID"), show="headings")
        self.product_tree.heading("Name", text="macOS Name", anchor=tk.W)
        self.product_tree.heading("Version", text="Version", anchor=tk.W)
        self.product_tree.heading("Build", text="Build", anchor=tk.W)
        self.product_tree.heading("Size", text="Size", anchor=tk.E)
        self.product_tree.heading("Product ID", text="Product ID", anchor=tk.W)
        
        self.product_tree.column("Name", width=300, stretch=tk.YES)
        self.product_tree.column("Version", width=100, stretch=tk.NO)
        self.product_tree.column("Build", width=100, stretch=tk.NO)
        self.product_tree.column("Size", width=80, anchor=tk.E, stretch=tk.NO)
        self.product_tree.column("Product ID", width=100, stretch=tk.NO)

        scrollbar = ttk.Scrollbar(self.products_frame, orient="vertical", command=self.product_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.product_tree.configure(yscrollcommand=scrollbar.set)
        self.product_tree.pack(fill=tk.BOTH, expand=True)

        self.product_tree.bind("<<TreeviewSelect>>", self._on_product_select)

        self.status_label = ttk.Label(self.status_frame, text="Ready.", wraplength=750)
        self.status_label.pack(fill=tk.X, pady=2)
        
        self.progress_bar = ttk.Progressbar(self.status_frame, orient="horizontal", length=200, mode="determinate")
        self.progress_bar.pack(fill=tk.X, pady=2)
        self.progress_bar_label = ttk.Label(self.status_frame, text="")
        self.progress_bar_label.pack(pady=2)

    def _on_catalog_change(self, selected_catalog):
        self.backend.set_catalog(selected_catalog)
        self.backend.save_settings()
        self._refresh_products()

    def _on_max_macos_change(self, event=None):
        version_str = self.max_macos_var.get().strip()
        version_num = self.backend.macos_to_num(version_str)
        if version_num:
            self.backend.current_macos = version_num
            self.backend.save_settings()
            self._refresh_products()
        else:
            self._queue_error_dialog("Invalid Input", "Please enter a valid macOS version (e.g., 10.15, 11, 12).")
            self.max_macos_var.set(self.backend.num_to_macos(self.backend.current_macos, for_url=False))

    def _on_find_recovery_toggle(self):
        self.backend.find_recovery = self.find_recovery_var.get()
        self.backend.save_settings()
        self._refresh_products()

    def _on_caffeinate_toggle(self):
        self.backend.caffeinate_downloads = self.caffeinate_downloads_var.get()
        self.backend.save_settings()

    def _on_save_local_toggle(self):
        self.backend.save_local = self.save_local_var.get()
        self.backend.save_settings()

    def _on_force_local_toggle(self):
        self.backend.force_local = self.force_local_var.get()
        self.backend.save_settings()

    def _toggle_console_log(self):
        if self.show_console_log_var.get():
            self.console_log_frame.grid(row=1, column=0, sticky=tk.NSEW)
        else:
            self.console_log_frame.grid_forget()

    def _browse_download_dir(self):
        selected_dir = filedialog.askdirectory(initialdir=self.download_dir)
        if selected_dir:
            self.download_dir = selected_dir
            self.download_dir_var.set(selected_dir)

    def _open_download_dir(self):
        try:
            webbrowser.open(self.download_dir)
        except Exception as e:
            self._queue_error_dialog("Error Opening Directory", f"Could not open download directory: {e}")

    def _set_su_catalog(self):
        if sys.platform != "darwin":
            self._queue_info_dialog("Not Applicable", "This feature is only available on macOS.")
            return
        
        self._set_ui_state(False)
        self.cancel_event.clear()

        def run_command():
            try:
                self._queue_status_update("Setting Software Update Catalog URL...")
                url = self.backend.build_url()
                self.backend.r.run({"args":["softwareupdate","--set-catalog",url],"sudo":True})
                self._queue_status_update(f"Software Update Catalog URL set to:\n{url}")
            except Exception as e:
                self._queue_status_update(f"Failed to set Software Update Catalog URL: {e}")
                self._queue_error_dialog("Error", f"Failed to set Software Update Catalog URL: {e}\n(Might require administrator privileges.)")
            finally:
                self._queue_ui_state(True)
                self.current_thread = None

        self.current_thread = threading.Thread(target=run_command)
        self.current_thread.start()

    def _clear_su_catalog(self):
        if sys.platform != "darwin":
            self._queue_info_dialog("Not Applicable", "This feature is only available on macOS.")
            return

        self._set_ui_state(False)
        self.cancel_event.clear()

        def run_command():
            try:
                self._queue_status_update("Clearing Software Update Catalog URL...")
                self.backend.r.run({"args":["softwareupdate","--clear-catalog"],"sudo":True})
                self._queue_status_update("Software Update Catalog URL cleared.")
            except Exception as e:
                self._queue_status_update(f"Failed to clear Software Update Catalog URL: {e}")
                self._queue_error_dialog("Error", f"Failed to clear Software Update Catalog URL: {e}\n(Might require administrator privileges.)")
            finally:
                self._queue_ui_state(True)
                self.current_thread = None
        
        self.current_thread = threading.Thread(target=run_command)
        self.current_thread.start()

    def _refresh_products(self):
        self._set_ui_state(False)
        self.cancel_event.clear()
        
        self._queue_status_update("Fetching and parsing macOS product catalog, please wait...")
        self.progress_bar["value"] = 0
        self.progress_bar_label.config(text="")

        def fetch_products_task():
            try:
                if self.backend.force_local:
                    self.backend.prod_cache = {}
                
                if not self.backend.get_catalog_data():
                    if self.cancel_event.is_set():
                        raise CancelledError("Catalog download cancelled.")
                    else:
                        raise ProgramError("Failed to retrieve catalog data. Check internet connection or catalog settings.")

                mac_prods_data = self.backend.get_dict_for_prods(self.backend.get_installers())
                
                if self.cancel_event.is_set():
                    raise CancelledError("Product scanning cancelled.")

                self.download_queue.put(("populate_products", mac_prods_data))
                self._queue_status_update("Catalog refreshed. Populating products...")
            except CancelledError as e:
                self._queue_status_update(str(e))
                self._queue_info_dialog(e.title, str(e))
            except ProgramError as e:
                self._queue_status_update(f"Error refreshing products: {e.title} - {e}")
                self._queue_error_dialog(e.title, str(e))
            except Exception as e:
                self._queue_status_update(f"An unexpected error occurred: {e}")
                self._queue_error_dialog("Error", str(e))
            finally:
                self._queue_status_update("Ready.")
                self._queue_ui_state(True)
                self.current_thread = None

        self.current_thread = threading.Thread(target=fetch_products_task)
        self.current_thread.start()

    def _populate_product_tree(self, mac_prods_data):
        self.product_tree.delete(*self.product_tree.get_children())
        self.gui_products_data = mac_prods_data
        for p in mac_prods_data:
            display_name = f"{p['title']} {p['version']}"
            if p['build'].lower() != 'unknown':
                display_name += f" ({p['build']})"
            
            self.product_tree.insert("", tk.END, iid=p["product"],
                                   values=(display_name, p["version"], p["build"], p["size"], p["product"]))
        self._queue_status_update(f"Found {len(mac_prods_data)} macOS products.")

    def _on_product_select(self, event):
        selected_items = self.product_tree.selection()
        if selected_items:
            self.download_button.config(state=tk.NORMAL)
        else:
            self.download_button.config(state=tk.DISABLED)

    def _download_selected(self):
        selected_item_id = self.product_tree.focus()
        if not selected_item_id:
            self._queue_info_dialog("No Selection", "Please select a macOS product to download.")
            return

        selected_prod = next((p for p in self.gui_products_data if p["product"] == selected_item_id), None)
        
        if not selected_prod:
            self._queue_error_dialog("Error", "Selected product not found in displayed data. Please refresh products.")
            return

        confirm = messagebox.askyesno(
            "Confirm Download",
            f"Are you sure you want to download '{selected_prod['title']} {selected_prod['version']} ({selected_prod['build']})' "
            f"to '{self.download_dir}'?"
        )
        if not confirm:
            return

        self._set_ui_state(False)
        self.cancel_event.clear()
        self.progress_bar["value"] = 0
        self.progress_bar_label.config(text="Starting download...")
        self._queue_status_update(f"Initiating download for {selected_prod['title']}...")

        def download_task():
            try:
                self.backend.download_prod(selected_prod, self.download_dir)
                self._queue_status_update(f"Download complete for {selected_prod['title']}!")
                self._queue_info_dialog(
                    "Download Complete",
                    f"All files for {selected_prod['title']} downloaded successfully to:\n"
                    f"{os.path.join(self.download_dir, selected_prod['product'])}"
                )
            except CancelledError as e:
                self._queue_status_update(str(e))
                self._queue_info_dialog(e.title, str(e))
            except ProgramError as e:
                self._queue_status_update(f"Download error: {e.title} - {e}")
                self._queue_error_dialog(e.title, str(e))
            except Exception as e:
                self._queue_status_update(f"An unexpected error occurred during download: {e}")
                self._queue_error_dialog("Error", str(e))
            finally:
                self._queue_progress_update(0, 0, 0)
                self._queue_ui_state(True)
                self._queue_status_update("Ready.")
                self.current_thread = None

        self.current_thread = threading.Thread(target=download_task)
        self.current_thread.start()

    def _cancel_operation(self):
        self.cancel_event.set()
        self._queue_status_update("Cancelling current operation, please wait...")

    def _set_ui_state(self, enabled):
        state = tk.NORMAL if enabled else tk.DISABLED
        self.catalog_dropdown.config(state=state)
        self.max_macos_entry.config(state=state)
        self.find_recovery_checkbox.config(state=state)
        self.caffeinate_checkbox.config(state=state if sys.platform == "darwin" else tk.DISABLED)
        self.save_local_checkbox.config(state=state)
        self.force_local_checkbox.config(state=state)
        self.browse_dir_button.config(state=state)
        
        set_su_state = tk.NORMAL if enabled and sys.platform == "darwin" else tk.DISABLED
        clear_su_state = tk.NORMAL if enabled and sys.platform == "darwin" else tk.DISABLED
        
        self.set_su_button.config(state=set_su_state)
        self.clear_su_button.config(state=clear_su_state)

        self.product_tree.config(selectmode="extended" if enabled else "none")

        if enabled and self.product_tree.selection():
            self.download_button.config(state=tk.NORMAL)
        else:
            self.download_button.config(state=tk.DISABLED)
        
        self.cancel_button.config(state=tk.NORMAL if not enabled else tk.DISABLED)
        self.show_console_checkbox.config(state=tk.NORMAL)

    def _show_how_to_use(self):
        """Improved help dialog with better organization"""
        help_text = """gibMacOS GUI - Help Guide

This application allows you to download macOS installers and recovery images directly from Apple's servers.

Key Features:
-------------
• Download full macOS installers (10.7 Lion through current versions)
• Access different catalogs (Public, Developer, Customer Seed)
• Download recovery-only images
• Set your Mac's Software Update catalog
• Save bandwidth by caching catalog data
• Detailed progress reporting with speed and ETA

Basic Usage:
------------
1. Select your desired catalog type from the dropdown
2. Set the maximum macOS version you want to see
3. Click "Refresh Products" to load available installers
4. Select an installer from the list
5. Choose download directory (defaults to ~/macOS Downloads)
6. Click "Download Selected" to begin download

Advanced Options:
----------------
• Find Recovery Only: Shows only recovery images (smaller downloads)
• Caffeinate Downloads: Prevents Mac from sleeping during downloads
• Save Catalog Locally: Caches catalog data for faster future use
• Force Local Catalog Re-download: Updates cached catalog data

License:
--------
This software is released under the MIT License.

For more information and updates, please visit:
https://github.com/corpnewt/gibMacOS
"""
        help_window = tk.Toplevel(self)
        help_window.title("gibMacOS GUI Help")
        help_window.geometry("700x500")
        
        text_frame = ttk.Frame(help_window)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        text = scrolledtext.ScrolledText(
            text_frame,
            wrap=tk.WORD,
            font=('Helvetica', 11),
            padx=10,
            pady=10
        )
        text.pack(fill=tk.BOTH, expand=True)
        text.insert(tk.END, help_text)
        text.config(state=tk.DISABLED)
        
        ttk.Button(
            help_window,
            text="Close",
            command=help_window.destroy
        ).pack(pady=10)

    def _show_about(self):
        """Improved about dialog with concise license information"""
        about_window = tk.Toplevel(self)
        about_window.title("About gibMacOS GUI")
        about_window.geometry("500x400")
        about_window.resizable(False, False)
        
        main_frame = ttk.Frame(about_window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        ttk.Label(
            main_frame,
            text="gibMacOS GUI",
            font=("Helvetica", 16, "bold")
        ).pack(pady=(0, 10))
        
        ttk.Label(
            main_frame,
            text="Version 2.0 (GUI Edition)",
            font=("Helvetica", 12)
        ).pack(pady=(0, 20))
        
        # Description
        desc_frame = ttk.LabelFrame(main_frame, text="Description", padding="10")
        desc_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(
            desc_frame,
            text="A graphical interface for corpnewt's gibMacOS tool that allows\ndownloading macOS installers directly from Apple's servers.",
            justify=tk.LEFT
        ).pack(anchor=tk.W)
        
        # License
        license_frame = ttk.LabelFrame(main_frame, text="License", padding="10")
        license_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(
            license_frame,
            text="MIT License\nCopyright © 2023 GPT Coding Partner",
            justify=tk.LEFT
        ).pack(anchor=tk.W)
        
        # Links
        links_frame = ttk.Frame(main_frame)
        links_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(links_frame, text="Original Project:").pack(side=tk.LEFT, padx=5)
        
        original_link = ttk.Label(
            links_frame, 
            text="github.com/corpnewt/gibMacOS", 
            foreground="blue",
            cursor="hand2"
        )
        original_link.pack(side=tk.LEFT)
        original_link.bind("<Button-1>", lambda e: webbrowser.open("https://github.com/corpnewt/gibMacOS"))
        
        # Close button
        ttk.Button(
            about_window,
            text="Close",
            command=about_window.destroy
        ).pack(pady=10)
        
        # Center window
        about_window.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() // 2) - (about_window.winfo_width() // 2)
        y = self.winfo_y() + (self.winfo_height() // 2) - (about_window.winfo_height() // 2)
        about_window.geometry(f"+{x}+{y}")

if __name__ == "__main__":
    app = GibMacOSGUI()
    print("GUI version running successfully!")
    app.mainloop()