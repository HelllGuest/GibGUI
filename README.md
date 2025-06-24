# ✨ gibMacOS GUI ✨

A user-friendly graphical interface for `gibMacOS` that automates setup and simplifies macOS downloader operations. This lightweight repository integrates seamlessly with the original `corpnewt/gibMacOS` project.

---

## 🚀 Key Advantages

✅ **Zero-Management Integration** - Automatically clones/updates original repo  
✅ **Single-Command Setup & Launch** - No complex installation steps  
✅ **Always Up-to-Date** - Uses latest `gibMacOS` version on every run  
✅ **Lightweight** - Only stores GUI-specific files (under 100KB)  
✅ **Cross-Platform** - Works on macOS, Windows, and Linux  

---

## ✨ Enhanced Features

* 🖥️ **Intuitive Tkinter Interface** - Access all functionality through visual controls
* 🔄 **Auto-Sync Engine** - Always uses latest `gibMacOS` version
* 📊 **Real-Time Download Metrics** - Progress bars, speed tracking & ETA
* ⚡ **One-Click Operations** - Catalog refresh, filtering, and downloads
* 🌐 **Catalog Management** - Public Release/Beta, Developer Seed options
* 🛑 **Graceful Cancellation** - Stop operations anytime
* 📂 **Directory Picker** - Choose download location visually
* 📜 **Integrated Console** - View background operations and logs
* ⏰ **Sleep Prevention** - `caffeinate` integration for macOS (prevents sleep during downloads)

---

## 🛠️ Prerequisites

1. **Python 3.8+** - [Download Python](https://www.python.org/downloads/)
2. **Git** - [Download Git](https://git-scm.com/downloads)
3. **Tkinter** (usually included with Python):
   ```bash
   # Linux (Debian/Ubuntu)
   sudo apt-get install python3-tk
   
   # macOS (usually pre-installed)
   brew install python-tk
   ```

---

## 🚀 Getting Started (One-Time Setup)

### Method 1: Git Clone (Recommended)
```bash
# Clone this repository
git clone https://github.com/HelllGuest/GibGUI.git

# Enter project directory
cd GibGUI

# Run the bootstrap (will auto-setup everything)
python run_gui.py
```

### Method 2: Direct Download
1. Download ZIP: [GibGUI Archive](https://github.com/HelllGuest/GibGUI/archive/main.zip)
2. Extract the archive
3. Run in terminal:
   ```bash
   cd GibGUI-main
   python run_gui.py
   ```

---

## 🔄 Daily Usage
After initial setup, simply:
```bash
cd GibGUI  # Your original clone directory
python run_gui.py
```

The script will:
1. Auto-update original `gibMacOS` repository
2. Apply GUI enhancements
3. Launch the application

---

## 🖥️ GUI Workflow

1. **Configure Settings**:
   - Select catalog type (Public Release, Beta, etc.)
   - Set maximum macOS version filter
   - Choose download directory
   - Enable sleep prevention (macOS)

   ![Settings Panel](https://via.placeholder.com/600x300?text=Configuration+Panel)

2. **Refresh Catalog**:
   - Click "Refresh Catalog" to load available versions
   - View products in treeview display

3. **Download macOS**:
   - Select desired version
   - Click "Download Selected"
   - Monitor progress in real-time

   ![Download Progress](https://via.placeholder.com/600x200?text=Download+Progress+Bar)

4. **Advanced Options**:
   - Toggle console log for debugging
   - Force catalog reload
   - Cancel ongoing operations

---

## 🐛 Troubleshooting

### Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| `Python not found` | Install Python 3.8+ and ensure it's in PATH |
| `Tkinter missing` | Install OS-specific Tkinter package |
| `Git not installed` | Install Git or use ZIP download method |
| `Download failures` | Check network connection and Apple server status |
| `Permission errors` | Run with `sudo` (macOS/Linux) or Admin (Windows) |
| `GUI not updating` | Delete `gibMacOS` folder and rerun `run_gui.py` |

### Diagnostic Steps
1. Verify file structure:
   ```
   GibGUI/
   ├── run_gui.py
   ├── gibmacos_gui.py
   └── Scripts/
       └── downloader.py
   ```

2. Check for required files:
   ```bash
   ls gibMacOS/Scripts/downloader.py  # Should exist after first run
   ```

3. Enable console logging in GUI for detailed error messages

---

## 🌟 Advanced Features

### Manual Integration (Developers)
To work with both repositories directly:
```bash
git clone https://github.com/corpnewt/gibMacOS.git
git clone https://github.com/HelllGuest/GibGUI.git

# Copy GUI components
cp GibGUI/gibmacos_gui.py gibMacOS/
cp -r GibGUI/Scripts/* gibMacOS/Scripts/

# Run GUI
cd gibMacOS
python gibmacos_gui.py
```

### Environment Variables
Control behavior with:
```bash
# Skip git pull on launch
export GIBGUI_SKIP_UPDATE=1
python run_gui.py

# Use specific gibMacOS branch
export GIBGUI_BRANCH=experimental
```

---

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create feature branch:
   ```bash
   git checkout -b enhance/gui-feature
   ```
3. Commit changes:
   ```bash
   git commit -m "Add: New download manager"
   ```
4. Push to fork:
   ```bash
   git push origin enhance/gui-feature
   ```
5. Open a pull request

---

## 📄 License

This project inherits the original `gibMacOS` license. Additional GUI components are licensed under:

```text
MIT License
Copyright (c) 2025 Anoop Kumar
```

---

## 🙏 Acknowledgments

Special thanks to:
- [corpnewt](https://github.com/corpnewt) for the amazing `gibMacOS` foundation
- Python community for Tkinter and requests library
- Apple for making macOS installers available

---

> **Note**: This project is not affiliated with Apple Inc. macOS is a trademark of Apple Inc.
