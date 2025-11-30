import unittest
import os
import tempfile
import numpy as np
import wave

# Импортируем из нового файла
from audio_steganography import AudioSteganography


class TestAudioSteganography(unittest.TestCase):

    def setUp(self):
        """Настройка перед каждым тестом"""
        self.stego = AudioSteganography()
        self.test_audio_path = self.create_test_audio()
        self.test_text = "Hello, World! This is a test message."
        self.test_password = "strong_password123"

    def tearDown(self):
        """Очистка после каждого теста"""
        if os.path.exists(self.test_audio_path):
            os.remove(self.test_audio_path)

    def create_test_audio(self, duration=1, sample_rate=44100, amplitude=1000):
        """Создание тестового WAV файла (уменьшена длительность для скорости)"""
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            temp_path = f.name
        t = np.linspace(0, duration, int(sample_rate * duration))
        # Генерируем синусоидальный сигнал
        signal = (amplitude * np.sin(2 * np.pi * 440 * t)).astype(np.int16)
        with wave.open(temp_path, 'wb') as wav_file:
            wav_file.setnchannels(1)  # моно
            wav_file.setsampwidth(2)  # 16 бит
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(signal.tobytes())
        return temp_path

    def test_1_text_binary_conversion(self):
        """Тест преобразования текста в бинарный формат и обратно"""
        print("\n=== Тест 1: Преобразование текста в бинарный формат ===")
        # Преобразование текста в бинарный формат
        binary = self.stego.text_to_binary(self.test_text)
        self.assertIsNotNone(binary)
        self.assertIsInstance(binary, str)
        self.assertTrue(all(bit in '01' for bit in binary))
        # Обратное преобразование
        restored_text = self.stego.binary_to_text(binary)
        self.assertEqual(self.test_text, restored_text)
        print(f"Исходный текст: {self.test_text}")
        print(f"Бинарная длина: {len(binary)} бит")
        print(f"Восстановленный текст: {restored_text}")
        print("✓ Преобразование текст↔бинарный работает корректно")

    def test_2_aes_encryption_decryption(self):
        """Тест шифрования и дешифрования AES"""
        print("\n=== Тест 2: Шифрование и дешифрование AES ===")
        # Шифрование
        encrypted_data = self.stego.encrypt_aes(self.test_text, self.test_password)
        self.assertIsNotNone(encrypted_data)
        self.assertIn('salt', encrypted_data)
        self.assertIn('nonce', encrypted_data)
        self.assertIn('ciphertext', encrypted_data)
        self.assertIn('tag', encrypted_data)
        # Преобразование в бинарный формат и обратно
        binary_data = self.stego.encrypted_data_to_binary(encrypted_data)
        self.assertIsNotNone(binary_data)
        restored_encrypted_data = self.stego.binary_to_encrypted_data(binary_data)
        self.assertIsNotNone(restored_encrypted_data)
        # Дешифрование
        decrypted_text = self.stego.decrypt_aes(restored_encrypted_data, self.test_password)
        self.assertEqual(self.test_text, decrypted_text)
        print(f"Исходный текст: {self.test_text}")
        print(f"Зашифрованные данные: {len(encrypted_data)} компонентов")
        print(f"Бинарная длина: {len(binary_data)} бит")
        print(f"Дешифрованный текст: {decrypted_text}")
        print("✓ Шифрование и дешифрование AES работают корректно")

    def test_3_capacity_calculation(self):
        """Тест расчета емкости аудиофайла"""
        print("\n=== Тест 3: Расчет емкости аудиофайла ===")
        capacity = self.stego.calculate_capacity(self.test_audio_path)[1]
        self.assertIsNotNone(capacity)
        required_keys = ['total_samples', 'total_bits', 'total_bytes',
                         'usable_bytes', 'encrypted_usable_bytes']
        for key in required_keys:
            self.assertIn(key, capacity)
            self.assertIsInstance(capacity[key], (int, float))
            self.assertGreater(capacity[key], 0)
        print(f"Общая емкость: {capacity['total_bytes']} байт")
        print(f"Полезная емкость: {capacity['usable_bytes']} байт")
        print(f"Емкость для шифрованных данных: ~{capacity['encrypted_usable_bytes']} байт")
        print("✓ Расчет емкости работает корректно")

    def test_4_encode_decode_without_encryption(self):
        """Тест кодирования и декодирования без шифрования"""
        print("\n=== Тест 4: Кодирование/декодирование без шифрования ===")
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            output_path = f.name
        try:
            # Кодирование
            self.stego.encode_audio(self.test_audio_path, self.test_text, output_path)
            self.assertTrue(os.path.exists(output_path))
            # Проверка размера файла
            original_size = os.path.getsize(self.test_audio_path)
            encoded_size = os.path.getsize(output_path)
            self.assertEqual(original_size, encoded_size)
            # Декодирование
            decoded_text = self.stego.decode_audio(output_path)[1]
            self.assertEqual(self.test_text, decoded_text)
            print(f"Исходный текст: {self.test_text}")
            print(f"Декодированный текст: {decoded_text}")
            print(f"Размер исходного аудио: {original_size} байт")
            print(f"Размер закодированного аудио: {encoded_size} байт")
            print("✓ Кодирование/декодирование без шифрования работает корректно")
        finally:
            if os.path.exists(output_path):
                os.remove(output_path)

    def test_5_encode_decode_with_encryption(self):
        """Тест кодирования и декодирования с шифрованием"""
        print("\n=== Тест 5: Кодирование/декодирование с шифрованием ===")
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            output_path = f.name
        try:
            # Кодирование с шифрованием
            self.stego.encode_audio(self.test_audio_path, self.test_text,
                                    output_path, self.test_password)
            self.assertTrue(os.path.exists(output_path))
            # Декодирование с правильным паролем
            decoded_text = self.stego.decode_audio(output_path, self.test_password)[1]
            self.assertEqual(self.test_text, decoded_text)
            # Попытка декодирования с неправильным паролем
            wrong_password_decoded = self.stego.decode_audio(output_path, "wrong_password")[1]
            # При неправильном пароле может вернуться None или некорректный текст
            self.assertNotEqual(self.test_text, wrong_password_decoded)
            print(f"Исходный текст: {self.test_text}")
            print(f"Декодированный с правильным паролем: {decoded_text}")
            print(f"Декодированный с неправильным паролем: {wrong_password_decoded}")
            print("✓ Кодирование/декодирование с шифрованием работает корректно")
        finally:
            if os.path.exists(output_path):
                os.remove(output_path)

    def test_6_error_handling(self):
        """Тест обработки ошибок"""
        print("\n=== Тест 6: Обработка ошибок ===")
        # Несуществующий файл
        result = self.stego.calculate_capacity("nonexistent.wav")
        self.assertEqual(False, result[0])
        print("✓ Обработка ошибок работает корректно")

    def test_7_binary_edge_cases(self):
        """Тест граничных случаев бинарных преобразований"""
        print("\n=== Тест 7: Граничные случаи бинарных преобразований ===")
        # Пустая строка
        empty_binary = self.stego.text_to_binary("")
        empty_restored = self.stego.binary_to_text(empty_binary)
        self.assertEqual("", empty_restored)
        # Специальные символы
        special_chars = "!@#$%^&*()\n\t\r"
        special_binary = self.stego.text_to_binary(special_chars)
        special_restored = self.stego.binary_to_text(special_binary)
        self.assertEqual(special_chars, special_restored)
        print("✓ Граничные случаи бинарных преобразований обрабатываются корректно")


if __name__ == '__main__':
    # Запуск тестов
    unittest.main(verbosity=2)
