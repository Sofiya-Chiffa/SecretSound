import wave
import numpy as np
import os
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import secrets
import base64

# Настройка внешнего вида CustomTkinter
ctk.set_appearance_mode("Dark")  # Режимы: "Light", "Dark", "System"
ctk.set_default_color_theme("blue")  # Темы: "blue", "green", "dark-blue"


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
            raise Exception(f"Ошибка при шифровании: {e}")

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
            raise Exception(f"Ошибка при дешифровании: {e}")

    def encrypted_data_to_binary(self, encrypted_data):
        """Преобразование зашифрованных данных в бинарную строку"""
        try:
            # Создаем строку с разделителями для структуры данных
            data_string = f"{encrypted_data['salt']}|{encrypted_data['nonce']}|{encrypted_data['ciphertext']}|{encrypted_data['tag']}"
            # Преобразуем в бинарный формат
            binary = ''.join(format(ord(char), '08b') for char in data_string)
            return binary
        except Exception as e:
            raise Exception(f"Ошибка при преобразовании в бинарный формат: {e}")

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
            raise Exception(f"Ошибка при преобразовании из бинарного формата: {e}")

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
                binary_text = self.encrypted_data_to_binary(encrypted_data)
            else:
                binary_text = self.text_to_binary(secret_text)
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
            return True, f"Сообщение успешно закодировано!\nФайл: {output_path}\nРежим: {'Зашифровано' if password else 'Без шифрования'}"
        except Exception as e:
            return False, f"Ошибка при кодировании: {e}"

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
                    decoded_text = self.decrypt_aes(encrypted_data, password)
                    return True, decoded_text, "Сообщение успешно дешифровано"
                except Exception:
                    # Если дешифрование не удалось, пробуем как обычный текст
                    pass
            # Если дешифрование не удалось или пароль не указан, пробуем как обычный текст
            decoded_text = self.binary_to_text(binary_text)
            return True, decoded_text, "Сообщение декодировано (без шифрования)"
        except Exception as e:
            return False, "", f"Ошибка при декодировании: {e}"

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
            encrypted_usable_bytes = (usable_bytes - 100) // 2
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
            return True, capacity_info
        except Exception as e:
            return False, f"Ошибка при расчете емкости: {e}"


