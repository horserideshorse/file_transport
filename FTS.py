# 导入所需模块
import os.path
from socket import *
import threading
import time

# 创建一个全局的Event对象，用于控制广播线程的执行
broadcast_control_event = threading.Event()


# 发送广播的函数
def send_broadcast(control_event):
    # 创建UDP套接字并允许广播
    broadcast_socket = socket(AF_INET, SOCK_DGRAM)
    broadcast_socket.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
    while True:
        # 当控制事件未被设置时，发送广播消息
        if not control_event.is_set():
            broadcast_socket.sendto(str.encode(gethostname()), ('255.255.255.255', 10130))  # 发送主机名到指定端口
        time.sleep(1)  # 每隔一秒检查一次控制事件状态


# 主函数
def server_main():
    # 创建TCP服务器套接字
    server_socket = socket(AF_INET, SOCK_STREAM)
    server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)  # 设置端口可立即重用
    server_socket.bind((gethostbyname(gethostname()), 8888))  # 绑定IP和端口
    server_socket.listen(5)  # 监听连接
    print("服务器广播中，等待连接...")
    # 接受客户端连接
    server, client_address = server_socket.accept()
    try:
        # 验证客户端连接信息
        if server.recv(1024) == b'hello':
            server.send(b'hello')
            if server.recv(1024) == b'ok':
                if input(f"{client_address}尝试连接，输入y确认: ") == 'y':
                    server.send(b"yes")
                    print(f"连接建立，客户端地址: {client_address}")
                    broadcast_control_event.set()  # 连接成功后，设置控制事件，停止广播
                    # 根据模式进行文件或文字传输
                    mode = server.recv(1024)
                    while mode != b'exit':
                        if mode == b'f':
                            print("文件传输模式")
                            handle_file_transfer(server)
                        elif mode == b'w':
                            print("文本传输模式")
                            handle_text_transfer(server)
                        mode = server.recv(1024)
                else:
                    server.send(b'refuse')
                    print("拒绝连接")
            else:
                raise Exception("验证失败")
        else:
            raise Exception("连接请求不合法")
    except Exception as e:
        print(f'连接异常: {e}')
    finally:
        server.close()
        print("与客户端的连接已关闭。")
        broadcast_control_event.clear() # 清除控制事件，允许广播线程继续执行


# 文件传输处理函数
def handle_file_transfer(server):
    i = 0
    f_name = server.recv(1024).decode()
    if f_name != 'error':
        while True:
            if input(f"是否接收文件'{f_name}'\n输入y确认\n") == 'y':
                try:
                    server.send(b'yes')
                    f_new_name, f_extend = os.path.splitext(f_name)
                    while os.path.exists(f_name):
                        i += 1
                        f_name = f_new_name + f"({i})" + f_extend
                    with open(f_name, 'wb') as f:
                        time_s = time.time()
                        print("接收中...")
                        while True:
                            data = server.recv(1024)
                            if data != b'sc':
                                f.write(data)
                            else:
                                server.send(b'success')
                                time_t = time.time() - time_s
                                print(f"接收完成,用时{time_t:.2f}s")
                                break
                except Exception as e:
                    print(f'接收文件时出现异常: {e}')
            elif 'n':
                server.send(b'no')
                print("取消接收")
                break
            break
    else:
        print("客户端取消传输")


# 文字传输处理函数
def handle_text_transfer(server):
    while True:
        word = server.recv(1024)
        server.send(word)
        print(word.decode())
        if word == b'quit':
            print("退出文本传输模式")
            break


# 程序入口
if __name__ == "__main__":
    # 启动广播线程
    broadcast_thread = threading.Thread(target=send_broadcast, args=(broadcast_control_event,)).start()
    # 循环等待并处理客户端连接
    while True:
        server_main()
