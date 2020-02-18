import sys
import socket
import base64
import time

from Crypto.Cipher import AES
from Crypto import Random

BLOCK_SIZE = 16
PADDING = ' '


# ACTIONS = ['muscle', 'weightlifting', 'shoutout', 'dumbbells', 'tornado', 'facewipe', 'pacman', 'shootingstar', 'logout']

class Client():
    def __init__(self, ip_addr, port_num, group_id, secret_key):
        super(Client, self).__init__()

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_address = (ip_addr, port_num)
        self.secret_key = secret_key
        self.socket.connect(server_address)
        # testing on laptop
        # self.timeout = 60
        print("client is connected!")

    def add_padding(self, plain_text):
        pad = lambda s: s + (BLOCK_SIZE - (len(s) % BLOCK_SIZE)) * PADDING
        padded_plain_text = pad(plain_text)
        print("padded_plain_text length: ", len(padded_plain_text))
        return padded_plain_text

    def encrypt_message(self, position, action, syncdelay):
        plain_text = '#' + position + '|' + action + '|' + syncdelay + '|'
        print("plain_text: ", plain_text)
        padded_plain_text = self.add_padding(plain_text)
        iv = Random.new().read(AES.block_size)
        aes_key = bytes(str(self.secret_key), encoding="utf8")
        cipher = AES.new(aes_key, AES.MODE_CBC, iv)
        encrypted_text = base64.b64encode(iv + cipher.encrypt(bytes(padded_plain_text, "utf8")))
        print(type(encrypted_text))
        return encrypted_text

    def send_data(self, position, action, syncdelay):
        encrypted_text = self.encrypt_message(position, action, syncdelay)
        print("encrypted_text: ", encrypted_text)
        sent_message = encrypted_text
        print("sent_message length: ", len(sent_message))
        self.socket.sendall(sent_message)

    def stop(self):
        self.connection.close()
        self.shutdown.set()
        self.timer.cancel()


def main():
    if len(sys.argv) != 5:
        print('Invalid number of arguments')
        print('python eval_client.py [IP address] [Port] [groupID] [secret key]')
        sys.exit()

    ip_addr = sys.argv[1]
    port_num = int(sys.argv[2])
    group_id = sys.argv[3]
    secret_key = sys.argv[4]

    my_client = Client(ip_addr, port_num, group_id, secret_key)
    action = ""
    # test client on laptop
    time.sleep(10)

    count = 0
    while action != "logout":
        my_client.send_data("1 2 3", "muscle", "1.00")
        time.sleep(2)
        count += 1
        if(count == 50) :
            my_client.stop()

if __name__ == '__main__':
    main()


