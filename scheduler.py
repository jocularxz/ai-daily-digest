import schedule
import time
import subprocess
import sys
import os
from datetime import datetime


def run_daily_task():
    print(f"\n{'=' * 50}")
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 开始执行每日任务...")
    print("=" * 50)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    main_py = os.path.join(script_dir, "main.py")

    result = subprocess.run([sys.executable, main_py], capture_output=False)

    if result.returncode == 0:
        print(f"\n[{datetime.now()}] 任务执行成功")
    else:
        print(f"\n[{datetime.now()}] 任务执行失败")


if __name__ == "__main__":
    print("=" * 50)
    print("  AI每日速递 - 后台调度器")
    print("  每天中午12:00自动推送")
    print("  按 Ctrl+C 退出")
    print("=" * 50)

    schedule.every().day.at("12:00").do(run_daily_task)

    next_run = schedule.next_run()
    print(f"\n下次运行时间: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")

    print("\n等待中... (程序会一直运行，请最小化窗口)")

    try:
        while True:
            schedule.run_pending()
            time.sleep(60)
    except KeyboardInterrupt:
        print("\n\n已退出调度器")
