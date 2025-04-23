# 护目君 - 智能护眼助手 (EyeProtector)

[![GitHub stars](https://img.shields.io/github/stars/zaijun91/-?style=social)](https://github.com/zaijun91/-/stargazers)

一款免费、开源的 Windows 护眼软件，旨在通过智能调节屏幕色温和亮度，减少蓝光和眩光对眼睛的刺激，并提供定时休息提醒，帮助您养成健康的用眼习惯。

---

## ✨ 为普通用户

长时间面对电脑屏幕感到眼睛疲劳、干涩？“护目君”可以帮您！

*   **智能过滤蓝光**：自动或手动调整屏幕色温，让屏幕光线更柔和，减少刺眼的蓝光。
*   **缓解屏幕眩光**：根据环境光线（需硬件支持）或手动调节屏幕亮度，让屏幕不再晃眼。
*   **定时休息提醒**：遵循“20-20-20”法则，每隔一段时间提醒您放松眼睛，看看远方。
*   **开机自启**：设置后可随 Windows 启动，默默守护您的眼睛。
*   **简单易用**：清爽的界面，简单的操作，无需复杂设置。

**⬇️ 下载安装包**

我们强烈建议您直接下载我们为您打包好的安装程序，简单几步即可完成安装：

👉 [**点击这里下载最新版安装包 (护目君_Setup_v1.0.exe)**](https://github.com/zaijun91/-/raw/main/Output/%E6%8A%A4%E7%9B%AE%E5%90%9B_Setup_v1.0.exe)

*注意：下载链接指向 GitHub 仓库中的文件。如果下载速度慢，可能需要网络工具辅助。*

---

## 🔧 为专业用户 / 开发者

本项目旨在探索和实践使用 Python 构建实用的 Windows 桌面应用。

**技术栈:**

*   **核心语言**: Python 3
*   **GUI 框架**: PySide6 (Qt for Python)
*   **屏幕控制**:
    *   色温调节: 调用 Windows API `SetDeviceGammaRamp` (通过 `ctypes` 实现，参考 `gamma_controller.py`)
    *   亮度调节: 调用 Windows API `SetMonitorBrightness` (通过 `ctypes` 实现，参考 `brightness_controller.py`)
*   **系统交互**:
    *   热键注册: `pynput` 库
    *   开机启动: 修改注册表 (`winreg`)
    *   定时器: `QTimer`
*   **打包**: PyInstaller
*   **安装包制作**: Inno Setup

**项目结构:**

```
EyeProtector/
├── .gitignore         # Git 忽略配置
├── EyeProtector.iss   # Inno Setup 脚本
├── EyeProtector.spec  # PyInstaller 配置文件 (备用)
├── Mind.ico           # 应用图标
├── README.md          # 就是您现在看到的文件
├── brightness_controller.py # 亮度控制模块
├── gamma_controller.py    # 色温控制模块
├── hotkey_manager.py      # 热键管理模块
├── main.py            # 主程序入口
├── main_window.py     # 主窗口 UI 和逻辑
├── reminder_manager.py  # 定时提醒模块
├── requirements.txt   # Python 依赖库
├── settings_manager.py  # 配置读写模块
├── startup_manager.py   # 开机启动管理模块
├── stats_manager.py     # 数据统计模块 (待完善)
├── 护目君.spec        # PyInstaller 配置文件 (主要使用)
├── build/             # PyInstaller 构建目录 (已忽略)
├── dist/              # PyInstaller 输出目录 (已忽略)
└── Output/            # Inno Setup 输出目录 (已忽略)
    └── 护目君_Setup_v1.0.exe # 生成的安装包
```

**如何运行源码:**

1.  确保安装了 Python 3 环境。
2.  克隆仓库: `git clone https://github.com/zaijun91/-.git`
3.  进入目录: `cd EyeProtector`
4.  (可选但推荐) 创建虚拟环境: `python -m venv venv` 并激活 (`venv\Scripts\activate` on Windows)
5.  安装依赖: `pip install -r requirements.txt`
6.  运行主程序: `python main.py`

**如何自行打包:**

1.  确保安装了 PyInstaller: `pip install pyinstaller`
2.  运行打包命令: `pyinstaller 护目君.spec` (注意使用的是中文名的 spec 文件)
3.  打包后的可执行文件位于 `dist/HuMuJun.exe`。

**如何制作安装包:**

1.  确保安装了 [Inno Setup](https://jrsoftware.org/isinfo.php)。
2.  将打包好的 `dist/HuMuJun.exe` 和 `Mind.ico` 放在 `EyeProtector` 目录下。
3.  使用 Inno Setup Compiler 编译 `EyeProtector.iss` 脚本。
    *   可以通过命令行: `"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" EyeProtector.iss`
    *   或者使用 Inno Setup GUI 打开 `.iss` 文件并编译。
4.  生成的安装包位于 `Output/护目君_Setup_v1.0.exe`。

---

## ⭐ 支持我们

如果您觉得“护目君”对您有帮助，请在 GitHub 上给我们点一个 Star ⭐！您的支持是我们持续改进的最大动力！

[![GitHub stars](https://img.shields.io/github/stars/zaijun91/-?style=social)](https://github.com/zaijun91/-/stargazers)
