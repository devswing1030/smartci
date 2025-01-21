import base64
import sys
from itertools import cycle


def XorEncrypt(data, key):
    """
    使用XOR加密数据并将结果编码为Base64格式。
    :param data: 要加密的数据（字符串）
    :param key: 密钥（字符串）
    :return: 加密后的数据，编码为Base64格式的字符串
    """
    # 将密钥和数据转换为字节序列
    key_bytes = key.encode()
    data_bytes = data.encode()

    # 使用密钥对数据进行XOR操作
    encrypted_bytes = bytes([data_byte ^ key_byte for data_byte, key_byte in zip(data_bytes, cycle(key_bytes))])

    # 将加密后的字节序列编码为Base64
    return base64.b64encode(encrypted_bytes).decode('ascii')


def XorDecrypt(encoded_data, key):
    """
    将Base64格式的加密数据解码并使用XOR解密。
    :param encoded_data: 加密后的数据，为Base64格式的字符串
    :param key: 密钥（字符串）
    :return: 解密后的原始数据字符串
    """
    # 将加密的数据从Base64格式解码
    encrypted_bytes = base64.b64decode(encoded_data)
    key_bytes = key.encode()

    # 使用密钥对数据进行XOR操作以解密
    decrypted_bytes = bytes(
        [encrypted_byte ^ key_byte for encrypted_byte, key_byte in zip(encrypted_bytes, cycle(key_bytes))])

    # 将结果转换回字符串
    return decrypted_bytes.decode('utf-8')

if __name__ == "__main__":
    import sys
    print(XorEncrypt(sys.argv[1], sys.argv[2]))
