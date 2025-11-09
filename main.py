import wave
import numpy as np
import os


class AudioSteganography:
    def __init__(self):
        self.supported_formats = ['.wav']

    def text_to_binary(self, text):
        """Преобразование текста в бинарную строку"""
        binary = ''.join(format(ord(char), '08b') for char in text)
        return binary

    def binary_to_text(self, binary):
        """Преобразование бинарной строки в текст"""
        text = ''
        for i in range(0, len(binary), 8):
            byte = binary[i:i + 8]
            text += chr(int(byte, 2))
        return text

    def encode_audio(self, audio_path, secret_text, output_path):
        """Кодирование секретного текста в аудиофайл"""
        try:
            with wave.open(audio_path, 'rb') as audio:
                params = audio.getparams()
                frames = audio.readframes(audio.getnframes())
            audio_array = np.frombuffer(frames, dtype=np.int16)
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
            print(f"Сообщение успешно закодировано в {output_path}")
            print(f"Размер исходного сообщения: {len(secret_text)} символов")
            print(f"Использовано аудиосэмплов: {len(binary_text)}")
        except Exception as e:
            print(f"Ошибка при кодировании: {e}")

    def decode_audio(self, audio_path):
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
            decoded_text = self.binary_to_text(binary_text)
            print(f"Декодированное сообщение: {decoded_text}")
            print(f"Размер декодированного сообщения: {len(decoded_text)} символов")
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
            capacity_info = {
                'total_samples': len(audio_array),
                'total_bits': total_bits,
                'total_bytes': total_bytes,
                'usable_bytes': usable_bytes,
                'sample_rate': params.framerate,
                'duration_seconds': len(audio_array) / params.framerate,
                'channels': params.nchannels
            }
            return capacity_info
        except Exception as e:
            print(f"Ошибка при расчете емкости: {e}")
            return None


stego = AudioSteganography()
while True:
    print("\n=== Аудио стеганография LSB ===")
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
            print(f"\nМаксимальная длина сообщения: {capacity['usable_bytes']} символов")
        secret_text = input("Введите текст для скрытия: ")
        output_path = input("Введите путь для сохранения закодированного аудио: ")
        stego.encode_audio(audio_path, secret_text, output_path)
    elif choice == '2':
        audio_path = input("Введите путь к закодированному аудиофайлу: ")
        if not os.path.exists(audio_path):
            print("Файл не найден!")
            continue
        decoded_text = stego.decode_audio(audio_path)
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
            print(f"Полезная емкость (символы): {capacity['usable_bytes']}")
            print(f"Длительность аудио: {capacity['duration_seconds']:.2f} секунд")
            print(f"Частота дискретизации: {capacity['sample_rate']} Гц")
            print(f"Количество каналов: {capacity['channels']}")
    elif choice == '4':
        print("Выход из программы.")
        break
    else:
        print("Неверный выбор!")
