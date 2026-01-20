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
    if sys.platform == "win32":
        # Windows 平台：完全隐藏命令行窗口
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.dwFlags |= subprocess.STARTF_USESTDHANDLES
        startupinfo.wShowWindow = subprocess.SW_HIDE
        creationflags = subprocess.CREATE_NO_WINDOW

        # 使用 Popen 而不是 run，提供更好的控制
        process = subprocess.Popen(
            command,
            shell=shell,
            startupinfo=startupinfo,
            creationflags=creationflags,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.DEVNULL,
        )
        stdout, stderr = process.communicate()

        # 打印错误信息以便调试
        if stderr:
            print(f"Error: {stderr.decode('utf-8', errors='ignore')}")

        return subprocess.CompletedProcess(
            args=command, returncode=process.returncode, stdout=stdout, stderr=stderr
        )
    else:
        # 非 Windows 平台
        return subprocess.run(command, shell=shell, capture_output=False, text=False)
