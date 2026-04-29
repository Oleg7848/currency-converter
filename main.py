import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
import urllib.request
import urllib.error
import ssl


class CurrencyConverter:
    """Главный класс приложения Конвертер валют (только встроенные модули)"""
    
    def __init__(self, root: tk.Tk):
        """
        Инициализация приложения
        
        Args:
            root: главное окно Tkinter
        """
        self.root = root
        self.root.title("Currency Converter")
        self.root.geometry("700x500")
        self.root.resizable(False, False)
        
        # API ключ (замените на свой или оставьте пустым для демо-режима)
        self.api_key = ""  # Оставьте пустым для демо-режима
        
        # Популярные валюты
        self.currencies = [
            "USD", "EUR", "GBP", "JPY", "CNY", 
            "RUB", "CAD", "AUD", "CHF", "KRW",
            "INR", "BRL", "MXN", "SEK", "NOK"
        ]
        
        # Демо-курсы валют (используются если нет API ключа или нет интернета)
        self.demo_rates = {
            "USD": 1.0,
            "EUR": 0.92,
            "GBP": 0.79,
            "JPY": 149.50,
            "RUB": 92.30,
            "CNY": 7.24,
            "CAD": 1.36,
            "AUD": 1.53,
            "CHF": 0.88,
            "KRW": 1320.0,
            "INR": 83.10,
            "BRL": 4.95,
            "MXN": 17.20,
            "SEK": 10.45,
            "NOK": 10.60
        }
        
        # Загрузка истории
        self.history_file = "history.json"
        self.conversion_history = self.load_history()
        
        # Создание интерфейса
        self.create_widgets()
        
    def create_widgets(self):
        """Создание всех элементов интерфейса"""
        # Основной фрейм
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Заголовок
        title_label = ttk.Label(
            main_frame, 
            text="Конвертер валют", 
            font=("Arial", 20, "bold")
        )
        title_label.grid(row=0, column=0, columnspan=4, pady=(0, 20))
        
        # Выбор исходной валюты
        ttk.Label(main_frame, text="Из валюты:").grid(
            row=1, column=0, sticky=tk.W, pady=5
        )
        self.from_currency = ttk.Combobox(
            main_frame, 
            values=self.currencies, 
            state="readonly",
            width=10
        )
        self.from_currency.grid(row=1, column=1, sticky=tk.W, pady=5)
        self.from_currency.set("USD")
        
        # Выбор целевой валюты
        ttk.Label(main_frame, text="В валюту:").grid(
            row=2, column=0, sticky=tk.W, pady=5
        )
        self.to_currency = ttk.Combobox(
            main_frame, 
            values=self.currencies, 
            state="readonly",
            width=10
        )
        self.to_currency.grid(row=2, column=1, sticky=tk.W, pady=5)
        self.to_currency.set("EUR")
        
        # Поле ввода суммы
        ttk.Label(main_frame, text="Сумма:").grid(
            row=3, column=0, sticky=tk.W, pady=5
        )
        
        # Валидация ввода (только цифры и точка)
        vcmd = (self.root.register(self.validate_numeric_input), '%P')
        self.amount_entry = ttk.Entry(
            main_frame, 
            width=20,
            validate='key',
            validatecommand=vcmd
        )
        self.amount_entry.grid(row=3, column=1, sticky=tk.W, pady=5)
        self.amount_entry.insert(0, "1.00")
        
        # Кнопка конвертации
        self.convert_button = ttk.Button(
            main_frame, 
            text="Конвертировать", 
            command=self.convert_currency
        )
        self.convert_button.grid(
            row=4, column=0, columnspan=2, pady=20
        )
        
        # Кнопка обновления курсов
        self.update_rates_button = ttk.Button(
            main_frame,
            text="Обновить курсы",
            command=self.update_exchange_rates
        )
        self.update_rates_button.grid(
            row=4, column=2, columnspan=2, pady=20
        )
        
        # Результат
        self.result_label = ttk.Label(
            main_frame, 
            text="", 
            font=("Arial", 14, "bold")
        )
        self.result_label.grid(
            row=5, column=0, columnspan=4, pady=10
        )
        
        # Информация о режиме работы
        self.mode_label = ttk.Label(
            main_frame,
            text="",
            font=("Arial", 9, "italic")
        )
        self.mode_label.grid(
            row=6, column=0, columnspan=4
        )
        self.update_mode_label()
        
        # Таблица истории
        ttk.Label(
            main_frame, 
            text="История конвертаций:", 
            font=("Arial", 12, "bold")
        ).grid(row=7, column=0, columnspan=4, sticky=tk.W, pady=(20, 5))
        
        # Создание таблицы
        self.create_history_table(main_frame)
        
        # Кнопка очистки истории
        clear_button = ttk.Button(
            main_frame,
            text="Очистить историю",
            command=self.clear_history
        )
        clear_button.grid(row=9, column=0, columnspan=2, pady=10)
        
        # Кнопка экспорта истории
        export_button = ttk.Button(
            main_frame,
            text="Экспорт истории",
            command=self.export_history
        )
        export_button.grid(row=9, column=2, columnspan=2, pady=10)
        
    def validate_numeric_input(self, value: str) -> bool:
        """
        Валидация ввода - только цифры и одна точка
        
        Args:
            value: введенное значение
            
        Returns:
            bool: True если ввод корректен
        """
        if value == "":
            return True
        
        # Проверяем, что ввод содержит только цифры и не более одной точки
        if value.count('.') > 1:
            return False
        
        # Проверяем каждый символ
        for char in value:
            if not char.isdigit() and char != '.':
                return False
        
        return True
        
    def create_history_table(self, parent):
        """Создание таблицы истории конвертаций"""
        # Фрейм для таблицы и скроллбара
        table_frame = ttk.Frame(parent)
        table_frame.grid(
            row=8, column=0, columnspan=4, sticky=(tk.W, tk.E)
        )
        
        # Скроллбар
        scrollbar = ttk.Scrollbar(table_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Таблица
        self.history_table = ttk.Treeview(
            table_frame,
            columns=("Дата", "Из", "В", "Сумма", "Результат", "Курс"),
            show="headings",
            height=10,
            yscrollcommand=scrollbar.set
        )
        
        # Определение столбцов
        self.history_table.heading("Дата", text="Дата")
        self.history_table.heading("Из", text="Из")
        self.history_table.heading("В", text="В")
        self.history_table.heading("Сумма", text="Сумма")
        self.history_table.heading("Результат", text="Результат")
        self.history_table.heading("Курс", text="Курс")
        
        # Ширина столбцов
        self.history_table.column("Дата", width=150)
        self.history_table.column("Из", width=70)
        self.history_table.column("В", width=70)
        self.history_table.column("Сумма", width=100)
        self.history_table.column("Результат", width=120)
        self.history_table.column("Курс", width=100)
        
        self.history_table.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.history_table.yview)
        
        # Загрузка истории в таблицу
        self.update_history_table()
    
    def update_mode_label(self):
        """Обновление информации о режиме работы"""
        if not self.api_key:
            self.mode_label.config(
                text="Режим: Демо (встроенные курсы)",
                foreground="orange"
            )
        else:
            self.mode_label.config(
                text=f"Режим: API (ключ: {self.api_key[:8]}...)",
                foreground="green"
            )
        
    def validate_amount(self, amount_str: str) -> Optional[float]:
        """
        Проверка корректности ввода суммы
        
        Args:
            amount_str: строка с суммой
            
        Returns:
            float или None: сумма как число или None при ошибке
        """
        if not amount_str:
            messagebox.showerror(
                "Ошибка", 
                "Пожалуйста, введите сумму!"
            )
            return None
            
        try:
            amount = float(amount_str)
            if amount <= 0:
                messagebox.showerror(
                    "Ошибка", 
                    "Сумма должна быть положительным числом!"
                )
                return None
            if amount > 999999999:
                messagebox.showerror(
                    "Ошибка", 
                    "Сумма слишком большая!"
                )
                return None
            return amount
        except ValueError:
            messagebox.showerror(
                "Ошибка", 
                "Пожалуйста, введите корректное число!"
            )
            return None
    
    def get_exchange_rate_api(self, from_curr: str, to_curr: str) -> Optional[float]:
        """
        Получение курса валют через API
        
        Args:
            from_curr: исходная валюта
            to_curr: целевая валюта
            
        Returns:
            float или None: курс обмена
        """
        if not self.api_key:
            return None
            
        try:
            # Создаем контекст SSL
            context = ssl.create_default_context()
            
            # Формируем URL
            url = f"https://v6.exchangerate-api.com/v6/{self.api_key}/latest/{from_curr}"
            
            # Создаем запрос
            request = urllib.request.Request(url)
            request.add_header('User-Agent', 'CurrencyConverter/1.0')
            
            # Выполняем запрос
            with urllib.request.urlopen(request, context=context, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
                
                if data.get("result") == "success":
                    rates = data.get("conversion_rates", {})
                    return rates.get(to_curr)
                else:
                    error_type = data.get("error-type", "unknown")
                    raise Exception(f"API Error: {error_type}")
                    
        except urllib.error.HTTPError as e:
            if e.code == 403:
                messagebox.showerror(
                    "Ошибка API",
                    "Неверный API ключ. Проверьте ключ или используйте демо-режим."
                )
            else:
                messagebox.showerror(
                    "Ошибка HTTP",
                    f"Ошибка HTTP {e.code}: {e.reason}"
                )
            return None
        except urllib.error.URLError as e:
            messagebox.showerror(
                "Ошибка сети",
                f"Не удалось подключиться к API: {str(e.reason)}"
            )
            return None
        except json.JSONDecodeError:
            messagebox.showerror(
                "Ошибка данных",
                "Получены некорректные данные от API"
            )
            return None
        except Exception as e:
            messagebox.showerror(
                "Ошибка", 
                f"Ошибка при получении курса: {str(e)}"
            )
            return None
    
    def update_exchange_rates(self):
        """Обновление курсов валют через API"""
        if not self.api_key:
            messagebox.showinfo(
                "Демо-режим",
                "API ключ не установлен. Используются встроенные курсы."
            )
            return
            
        try:
            context = ssl.create_default_context()
            url = f"https://v6.exchangerate-api.com/v6/{self.api_key}/latest/USD"
            
            request = urllib.request.Request(url)
            request.add_header('User-Agent', 'CurrencyConverter/1.0')
            
            with urllib.request.urlopen(request, context=context, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
                
                if data.get("result") == "success":
                    self.demo_rates = data.get("conversion_rates", {})
                    messagebox.showinfo(
                        "Успех",
                        "Курсы валют успешно обновлены!"
                    )
                else:
                    raise Exception("API вернул ошибку")
                    
        except Exception as e:
            messagebox.showerror(
                "Ошибка обновления",
                f"Не удалось обновить курсы: {str(e)}"
            )
    
    def get_exchange_rate(self, from_curr: str, to_curr: str) -> Optional[float]:
        """
        Получение курса валют (API или демо)
        
        Args:
            from_curr: исходная валюта
            to_curr: целевая валюта
            
        Returns:
            float или None: курс обмена
        """
        if from_curr == to_curr:
            return 1.0
            
        # Пробуем получить курс через API
        if self.api_key:
            rate = self.get_exchange_rate_api(from_curr, to_curr)
            if rate is not None:
                return rate
        
        # Используем демо-курсы
        if from_curr in self.demo_rates and to_curr in self.demo_rates:
            return self.demo_rates[to_curr] / self.demo_rates[from_curr]
        
        return None
    
    def convert_currency(self):
        """Выполнение конвертации валют"""
        # Получение данных из полей
        from_curr = self.from_currency.get()
        to_curr = self.to_currency.get()
        amount_str = self.amount_entry.get()
        
        # Валидация суммы
        amount = self.validate_amount(amount_str)
        if amount is None:
            return
        
        # Проверка выбора валют
        if from_curr == to_curr:
            messagebox.showinfo(
                "Информация", 
                "Вы выбрали одинаковые валюты для конвертации!"
            )
            return
        
        # Получение курса
        rate = self.get_exchange_rate(from_curr, to_curr)
        if rate is None:
            messagebox.showerror(
                "Ошибка",
                "Не удалось получить курс для выбранных валют"
            )
            return
        
        # Расчет результата
        result = amount * rate
        
        # Отображение результата
        self.result_label.config(
            text=f"{amount:.2f} {from_curr} = {result:.2f} {to_curr}\n"
                 f"Курс: 1 {from_curr} = {rate:.4f} {to_curr}"
        )
        
        # Сохранение в историю
        self.save_to_history(from_curr, to_curr, amount, result, rate)
        
    def save_to_history(
        self, 
        from_curr: str, 
        to_curr: str, 
        amount: float, 
        result: float, 
        rate: float
    ):
        """
        Сохранение конвертации в историю
        
        Args:
            from_curr: исходная валюта
            to_curr: целевая валюта
            amount: сумма для конвертации
            result: результат конвертации
            rate: курс обмена
        """
        conversion = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "from_currency": from_curr,
            "to_currency": to_curr,
            "amount": round(amount, 2),
            "result": round(result, 2),
            "rate": round(rate, 4)
        }
        
        self.conversion_history.append(conversion)
        
        # Ограничение истории до 100 записей
        if len(self.conversion_history) > 100:
            self.conversion_history = self.conversion_history[-100:]
        
        self.save_history()
        self.update_history_table()
    
    def load_history(self) -> List[Dict[str, Any]]:
        """
        Загрузка истории из JSON файла
        
        Returns:
            list: список записей истории
        """
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as file:
                    history = json.load(file)
                    if isinstance(history, list):
                        return history
            except (json.JSONDecodeError, IOError) as e:
                print(f"Ошибка загрузки истории: {e}")
        return []
    
    def save_history(self):
        """Сохранение истории в JSON файл"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as file:
                json.dump(
                    self.conversion_history, 
                    file, 
                    ensure_ascii=False, 
                    indent=2
                )
        except IOError as e:
            messagebox.showerror(
                "Ошибка", 
                f"Не удалось сохранить историю: {str(e)}"
            )
    
    def update_history_table(self):
        """Обновление таблицы истории"""
        # Очистка таблицы
        for item in self.history_table.get_children():
            self.history_table.delete(item)
        
        # Добавление записей (в обратном порядке - новые сверху)
        for record in reversed(self.conversion_history):
            self.history_table.insert(
                "", 
                "end",
                values=(
                    record.get("date", ""),
                    record.get("from_currency", ""),
                    record.get("to_currency", ""),
                    f"{record.get('amount', 0):.2f}",
                    f"{record.get('result', 0):.2f}",
                    f"{record.get('rate', 0):.4f}"
                )
            )
    
    def clear_history(self):
        """Очистка истории конвертаций"""
        if messagebox.askyesno(
            "Подтверждение", 
            "Вы уверены, что хотите очистить всю историю?"
        ):
            self.conversion_history = []
            self.save_history()
            self.update_history_table()
            messagebox.showinfo("Успех", "История очищена!")
    
    def export_history(self):
        """Экспорт истории в отдельный файл"""
        if not self.conversion_history:
            messagebox.showinfo(
                "Информация",
                "История пуста. Нечего экспортировать."
            )
            return
            
        try:
            export_file = f"history_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(export_file, 'w', encoding='utf-8') as file:
                json.dump(
                    self.conversion_history,
                    file,
                    ensure_ascii=False,
                    indent=2
                )
            messagebox.showinfo(
                "Успех",
                f"История экспортирована в файл:\n{export_file}"
            )
        except IOError as e:
            messagebox.showerror(
                "Ошибка экспорта",
                f"Не удалось экспортировать историю: {str(e)}"
            )


def main():
    """Главная функция запуска приложения"""
    root = tk.Tk()
    
    # Установка иконки (если есть файл icon.ico)
    try:
        root.iconbitmap("icon.ico")
    except:
        pass
    
    app = CurrencyConverter(root)
    
    # Обработка закрытия окна
    def on_closing():
        if messagebox.askokcancel("Выход", "Вы уверены, что хотите выйти?"):
            root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
