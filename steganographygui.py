import os
from tkinter import filedialog, messagebox
import customtkinter as ctk
from audio_steganography import AudioSteganography

# Настройка внешнего вида CustomTkinter
ctk.set_appearance_mode("Dark")  # Режимы: "Light", "Dark", "System"
ctk.set_default_color_theme("blue")  # Темы: "blue", "green", "dark-blue"

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
