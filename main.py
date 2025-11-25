import wave
import numpy as np
import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import secrets
import base64


class AudioSteganography:
    def __init__(self):
        self.supported_formats = ['.wav']

    def encrypt_aes(self, plaintext, password):
        """Шифрование текста с использованием AES-256 в режиме GCM"""
        try:
            # Генерируем соль для ключа
            salt = secrets.token_bytes(16)
            # Генерируем ключ из пароля с помощью PBKDF2
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
                backend=default_backend()
            )
            key = kdf.derive(password.encode('utf-8'))
            # Генерируем nonce для GCM режима
            nonce = secrets.token_bytes(16)
            # Создаем шифр
            cipher = Cipher(algorithms.AES(key), modes.GCM(nonce), backend=default_backend())
            encryptor = cipher.encryptor()
            # Шифруем данные
            ciphertext = encryptor.update(plaintext.encode('utf-8')) + encryptor.finalize()
            # Получаем тег аутентификации
            tag = encryptor.tag
            # Объединяем все компоненты b кодируем в base64 для удобства хранения
            encoded_data = {
                'salt': base64.b64encode(salt).decode('utf-8'),
                'nonce': base64.b64encode(nonce).decode('utf-8'),
                'ciphertext': base64.b64encode(ciphertext).decode('utf-8'),
                'tag': base64.b64encode(tag).decode('utf-8')
            }
            return encoded_data
        except Exception as e:
            print(f"Ошибка при шифровании: {e}")
            return None

    def decrypt_aes(self, encrypted_data, password):
        """Дешифрование текста с использованием AES-256"""
        try:
            # Декодируем из base64
            salt = base64.b64decode(encrypted_data['salt'])
            nonce = base64.b64decode(encrypted_data['nonce'])
            ciphertext = base64.b64decode(encrypted_data['ciphertext'])
            tag = base64.b64decode(encrypted_data['tag'])
            # Генерируем ключ из пароля
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
                backend=default_backend()
            )
            key = kdf.derive(password.encode('utf-8'))
            # Создаем шифр для дешифрования
            cipher = Cipher(algorithms.AES(key), modes.GCM(nonce, tag), backend=default_backend())
            decryptor = cipher.decryptor()
            # Дешифруем данные
            plaintext = decryptor.update(ciphertext) + decryptor.finalize()
            return plaintext.decode('utf-8')
        except Exception as e:
            print(f"Ошибка при дешифровании: {e}")
            return None

    def encrypted_data_to_binary(self, encrypted_data):
        """Преобразование зашифрованных данных в бинарную строку"""
        try:
            # Создаем строку с разделителями для структуры данных
            data_string = f"{encrypted_data['salt']}|{encrypted_data['nonce']}|{encrypted_data['ciphertext']}|{encrypted_data['tag']}"
            # Преобразуем в бинарный формат
            binary = ''.join(format(ord(char), '08b') for char in data_string)
            return binary
        except Exception as e:
            print(f"Ошибка при преобразовании в бинарный формат: {e}")
            return None

    def binary_to_encrypted_data(self, binary_string):
        """Преобразование бинарной строки обратно в зашифрованные данные"""
        try:
            # Преобразуем бинарную строку обратно в текст
            text = ''
            for i in range(0, len(binary_string), 8):
                byte = binary_string[i:i + 8]
                if len(byte) == 8:
                    text += chr(int(byte, 2))
            # Разбираем строку с разделителями
            parts = text.split('|')
            if len(parts) != 4:
                raise ValueError("Неверный формат зашифрованных данных")
            encrypted_data = {
                'salt': parts[0],
                'nonce': parts[1],
                'ciphertext': parts[2],
                'tag': parts[3]
            }
            return encrypted_data

        except Exception as e:
            print(f"Ошибка при преобразовании из бинарного формата: {e}")
            return None

    def text_to_binary(self, text):
        """Преобразование текста в бинарную строку"""
        binary = ''.join(format(ord(char), '08b') for char in text)
        return binary

    def binary_to_text(self, binary):
        """Преобразование бинарной строки в текст"""
        text = ''
        for i in range(0, len(binary), 8):
            byte = binary[i:i + 8]
            if len(byte) == 8:
                text += chr(int(byte, 2))
        return text

    def encode_audio(self, audio_path, secret_text, output_path, password=None):
        """Кодирование секретного текста в аудиофайл с опциональным шифрованием"""
        try:
            with wave.open(audio_path, 'rb') as audio:
                params = audio.getparams()
                frames = audio.readframes(audio.getnframes())
            audio_array = np.frombuffer(frames, dtype=np.int16)
            # Шифруем текст если указан пароль
            if password:
                encrypted_data = self.encrypt_aes(secret_text, password)
                if not encrypted_data:
                    raise ValueError("Ошибка при шифровании данных")
                binary_text = self.encrypted_data_to_binary(encrypted_data)
                print("Сообщение зашифровано с использованием AES-256")
            else:
                binary_text = self.text_to_binary(secret_text)
                print("Сообщение сохранено без шифрования")
            # Добавляем маркер конца сообщения
            binary_text += '1111111111111110'
            if len(binary_text) > len(audio_array):
                raise ValueError("Текст слишком длинный для данного аудиофайла")
            # Кодируем текст в LSB аудиоданных
            encoded_audio = audio_array.copy()
            for i in range(len(binary_text)):
                # Заменяем младший бит
                if binary_text[i] == '1':
                    encoded_audio[i] = encoded_audio[i] | 1
                else:
                    encoded_audio[i] = encoded_audio[i] & ~1
            with wave.open(output_path, 'wb') as output_audio:
                output_audio.setparams(params)
                output_audio.writeframes(encoded_audio.tobytes())
            print(f"Сообщение успешно закодировано в {output_path}")
            print(f"Размер исходного сообщения: {len(secret_text)} символов")
            print(f"Использовано аудиосэмплов: {len(binary_text)}")
            print(f"Режим: {'Зашифровано' if password else 'Без шифрования'}")
        except Exception as e:
            print(f"Ошибка при кодировании: {e}")

    def decode_audio(self, audio_path, password=None):
        """Декодирование секретного текста из аудиофайла"""
        try:
            with wave.open(audio_path, 'rb') as audio:
                frames = audio.readframes(audio.getnframes())
            audio_array = np.frombuffer(frames, dtype=np.int16)
            binary_text = ''
            for sample in audio_array:
                # Извлекаем младший бит
                lsb = sample & 1
                binary_text += str(lsb)
                # Проверяем маркер конца сообщения
                if len(binary_text) >= 16 and binary_text[-16:] == '1111111111111110':
                    break
            # Удаляем маркер конца
            if binary_text.endswith('1111111111111110'):
                binary_text = binary_text[:-16]
            # Определяем, зашифрованы ли данные и пытаемся дешифровать
            if password:
                try:
                    encrypted_data = self.binary_to_encrypted_data(binary_text)
                    if encrypted_data:
                        decoded_text = self.decrypt_aes(encrypted_data, password)
                        if decoded_text:
                            print("Сообщение успешно дешифровано")
                            print(f"Декодированное сообщение: {decoded_text}")
                            print(f"Размер декодированного сообщения: {len(decoded_text)} символов")
                            return decoded_text
                except Exception as e:
                    print(f"Ошибка при дешифровании: {e}")
                    print("Попытка декодировать как незашифрованное сообщение...")
            # Если дешифрование не удалось или пароль не указан, пробуем как обычный текст
            decoded_text = self.binary_to_text(binary_text)
            print(f"Декодированное сообщение: {decoded_text}")
            print(f"Размер декодированного сообщения: {len(decoded_text)} символов")
            print("Режим: Без шифрования")
            return decoded_text
        except Exception as e:
            print(f"Ошибка при декодировании: {e}")
            return None

    def calculate_capacity(self, audio_path):
        """Расчет максимальной емкости аудиофайла для скрытия данных"""
        try:
            with wave.open(audio_path, 'rb') as audio:
                frames = audio.readframes(audio.getnframes())
                params = audio.getparams()
            audio_array = np.frombuffer(frames, dtype=np.int16)
            # Емкость в битах (каждый сэмпл может хранить 1 бит)
            total_bits = len(audio_array)
            total_bytes = total_bits // 8
            # Учитываем маркер конца (2 байта)
            usable_bytes = total_bytes - 2
            # Для зашифрованных данных емкость меньше из-за накладных расходов
            encrypted_usable_bytes = (usable_bytes - 100) // 2  # Примерная оценка
            capacity_info = {
                'total_samples': len(audio_array),
                'total_bits': total_bits,
                'total_bytes': total_bytes,
                'usable_bytes': usable_bytes,
                'encrypted_usable_bytes': encrypted_usable_bytes,
                'sample_rate': params.framerate,
                'duration_seconds': len(audio_array) / params.framerate,
                'channels': params.nchannels
            }
            return capacity_info
        except Exception as e:
            print(f"Ошибка при расчете емкости: {e}")
            return None


