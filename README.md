# ✨ gibMacOS GUI ✨

A user-friendly graphical interface (GUI) for the popular `gibMacOS` tool, designed to simplify the process of downloading macOS installers. This repository contains the GUI script and a modified `downloader.py` for enhanced functionality and ease of use.

---

## 🚀 Overview

`gibMacOS GUI` provides an intuitive way to access and download various macOS installers directly from Apple's servers. Built on top of the powerful `gibMacOS` script, this GUI eliminates the need for command-line interactions, making it accessible to a wider audience. Whether you need the latest public release, a developer beta, or a specific older version, `gibMacOS GUI` puts the power of macOS downloads at your fingertips.

---

## ✨ Features

* 🖥️ **Intuitive User Interface:** A clean and easy-to-navigate Tkinter-based GUI.
* 📦 **Catalog Selection:** Easily switch between different macOS update catalogs (Public Release, Public Beta, Customer Seed, Developer Seed).
* 🔍 **Version Filtering:** Specify a maximum macOS version to filter available downloads.
* 💾 **Download Management:** Select and download macOS packages directly to your chosen directory.
* ⚡ **Download Progress & Speed:** Real-time updates on download progress, speed, and estimated time remaining.
* 🚫 **Cancellation Support:** Gracefully cancel ongoing download operations.
* 😴 **Prevent Sleep:** Option to prevent your Mac from sleeping during downloads (macOS only) using `caffeinate`.
* 📜 **Local Catalog Management:** Options to save and force re-download of the Apple catalog locally.
* 📝 **Console Logging:** View detailed background operations and status messages in an integrated console log.

---

## 🛠️ Prerequisites

Before running the setup, ensure you have the following installed:

* **Python 3.x:** Download from [python.org](https://www.python.org/downloads/).
* **Git:** Download from [git-scm.com](https://git-scm.com/downloads/).
* **`tkinter`:** Usually included with standard Python 3 installations. If you encounter issues, ensure it's installed (e.g., `sudo apt-get install python3-tk` on Debian/Ubuntu, or ensure it was selected during Windows Python installation).

All other necessary Python libraries (`requests`, `pyobjc`) will be automatically installed by the setup script.

---

## 🚀 Getting Started

Follow these simple steps to set up and run `gibMacOS GUI`:

1.  **Clone This Repository:**
    Start by cloning *this* `gibMacOS GUI` repository to your local machine:
    ```bash
    git clone https://github.com/HelllGuest/GibGUI.git
    cd GibGUI
    ```
    *(Remember to replace `https://github.com/HelllGuest/GibGUI.git` with the actual URL of your repository.)*

2.  **Run the Setup Script:**
    Execute the `setup.py` script. This script will automatically clone the original `gibMacOS` repository, install required Python dependencies, and place the modified `downloader.py` into the correct location.
    ```bash
    python setup.py
    ```
    Follow any prompts in the terminal.

3.  **Launch the GUI:**
    Once the setup script completes successfully, you can launch the GUI with a single command:
    ```bash
    python gibmacos_gui.py
    ```
    The `gibMacOS GUI` window should appear, ready for use!

---

## 💡 Usage

Once the application is running, you can:

1.  **Configure Settings:**
    * **Catalog:** Use the dropdown to select your desired catalog (e.g., "PublicRelease" for stable versions).
    * **Max macOS Version:** Enter the desired maximum major macOS version (e.g., `14` for Sonoma, `13` for Ventura).
    * **Find Recovery HDs:** Check this box to include Recovery HD images in the search.
    * **Prevent Sleep During Downloads (macOS only):** Keep your system awake while files are downloading.
    * **Save Catalog Locally:** Stores the downloaded Apple catalog plist file for faster future access.
    * **Force Local Catalog Reload:** Forces the GUI to re-download the catalog even if a local copy exists.
    * **Download Directory:** Click "Browse" to choose where downloaded macOS installers will be saved.

2.  **Refresh Catalog:**
    * Click the "Refresh Catalog" button to fetch the latest list of macOS products based on your current settings.
    * The status bar will update, and the product treeview will populate with available installers.

3.  **Download Selected Product:**
    * Select a macOS product from the list in the treeview.
    * Click the "Download Selected" button.
    * The download progress will be displayed in the status bar.

4.  **Cancel Operation:**
    * During a catalog refresh or download, click "Cancel Operation" to stop the current process.

5.  **Show Console Log:**
    * Check the "Show Console Log" checkbox in the status area to reveal a detailed log of background operations and messages. This is helpful for debugging or understanding what the script is doing.

---

## 🐛 Troubleshooting

* **"Error: Python 3 or higher is required."**: Ensure you are running the `setup.py` with `python` command that points to Python 3. If you have multiple Python versions, try `python3 setup.py`.
* **"Error: Git is not installed..."**: Install Git from [git-scm.com](https://git-scm.com/downloads/).
* **"Failed to install [package name]" during setup:** This usually indicates network issues or permission problems. Try running the pip command manually (e.g., `pip install requests`). If permissions are an issue, consider `pip install --user [package name]` or use a virtual environment.
* **GUI doesn't launch (Tkinter errors):** Ensure `tkinter` is correctly installed with your Python distribution. It's often an optional component during Python installation.
* **Downloads failing with "Download failed or was interrupted (no specific error)" or "missing positional arguments":**
    These issues suggest that the modified `downloader.py` might not have been correctly copied, or there's a version mismatch.
    1.  Ensure you cloned *this* repository correctly.
    2.  Rerun `python setup.py` to ensure the `downloader.py` is copied.
    3.  Check the `gibMacOS/Scripts/downloader.py` file to confirm it matches the corrected version you received.

---

## 🤝 Contributing

Contributions are welcome! If you have suggestions, bug reports, or want to contribute code, please feel free to:

1.  Fork the repository.
2.  Create a new branch (`git checkout -b feature/YourFeature`).
3.  Make your changes.
4.  Commit your changes (`git commit -m 'Add new feature'`).
5.  Push to the branch (`git push origin feature/YourFeature`).
6.  Open a Pull Request.

---

## 📄 License

This project incorporates the original `gibMacOS` script. Please refer to the `gibMacOS` repository for its specific licensing information. The `gibMacOS GUI` component (this repository) is licensed under the [MIT License](LICENSE) (recommended, assuming you'll add a `LICENSE` file).

---

## 🙏 Acknowledgements

This project would not be possible without the excellent work of **corpnewt** and their original `gibMacOS` script. Many thanks for providing such a valuable tool!

* **Original `gibMacOS` Repository:** [https://github.com/corpnewt/gibMacOS](https://github.com/corpnewt/gibMacOS)

---