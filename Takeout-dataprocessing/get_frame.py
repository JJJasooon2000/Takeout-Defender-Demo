import cv2
import time
import multiprocessing as mp
import get_result


def image_put(q):
    video_stream_path = 'rtsp://admin:@192.168.137.147:554/stream2'  # 视频流rtsp地址
    cap = cv2.VideoCapture(video_stream_path)  # 接收视频流

    while True:
        q.put(cap.read()[1])  # 读取视频流保存在队列q中"
        q.get() if q.qsize() > 1 else time.sleep(0.01)  # 定时刷新视频流q，队列大小不超过2


def image_get(q):
    import os
    picSavePath = 'C:/extract_frame'  # 自定义图片保存路径
    '''如果目录picSavePath不存在就创建这个目录'''
    if not os.path.isdir(picSavePath):
        os.makedirs(picSavePath)
    saveDir = picSavePath
    print(saveDir)
    counter = 0  # 计算帧数
    while True:
        frame = q.get()  # 读取视频帧
        if counter == 100:
            counter = 0
        counter += 1  # 命名编号+1
        imgname = "carline-%s.jpg" % str(counter)  # 图片命名
        # imgname = ("%s--%s.jpg" % (str(counter), time.strftime('%H-%M-%S', time.localtime(time.time())))) # 图片命名
        path = os.path.join(saveDir, imgname)  # 图片命名
        print(path)
        cv2.imwrite(path, frame)  # 写入图片
        cv2.imshow('frame', frame)
        cv2.waitKey(1000)  # wait for 1000ms(1s) HERE!!!!!!!!!!!!!!


def run_single_camera():
    mp.set_start_method(method='spawn')  # init
    queue = mp.Queue(maxsize=2)  # 视频流队列大小为2
    processes = [mp.Process(target=image_put, args=(queue,)),  # 执行第一个线程，输入视频路
                 mp.Process(target=image_get, args=(queue,)),
                 mp.Process(target=image_result, )]

    [process.start() for process in processes]  # 开始所有线程
    [process.join() for process in processes]  # 等待所有线程结束


def image_result():
    get_result.get_results()


if __name__ == '__main__':
    run_single_camera()  # 运行摄像头,从摄像头视频获取帧并保存, 同时进行处理
