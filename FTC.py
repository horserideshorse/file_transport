# 导入所需模块
import threading
import time
from socket import *
from tkinter import filedialog
import os

# 初始化全局变量
dat = []  # 用于存储接收到的广播数据
addr = []  # 用于存储广播数据对应的地址
num = 0  # 计数器，记录已发现的服务器数量0
receive_control_event = threading.Event()  # 控制接收线程的事件对象


# 接收广播的函数
def receive_broadcast(control_event):
    global num
    # 创建UDP套接字并允许接收广播
    s = socket(AF_INET, SOCK_DGRAM)
    s.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
    s.bind(('0.0.0.0', 10130))  # 绑定到所有网络接口的指定端口
    while True:
        # 当控制事件未设置时，接收并处理广播消息
        if not control_event.is_set():
            data, address = s.recvfrom(1024)  # 接收数据和发送者地址
            if data not in dat:  # 避免重复记录
                dat.append(data)  # 添加数据到列表
                addr.append(address)  # 添加地址到列表
                if data.decode() == gethostname():
                    print(f'{num} ' + data.decode() + "(本机)" + str(address))
                else:
                    print(f'{num} ' + data.decode() + str(address))  # 打印发现的服务器信息
                num += 1  # 增加计数器
        time.sleep(1)  # 暂停一秒，避免频繁查询


# 主函数
def main():
    global num
    try:
        n = int(input("正在搜索服务器...\n请输入要连接的服务器编号: \n"))  # 用户输入选择的服务器编号
        client = socket()  # 创建客户端TCP套接字
        client.connect((dat[n].decode(), 8888))  # 尝试连接到选中的服务器
        client.send(b'hello')  # 发送连接请求
        if client.recv(1024) == b'hello':  # 验证服务端回应
            client.send(b'ok')  # 发送确认
            print("服务端确认连接中...")
            if client.recv(1024) == b'yes':
                print("确认连接" + f"，服务端地址: {addr[n]}")  # 打印成功信息
                receive_control_event.set()  # 设置控制事件，停止广播接收
                while True:
                    mode = input('请选择模式(f: 文件传输, w: 文字传输, exit: 断开连接)\n')  # 选择传输模式
                    if mode == 'f':  # 文件传输模式
                        client.send(b'f')
                        print("文件传输模式")
                        file_transfer(client)
                    elif mode == 'w':  # 文字传输模式
                        client.send(b'w')
                        print("文本传输模式(quit退出)")
                        text_transfer(client)
                    elif mode == 'exit':
                        client.send(b'exit')
                        print("断开连接")
                        break
                    else:
                        print("无效的模式选择")
            elif b'refuse':
                raise Exception("服务端拒绝连接")
    except Exception as e:
        print(f"发生异常: {e}")
    finally:
        print("与服务端的连接已关闭")
        receive_control_event.clear()  # 清除控制事件，允许再次接收广播
        num = 0  # 重置计数器


def file_transfer(client):
    f_path = filedialog.askopenfilename()  # 选择文件
    if f_path:
        try:
            client.send(os.path.basename(f_path).encode())  # 发送文件名
            print("服务端确认中...")
            if client.recv(1024) == b'yes':
                with open(f_path, 'rb') as f:  # 打开并读取文件
                    time.sleep(0.1)
                    print("开始传输...")
                    while True:
                        data = f.read(1024)
                        if data:
                            client.send(data)
                        else:
                            time.sleep(0.1)
                            client.send(b'sc')
                            if client.recv(1024) == b'success':
                                print("文件传输完成")
                                break
                            else:
                                raise Exception("接收异常")
            else:
                print("服务端取消接收")
        except Exception as e:
            print("传输异常", e)
    else:
        client.send(b'error')
        print("取消传输")


def text_transfer(client):
    while True:
        word = input()  # 获取用户输入
        client.send(word.encode())  # 发送文字
        print("send: " + client.recv(1024).decode())
        if word == 'quit':
            break


# 程序入口
if __name__ == "__main__":
    # 启动接收广播的线程
    receive_thread = threading.Thread(target=receive_broadcast, args=(receive_control_event,)).start()
    # 进入主循环，等待用户操作
    while True:
        main()
        dat.clear()  # 清空已发现服务器列表
        addr.clear()  # 清空地址列表
