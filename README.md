# 小红书图片工作台

Windows 单机桌面工具，用于制作小红书图片笔记、商品主图和详情图。

## 第一阶段能力

- Electron 桌面壳
- Python FastAPI 本地后端
- 健康检查
- 设置读写
- 项目目录创建
- 本地日志

## 环境

- Windows
- Python 3
- Electron: `D:\WindowsUtils\Electron\electron-v30.5.1-win32-x64`

## 安装 Python 依赖

```powershell
python -m pip install -r requirements.txt
```

如果系统 `python` 命令不可用，可以使用 Codex 自带 Python：

```powershell
C:\Users\WeiWei\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pip install -r requirements.txt
```

## 运行后端

```powershell
python -m backend.server
```

## 运行桌面端

```powershell
& 'D:\WindowsUtils\Electron\electron-v30.5.1-win32-x64\electron.exe' 'G:\CodeWork\CodeX\xhsPicture\app\electron'
```

## 测试

```powershell
python -m pytest tests/backend -v
node --test app/electron/tests/main.test.js
```
