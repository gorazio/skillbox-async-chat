#
# Серверное приложение для соединений
#
import asyncio
from asyncio import transports


class ServerProtocol(asyncio.Protocol):
    login: str = None
    server: 'Server'
    transport: transports.Transport

    def __init__(self, server: 'Server'):
        self.server = server

    def data_received(self, data: bytes):
        print(data)

        decoded = data.decode()

        if self.login is not None:
            self.send_message(decoded)
        else:
            if decoded.startswith("login:"):
                login = decoded.replace("login:", "").replace("\r\n", "") #сохраняем имя пользователя в переменную
                for user in self.server.clients: #цикл по всем пользователям сервера
                    if user.login == login: #сравниваем имя каждого пользователя с текущим
                        self.transport.write(f"Логин {login} занят, попробуйте другой".encode())
                        self.transport.close() # закрываем коннект если найдено совпадение
                self.login = login
                self.transport.write(
                    f"Привет, {self.login}!\n".encode()
                )
                self.send_history() # отправляем историю при удачном логоне
            else:
                self.transport.write("Неправильный логин\n".encode())

    def connection_made(self, transport: transports.Transport):
        self.server.clients.append(self)
        self.transport = transport
        print("Пришел новый клиент")

    def connection_lost(self):
        self.server.clients.remove(self)
        print("Клиент вышел")

    def send_message(self, content: str):
        message = f"{self.login}: {content}\n"
        self.server.history.append(message) # сохраняем сообщение в историю
        for user in self.server.clients:
            user.transport.write(message.encode())

    def send_history(self):
        for message in self.server.history[-10:]: #цикл по последним 10 сообщениям истории
            self.transport.write(message.encode()) #шлем себе сообщение из истории

class Server:
    clients: list
    messages: list #тут храним историю

    def __init__(self):
        self.clients = []
        self.history = [] # обнуляем историю на старте

    def build_protocol(self):
        return ServerProtocol(self)

    async def start(self):
        loop = asyncio.get_running_loop()

        coroutine = await loop.create_server(
            self.build_protocol,
            '127.0.0.1',
            8888
        )

        print("Сервер запущен ...")

        await coroutine.serve_forever()


process = Server()

try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print("Сервер остановлен вручную")