# Основная программа
stego = AudioSteganography()
while True:
    print("\n=== Аудио стеганография LSB с AES-256 шифрованием ===")
    print("1. Закодировать сообщение в аудио")
    print("2. Декодировать сообщение из аудио")
    print("3. Проверить емкость аудиофайла")
    print("4. Выход")
    choice = input("Выберите действие: ")
    if choice == '1':
        audio_path = input("Введите путь к исходному аудиофайлу (.wav): ")
        if not os.path.exists(audio_path):
            print("Файл не найден!")
            continue
        capacity = stego.calculate_capacity(audio_path)
        if capacity:
            print(f"\nИнформация о емкости:")
            print(f"Максимальная длина незашифрованного сообщения: {capacity['usable_bytes']} символов")
            print(f"Максимальная длина зашифрованного сообщения: ~{capacity['encrypted_usable_bytes']} символов")
        secret_text = input("Введите текст для скрытия: ")
        use_encryption = input("Использовать шифрование AES-256? (y/n): ").lower().strip()
        password = None
        if use_encryption == 'y':
            password = input("Введите пароль для шифрования: ")
            if len(password) < 8:
                print("Предупреждение: рекомендуется использовать пароль длиной не менее 8 символов")

        output_path = input("Введите путь для сохранения закодированного аудио: ")
        stego.encode_audio(audio_path, secret_text, output_path, password)
    elif choice == '2':
        audio_path = input("Введите путь к закодированному аудиофайлу: ")
        if not os.path.exists(audio_path):
            print("Файл не найден!")
            continue
        use_password = input("Сообщение зашифровано? (y/n): ").lower().strip()
        password = None
        if use_password == 'y':
            password = input("Введите пароль для дешифрования: ")
        decoded_text = stego.decode_audio(audio_path, password)
        if decoded_text:
            print(f"\nДекодированное сообщение: {decoded_text}")
    elif choice == '3':
        audio_path = input("Введите путь к аудиофайлу: ")
        if not os.path.exists(audio_path):
            print("Файл не найден!")
            continue
        capacity = stego.calculate_capacity(audio_path)
        if capacity:
            print(f"\nИнформация о емкости аудиофайла:")
            print(f"Общее количество сэмплов: {capacity['total_samples']}")
            print(f"Общая емкость (биты): {capacity['total_bits']}")
            print(f"Общая емкость (байты): {capacity['total_bytes']}")
            print(f"Полезная емкость для незашифрованных данных (символы): {capacity['usable_bytes']}")
            print(f"Полезная емкость для зашифрованных данных (символы): ~{capacity['encrypted_usable_bytes']}")
            print(f"Длительность аудио: {capacity['duration_seconds']:.2f} секунд")
            print(f"Частота дискретизации: {capacity['sample_rate']} Гц")
            print(f"Количество каналов: {capacity['channels']}")
    elif choice == '4':
        print("Выход из программы.")
        break
    else:
        print("Неверный выбор!")
