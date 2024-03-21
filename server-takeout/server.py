import multiprocessing as mp
import os
import server_local


def servers():
    processes = [mp.Process(target=server_local.local, ),
                 mp.Process(target=workers, ),
                 ]  # 执行第三个线程，上传视频流
    [process.start() for process in processes]  # 开始所有线程
    [process.join() for process in processes]  # 等待所有线程结束


def workers():
    print("服务器开启")
    os.system(r'"C:/natapp/natapp.exe"')


if __name__ == '__main__':
    servers()