class SteganographyGUI:
    def __init__(self):
        self.stego = AudioSteganography()
        self.setup_gui()

    def setup_gui(self):
        # Создаем главное окно
        self.root = ctk.CTk()
        self.root.title("Аудио Стеганография с AES-256")
        self.root.geometry("800x700")
        # Создаем вкладки
        self.tabview = ctk.CTkTabview(self.root)
        self.tabview.pack(padx=20, pady=20, fill="both", expand=True)
        # Добавляем вкладки
        self.tab_encode = self.tabview.add("Кодирование")
        self.tab_decode = self.tabview.add("Декодирование")
        self.tab_capacity = self.tabview.add("Анализ емкости")
        self.setup_encode_tab()
        self.setup_decode_tab()
        self.setup_capacity_tab()

    def setup_encode_tab(self):
        # Вкладка кодирования
        ctk.CTkLabel(self.tab_encode, text="Кодирование сообщения в аудио",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        # Выбор аудиофайла
        ctk.CTkLabel(self.tab_encode, text="Исходный аудиофайл:").pack(pady=5)
        self.encode_audio_frame = ctk.CTkFrame(self.tab_encode)
        self.encode_audio_frame.pack(pady=5, fill="x", padx=20)
        self.encode_audio_path = ctk.CTkEntry(self.encode_audio_frame, placeholder_text="Выберите WAV файл...")
        self.encode_audio_path.pack(side="left", padx=5, pady=5, fill="x", expand=True)
        ctk.CTkButton(self.encode_audio_frame, text="Обзор", width=80,
                      command=self.browse_encode_audio).pack(side="right", padx=5, pady=5)
        # Сообщение для скрытия
        ctk.CTkLabel(self.tab_encode, text="Секретное сообщение:").pack(pady=5)
        self.secret_message = ctk.CTkTextbox(self.tab_encode, height=100)
        self.secret_message.pack(pady=5, fill="x", padx=20)
        # Шифрование
        self.encryption_var = ctk.BooleanVar()
        self.encryption_check = ctk.CTkCheckBox(self.tab_encode, text="Использовать AES-256 шифрование",
                                                variable=self.encryption_var)
        self.encryption_check.pack(pady=10)
        self.password_frame = ctk.CTkFrame(self.tab_encode)
        self.password_frame.pack(pady=5, fill="x", padx=20)
        ctk.CTkLabel(self.password_frame, text="Пароль:").pack(pady=5)
        self.encode_password = ctk.CTkEntry(self.password_frame, placeholder_text="Введите пароль...", show="*")
        self.encode_password.pack(pady=5, fill="x")
        # Выходной файл
        ctk.CTkLabel(self.tab_encode, text="Выходной файл:").pack(pady=5)
        self.output_frame = ctk.CTkFrame(self.tab_encode)
        self.output_frame.pack(pady=5, fill="x", padx=20)
        self.output_path = ctk.CTkEntry(self.output_frame, placeholder_text="Выберите путь для сохранения...")
        self.output_path.pack(side="left", padx=5, pady=5, fill="x", expand=True)
        ctk.CTkButton(self.output_frame, text="Обзор", width=80,
                      command=self.browse_output_audio).pack(side="right", padx=5, pady=5)
        # Кнопка кодирования
        ctk.CTkButton(self.tab_encode, text="Закодировать сообщение",
                      command=self.encode_message, height=40).pack(pady=20)
        # Статус кодирования
        self.encode_status = ctk.CTkTextbox(self.tab_encode, height=80, state="disabled")
        self.encode_status.pack(pady=10, fill="x", padx=20)

    def setup_decode_tab(self):
        # Вкладка декодирования
        ctk.CTkLabel(self.tab_decode, text="Декодирование сообщения из аудио",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        # Выбор закодированного аудиофайла
        ctk.CTkLabel(self.tab_decode, text="Закодированный аудиофайл:").pack(pady=5)
        self.decode_audio_frame = ctk.CTkFrame(self.tab_decode)
        self.decode_audio_frame.pack(pady=5, fill="x", padx=20)
        self.decode_audio_path = ctk.CTkEntry(self.decode_audio_frame, placeholder_text="Выберите WAV файл...")
        self.decode_audio_path.pack(side="left", padx=5, pady=5, fill="x", expand=True)
        ctk.CTkButton(self.decode_audio_frame, text="Обзор", width=80,
                      command=self.browse_decode_audio).pack(side="right", padx=5, pady=5)
        # Пароль для дешифрования
        ctk.CTkLabel(self.tab_decode, text="Пароль (если сообщение зашифровано):").pack(pady=5)
        self.decode_password = ctk.CTkEntry(self.tab_decode, placeholder_text="Введите пароль...", show="*")
        self.decode_password.pack(pady=5, fill="x", padx=20)
        # Кнопка декодирования
        ctk.CTkButton(self.tab_decode, text="Декодировать сообщение",
                      command=self.decode_message, height=40).pack(pady=20)
        # Результат декодирования
        ctk.CTkLabel(self.tab_decode, text="Декодированное сообщение:").pack(pady=5)
        self.decoded_message = ctk.CTkTextbox(self.tab_decode, height=150)
        self.decoded_message.pack(pady=5, fill="both", expand=True, padx=20)
        # Статус декодирования
        self.decode_status = ctk.CTkLabel(self.tab_decode, text="", text_color="gray")
        self.decode_status.pack(pady=5)

    def setup_capacity_tab(self):
        # Вкладка анализа емкости
        ctk.CTkLabel(self.tab_capacity, text="Анализ емкости аудиофайла",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        # Выбор аудиофайла для анализа
        ctk.CTkLabel(self.tab_capacity, text="Аудиофайл для анализа:").pack(pady=5)
        self.capacity_audio_frame = ctk.CTkFrame(self.tab_capacity)
        self.capacity_audio_frame.pack(pady=5, fill="x", padx=20)
        self.capacity_audio_path = ctk.CTkEntry(self.capacity_audio_frame, placeholder_text="Выберите WAV файл...")
        self.capacity_audio_path.pack(side="left", padx=5, pady=5, fill="x", expand=True)
        ctk.CTkButton(self.capacity_audio_frame, text="Обзор", width=80,
                      command=self.browse_capacity_audio).pack(side="right", padx=5, pady=5)
        # Кнопка анализа
        ctk.CTkButton(self.tab_capacity, text="Проанализировать емкость",
                      command=self.analyze_capacity, height=40).pack(pady=20)
        # Результаты анализа
        self.capacity_results = ctk.CTkTextbox(self.tab_capacity, height=300, state="disabled")
        self.capacity_results.pack(pady=10, fill="both", expand=True, padx=20)

    def browse_encode_audio(self):
        filename = filedialog.askopenfilename(filetypes=[("WAV files", "*.wav")])
        if filename:
            self.encode_audio_path.delete(0, "end")
            self.encode_audio_path.insert(0, filename)

    def browse_decode_audio(self):
        filename = filedialog.askopenfilename(filetypes=[("WAV files", "*.wav")])
        if filename:
            self.decode_audio_path.delete(0, "end")
            self.decode_audio_path.insert(0, filename)

    def browse_capacity_audio(self):
        filename = filedialog.askopenfilename(filetypes=[("WAV files", "*.wav")])
        if filename:
            self.capacity_audio_path.delete(0, "end")
            self.capacity_audio_path.insert(0, filename)

    def browse_output_audio(self):
        filename = filedialog.asksaveasfilename(defaultextension=".wav", filetypes=[("WAV files", "*.wav")])
        if filename:
            self.output_path.delete(0, "end")
            self.output_path.insert(0, filename)

    def encode_message(self):
        audio_path = self.encode_audio_path.get()
        secret_text = self.secret_message.get("1.0", "end-1c")
        output_path = self.output_path.get()
        if not audio_path or not secret_text or not output_path:
            messagebox.showerror("Ошибка", "Заполните все поля!")
            return
        if not os.path.exists(audio_path):
            messagebox.showerror("Ошибка", "Исходный аудиофайл не найден!")
            return
        password = self.encode_password.get() if self.encryption_var.get() else None
        if self.encryption_var.get() and not password:
            messagebox.showerror("Ошибка", "Введите пароль для шифрования!")
            return
        try:
            success, message = self.stego.encode_audio(audio_path, secret_text, output_path, password)
            self.encode_status.configure(state="normal")
            self.encode_status.delete("1.0", "end")
            if success:
                self.encode_status.insert("1.0", f"✓ УСПЕХ\n{message}")
            else:
                self.encode_status.insert("1.0", f"✗ ОШИБКА\n{message}")
            self.encode_status.configure(state="disabled")
        except Exception as e:
            self.encode_status.configure(state="normal")
            self.encode_status.delete("1.0", "end")
            self.encode_status.insert("1.0", f"✗ ОШИБКА\n{str(e)}")
            self.encode_status.configure(state="disabled")

    def decode_message(self):
        audio_path = self.decode_audio_path.get()
        password = self.decode_password.get() or None
        if not audio_path:
            messagebox.showerror("Ошибка", "Выберите аудиофайл!")
            return
        if not os.path.exists(audio_path):
            messagebox.showerror("Ошибка", "Аудиофайл не найден!")
            return
        try:
            success, decoded_text, status_message = self.stego.decode_audio(audio_path, password)
            self.decoded_message.delete("1.0", "end")
            if success:
                self.decoded_message.insert("1.0", decoded_text)
                self.decode_status.configure(text=f"✓ {status_message}", text_color="green")
            else:
                self.decode_status.configure(text=f"✗ {status_message}", text_color="red")
        except Exception as e:
            self.decoded_message.delete("1.0", "end")
            self.decode_status.configure(text=f"✗ Ошибка: {str(e)}", text_color="red")

    def analyze_capacity(self):
        audio_path = self.capacity_audio_path.get()
        if not audio_path:
            messagebox.showerror("Ошибка", "Выберите аудиофайл!")
            return
        if not os.path.exists(audio_path):
            messagebox.showerror("Ошибка", "Аудиофайл не найден!")
            return
        try:
            success, capacity_info = self.stego.calculate_capacity(audio_path)
            self.capacity_results.configure(state="normal")
            self.capacity_results.delete("1.0", "end")
            if success:
                info_text = f"""
=== ИНФОРМАЦИЯ О ЕМКОСТИ АУДИОФАЙЛА ===

Основные параметры:
• Общее количество сэмплов: {capacity_info['total_samples']:,}
• Длительность аудио: {capacity_info['duration_seconds']:.2f} секунд
• Частота дискретизации: {capacity_info['sample_rate']} Гц
• Количество каналов: {capacity_info['channels']}

Емкость для стеганографии:
• Общая емкость (биты): {capacity_info['total_bits']:,}
• Общая емкость (байты): {capacity_info['total_bytes']:,}
• Полезная емкость для незашифрованных данных: {capacity_info['usable_bytes']:,} символов
• Полезная емкость для зашифрованных данных: ~{capacity_info['encrypted_usable_bytes']:,} символов

Рекомендации:
• Максимальная длина текстового сообщения: {capacity_info['usable_bytes']} символов
• С учетом шифрования: ~{capacity_info['encrypted_usable_bytes']} символов
"""
                self.capacity_results.insert("1.0", info_text)
            else:
                self.capacity_results.insert("1.0", f"✗ ОШИБКА\n{capacity_info}")
            self.capacity_results.configure(state="disabled")
        except Exception as e:
            self.capacity_results.configure(state="normal")
            self.capacity_results.delete("1.0", "end")
            self.capacity_results.insert("1.0", f"✗ ОШИБКА\n{str(e)}")
            self.capacity_results.configure(state="disabled")

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    # Установка необходимых библиотек
    try:
        import customtkinter
        import cryptography
        import numpy
    except ImportError as e:
        print("Установите необходимые библиотеки:")
        print("pip install customtkinter cryptography numpy")
        exit(1)
    app = SteganographyGUI()
    app.run()
