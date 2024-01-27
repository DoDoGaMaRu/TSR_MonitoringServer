import os
import sys
import psutil
import tkinter
import multiprocessing

from tkinter import *
from monitoring_app import MonitoringApp


lock_file_path = "monitoring.lock"


if sys.stderr is None:
    sys.stderr = open(os.devnull, 'w')
if sys.stdout is None:
    sys.stdout = open(os.devnull, 'w')


def acquire_lock():
    with open(lock_file_path, 'w') as lock_file:
        lock_file.seek(0)
        lock_file.write(str(os.getpid()))
        lock_file.flush()


def get_locker_pid():
    with open(lock_file_path, 'r') as lock_file:
        existing_pid = int(lock_file.read().strip())
        return existing_pid


def is_process_running(pid) -> bool:
    try:
        process = psutil.Process(pid)
        return process.is_running()
    except psutil.NoSuchProcess:
        return False


def show_alert(existing_pid):
    window = Tk()
    window.title('MonitoringServer')
    window.geometry("300x150+100+100")
    window.resizable(False, False)

    def close():
        window.destroy()
        window.quit()

    def terminate_process():
        try:
            process = psutil.Process(existing_pid)
            c_processes = process.children(recursive=True)
            for c_process in c_processes:
                c_process.terminate()
            process.terminate()
            os.remove(lock_file_path)
        except psutil.NoSuchProcess:
            pass
        close()

    label = tkinter.Label(window, text="서버가 이미 실행 중입니다.\n확인을 누르면, 실행 중인 서버가 종료됩니다.")
    label.pack(pady='20')

    btn_acc = Button(window, text='확인', width='20', command=terminate_process)
    btn_rej = Button(window, text='취소', width='20', command=close)
    btn_acc.pack()
    btn_rej.pack()

    window.mainloop()


if __name__ == '__main__':
    multiprocessing.freeze_support()
    if os.path.isfile(lock_file_path):
        existing_pid = get_locker_pid()
        if is_process_running(existing_pid):
            show_alert(existing_pid)
            sys.exit(0)

    try:
        acquire_lock()

        server = MonitoringApp()
        server.run()

        os.remove(lock_file_path)
    except Exception as e:
        print(e)
