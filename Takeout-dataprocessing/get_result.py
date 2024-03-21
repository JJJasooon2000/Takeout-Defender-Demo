import json
import requests
import numpy as np
import cv2
import os
import time
import shutil
import glob


def get_results():
    counter = 0
    n_last = 0
    centers_new_last = []
    data_whole = [[128], [0], [0], [2048], ['leave']]

    while True:
        if counter == 101:
            counter = 0  # 1 - 101
            print(counter)
        else:
            counter += 1
            if os.path.exists('C:/extract_frame/carline-%s.jpg' % counter):
                time_start = time.time()
                time.sleep(0.02)  # 等待图片缓冲
                input_img_path = 'C:/extract_frame/carline-%s.jpg' % counter  # 图片路径
                print(input_img_path)  # 打印图片路径
                files = {'images': open(input_img_path, 'rb')}  # 指定上传文件
                infer_header = {
                    'X-Apig-AppCode': 'fccd71b5d0d6470ca4853936c0ba3881945be212e821497289649eab23818420'}  # 发送api访问密码
                infer_url = 'https://e27faf2cc66a42fbad2dce18747962e5.apig.cn-north-4.huaweicloudapis.com/v1/infers/acf80d48-0524-4810-9709-143ec00b023f'
                requests.packages.urllib3.disable_warnings()
                r = requests.post(infer_url, files=files, verify=False, headers=infer_header)  # 返回数据保存
                json_str = json.dumps(r.text)  # json字符转换为python字符
                json_json = json.loads(json_str)  # python字符转换为字典
                data = eval(json_json)
                print(data)

                if os.path.exists('C:/extract_frame/carline-%s.jpg' % (counter - 1)):
                    if os.path.exists('C:/extract_frame/carline-%s-c.jpg' % (counter - 1)):
                        os.remove('C:/extract_frame/carline-%s-c.jpg' % (counter - 1))
                    os.rename('C:/extract_frame/carline-%s.jpg' % (counter - 1),
                              'C:/extract_frame/carline-%s-c.jpg' % (counter - 1))  # 已检查文件

                if counter != 101:  # 跳过中转图
                    try:  # 防止云端返回数据错误导致程序终止
                        position = data['detection_boxes']  # 字典查询数据
                        m = n_last  # 上一帧外卖数
                        n = len(position)  # 本帧外卖数
                        centers_old = centers_new_last  # 上一帧中心点
                        centers_new = center(n, position)  # 计算本帧中心点
                        distances = distance(n, centers_new, m, centers_old)  # 计算距离矩阵
                        print(distances)
                        matches = match(m, n, distances)  # 距离匹配
                        print(matches)
                        if counter == 1:
                            data_whole = run_state_machine(101, n, m, matches, centers_new, distances, data_whole[0],
                                                           data_whole[1], data_whole[2], data_whole[3], data_whole[4])
                        else:
                            data_whole = run_state_machine(counter, n, m, matches, centers_new, distances,
                                                           data_whole[0],
                                                           data_whole[1], data_whole[2], data_whole[3],
                                                           data_whole[4])  # 运行状态机判别并更新
                        print(data_whole)

                        n_last = n
                        centers_new_last = centers_new  # 只有正确运行后才保存为上一参数
                        print('done')
                    except:
                        print('skip')

                print('cost %3f sec' % (time.time() - time_start))

            else:
                counter -= 1


def center(n, position):  # n为本帧外卖数，position为返回的位置信息
    centers = [[0 for i in range(2)] for j in range(n)]
    for i in range(n):
        centers[i][0] = (position[i][0] + position[i][2]) / 2
        centers[i][1] = (position[i][1] + position[i][3]) / 2
    return centers


def distance(n, centers_new, m, centers_old):  # m为上一帧外卖数
    distances = [[0 for j in range(n)] for i in range(m)]
    for j in range(n):  # 距离矩阵每一行为上一帧的
        for i in range(m):  # 某份外卖与本次各个外卖的距离
            distances[i][j] = abs(centers_new[j][0] - centers_old[i][0]) + abs(centers_new[j][1] - centers_old[i][1])
    return distances


def match(m, n, distances):
    matches = [128 for i in range(m)]
    d = np.array(distances)
    if m != 0 and n != 0:
        while max(matches) == 128 and np.amin(d) != 2048:  # 匹配还未完成
            if m == 1:  # 上一帧只有单个外卖
                matches[0] = int(np.where(d == np.amin(d))[0])
            else:
                num = len(np.where(d == np.amin(d))[0])  # 得到同等优先级匹配方案个数
                plan = np.where(d == np.amin(d))  # 保存方案
                if num == 1:
                    if matches[int(plan[0])] == 128:
                        matches[int(plan[0])] = int(plan[1])
                        d[[plan[0]], :] = 2048  # 防止重复匹配
                        d[:, [plan[1]]] = 2048  # 防止重复匹配
                else:
                    for i in range(num):  # 循环匹配
                        if matches[int(plan[0][i])] == 128:
                            matches[int(plan[0][i])] = int(plan[1][i])
                        d[[plan[0][i]], :] = 2048  # 防止重复匹配
                        d[:, [plan[1][i]]] = 2048  # 防止重复匹配
    return matches


