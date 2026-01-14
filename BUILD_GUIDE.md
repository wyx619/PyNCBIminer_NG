# PyNCBIminer Windows 打包指南

## 快速开始

### 方法一：使用批处理脚本（推荐）

1. 双击运行 `build_windows.bat`
2. 等待打包完成
3. 在 `dist\PyNCBIminer\` 目录下找到 `PyNCBIminer.exe`

### 方法二：手动执行命令

```bash
# 激活虚拟环境
uv sync

# 运行打包
pyinstaller PyNCBIminer.spec

# 可执行文件位置
dist\PyNCBIminer.exe
```

## 打包选项说明

### PyInstaller 配置文件 (PyNCBIminer.spec)

主要配置项：

- **name**: 可执行文件名称
- **icon**: 应用程序图标
- **console**: False（不显示控制台窗口）
- **datas**: 需要打包的数据文件
  - `icons/`: 图标文件
  - `blast_parameters/`: BLAST参数文件
  - `initial_queries/`: 初始查询序列
  - `graph/`: 图形文件
- **hiddenimports**: 隐式导入的模块
- **excludes**: 排除不需要的模块以减小体积

## 常见问题

### 1. 打包后程序无法启动

**可能原因：**
- 缺少数据文件
- 隐式导入的模块未包含

**解决方法：**
- 检查 `PyNCBIminer.spec` 中的 `datas` 和 `hiddenimports` 配置
- 查看错误日志：在命令行运行 `PyNCBIminer.exe`

### 2. 程序体积过大

**优化方法：**
- 使用 UPX 压缩（已启用）
- 排除不需要的模块（已在 `excludes` 中配置）
- 考虑使用虚拟环境打包（推荐）

### 3. 杀毒软件误报

**原因：** PyInstaller 打包的程序有时会被杀毒软件误报为病毒

**解决方法：**
- 添加到杀毒软件白名单
- 使用代码签名证书（需要购买）

### 4. 缺少运行时依赖

**检查方法：**
```bash
# 在打包前检查依赖
uv pip list
```

**解决方法：**
- 确保所有依赖都已安装
- 在 `hiddenimports` 中添加缺失的模块

## 高级选项

### 创建单文件版本

修改 `PyNCBIminer.spec`：

```python
exe = EXE(
    pyz,
    a.scripts,
    [],  # 不包含 binaries 和 datas
    exclude_binaries=True,
    name='PyNCBIminer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon='src/icons/app_icon.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='PyNCBIminer',
)
```

### 添加版本信息

创建 `version_info.txt`：

```txt
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(1, 2, 12, 0),
    prodvers=(1, 2, 12, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'PyNCBIminer'),
        StringStruct(u'FileDescription', u'A powerful tool for sequence mining from NCBI database'),
        StringStruct(u'FileVersion', u'1.2.12'),
        StringStruct(u'InternalName', u'PyNCBIminer'),
        StringStruct(u'LegalCopyright', u'Copyright 2024'),
        StringStruct(u'OriginalFilename', u'PyNCBIminer.exe'),
        StringStruct(u'ProductName', u'PyNCBIminer'),
        StringStruct(u'ProductVersion', u'1.2.12')])
      ]),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
```

修改 `PyNCBIminer.spec`：

```python
exe = EXE(
    ...
    version='version_info.txt',
    ...
)
```

## 分发建议

### 1. 创建安装程序

使用 NSIS 或 Inno Setup 创建安装程序：

- [NSIS](https://nsis.sourceforge.io/)
- [Inno Setup](https://jrsoftware.org/isinfo.php)

### 2. 压缩分发

```bash
# 使用 7-Zip 压缩
7z a PyNCBIminer-1.2.12-Windows.zip dist\PyNCBIminer\
```

### 3. GitHub Releases

1. 在 GitHub 上创建 Release
2. 上传打包好的文件
3. 提供下载链接

## 测试清单

打包完成后，请测试以下功能：

- [ ] 程序能正常启动
- [ ] 界面显示正常
- [ ] 所有菜单功能正常
- [ ] BLAST 搜索功能正常
- [ ] 序列下载功能正常
- [ ] 序列过滤功能正常
- [ ] 序列比对功能正常
- [ ] 数据文件读写正常
- [ ] 程序关闭功能正常（包括淡出动画）

## 联系方式

如有问题，请提交 Issue 或联系开发团队。
