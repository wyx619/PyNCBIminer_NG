import subprocess
import sys

def run_command(command, shell=True):
    """
    执行命令并隐藏命令行窗口（适用于 Windows）
    
    Args:
        command: 要执行的命令字符串
        shell: 是否使用 shell 执行（默认为 True）
    
    Returns:
        subprocess.CompletedProcess 对象
    """
    if sys.platform == 'win32':
        # Windows 平台：隐藏命令行窗口
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        creationflags = subprocess.CREATE_NO_WINDOW
    else:
        # 非 Windows 平台
        startupinfo = None
        creationflags = None
    
    return subprocess.run(
        command,
        shell=shell,
        startupinfo=startupinfo,
        creationflags=creationflags,
        capture_output=False,
        text=False
    )