def draw(x, y, image, ID):
    img = cv2.imread(image + '.jpg')
    cv2.circle(img, (round(x), round(y)), 10, (0, 0, 255), -1)
    cv2.imwrite(image + '-%s.jpg' % ID, img)


def run_state_machine(counter, n, m, matches, centers_new, distances, list_matches, list_centers_x, list_centers_y,
                      list_distances, list_states):
    id = [0 for i in range(m)]
    for i in range(m):  # 原有及减少外卖信息更新
        id[i] = list_matches.index(i)  # 找到match号对应的外卖编号

    for i in range(m):
        ID = id[i]
        if matches[i] != 128:
            list_distances[ID] = distances[i][matches[i]]  # 更新移动距离信息
        else:
            list_distances[ID] = 2048  # 已离开则赋极大值

        if list_states[ID] == 'new':
            if 20 <= list_distances[ID] < 2048:
                list_states[ID] = 'move'
            elif list_distances[ID] < 20:
                list_states[ID] = 'stay'
                if os.path.exists('C:/extract_frame/carline-%s-c.jpg' % (counter - 1)) and not (
                        glob.glob('C:/useful_frame/%s-0-*.jpg' % ID)):
                    image = 'C:/extract_frame/carline-%s-c' % (counter - 1)
                    draw(list_centers_y[ID], list_centers_x[ID], image, ID)
                    shutil.copy('C:/extract_frame/carline-%s-c-%s.jpg' % (counter - 1, ID), (
                            'C:/useful_frame/%s-0-%s.jpg' % (
                        ID, time.strftime('%H-%M', time.localtime(time.time())))))
            elif list_distances[ID] == 2048:
                list_states[ID] = 'leave'

        if list_states[ID] == 'move':
            if 20 <= list_distances[ID] < 2048:
                list_states[ID] = 'move'
            elif list_distances[ID] < 20:
                if os.path.exists('C:/extract_frame/carline-%s-c.jpg' % (counter - 1)) and not (
                        glob.glob('C:/useful_frame/%s-0-*.jpg' % ID)):
                    image = 'C:/extract_frame/carline-%s-c' % (counter - 1)
                    draw(list_centers_y[ID], list_centers_x[ID], image, ID)
                    shutil.copy('C:/extract_frame/carline-%s-c-%s.jpg' % (counter - 1, ID), (
                            'C:/useful_frame/%s-0-%s.jpg' % (
                        ID, time.strftime('%H-%M', time.localtime(time.time())))))
                list_states[ID] = 'stay'
            elif list_distances[ID] == 2048:
                if os.path.exists('C:/extract_frame/carline-%s-c.jpg' % (counter - 1)) and not (
                        glob.glob('C:/useful_frame/%s-1-*.jpg' % ID)):
                    image = 'C:/extract_frame/carline-%s-c' % (counter - 1)
                    draw(list_centers_y[ID], list_centers_x[ID], image, ID)
                    shutil.copy('C:/extract_frame/carline-%s-c-%s.jpg' % (counter - 1, ID), (
                            'C:/useful_frame/%s-1-%s.jpg' % (
                        ID, time.strftime('%H-%M', time.localtime(time.time())))))
                list_states[ID] = 'leave'

        if list_states[ID] == 'stay':
            if 20 <= list_distances[ID] < 2048:
                list_states[ID] = 'move'
            elif list_distances[ID] < 20:
                list_states[ID] = 'stay'
            elif list_distances[ID] == 2048:
                if os.path.exists('C:/extract_frame/carline-%s-c.jpg' % (counter - 1)) and not (
                        glob.glob('C:/useful_frame/%s-1-*.jpg' % ID)):
                    image = 'C:/extract_frame/carline-%s-c' % (counter - 1)
                    draw(list_centers_y[ID], list_centers_x[ID], image, ID)
                    shutil.copy('C:/extract_frame/carline-%s-c-%s.jpg' % (counter - 1, ID), (
                            'C:/useful_frame/%s-1-%s.jpg' % (
                        ID, time.strftime('%H-%M', time.localtime(time.time())))))
                list_states[ID] = 'leave'

        if matches[i] != 128:
            list_centers_x[ID] = centers_new[matches[i]][0]  # 更新坐标信息
            list_centers_y[ID] = centers_new[matches[i]][1]
        else:
            list_centers_x[ID] = 0
            list_centers_y[ID] = 0

        list_matches[ID] = matches[i]  # 更新配对号信息

    matches_new = [i for i in range(n) if i not in matches]  # 增加外卖信息更新
    for i in range(len(matches_new)):
        list_distances.append(0)
        list_centers_x.append(centers_new[matches_new[i]][0])
        list_centers_y.append(centers_new[matches_new[i]][1])
        list_matches.append(matches_new[i])
        list_states.append('new')

    list_whole = [list_matches, list_centers_x, list_centers_y, list_distances, list_states]
    # 整合所有信息并输出
    return list_whole
