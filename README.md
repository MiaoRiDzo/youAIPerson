# Telegram Bot Memory

Telegram-бот с продвинутой системой памяти, построенный на aiogram 3.x и SQLAlchemy 2.x.

## Структура проекта

```
/telegram-bot-memory
|-- /app
|   |-- /database
|   |   |-- __init__.py
|   |   |-- models.py       # Определение моделей SQLAlchemy
|   |   `-- engine.py       # Настройка движка и сессий SQLAlchemy
|   |-- /handlers
|   |   |-- __init__.py
|   |   `-- user_commands.py # Обработчики команд пользователя
|   |-- __init__.py
|   `-- bot.py              # Основной файл бота
|-- main.py                 # Центральная точка входа
|-- .env                    # Файл для хранения токена бота
|-- requirements.txt        # Список зависимостей
|-- requirements-minimal.txt # Минимальные зависимости
`-- README.md              # Этот файл
```

## Настройка окружения

### 1. Создание виртуального окружения

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Linux/MacOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Установка зависимостей

```bash
pip install -r requirements.txt
```

**Если возникают проблемы с установкой (ошибки компиляции):**

```bash
pip install -r requirements-minimal.txt
```

**Или установите зависимости по одной:**

```bash
pip install aiogram==3.3.0
pip install sqlalchemy==2.0.23
pip install aiosqlite==0.19.0
pip install python-dotenv==1.0.0
```

### 3. Настройка токена бота

1. Скопируйте файл `env_example.txt` в `.env`:
   ```bash
   copy env_example.txt .env
   ```

2. Отредактируйте файл `.env` и замените `'ВАШ_ТОКЕН_ЗДЕСЬ'` на ваш реальный токен бота от @BotFather.

## Запуск бота

**Рекомендуемый способ:**
```bash
python main.py
```

**Для Windows (двойной клик):**
```bash
run.bat
```

**Для Linux/MacOS:**
```bash
chmod +x run.sh
./run.sh
```

**Альтернативный способ:**
```bash
python -m app.bot
```

## Тестирование

**Проверка базы данных:**
```bash
python test_db.py
```

## Доступные команды

- `/start` - Начальная команда, регистрирует пользователя в базе данных
- `/clean` - Заглушка для будущей функции очистки

## База данных

Бот использует SQLite с асинхронным SQLAlchemy 2.x. База данных автоматически создается при первом запуске в файле `telegram_bot_memory.db`.

### Модель User

- `user_id` (BigInteger, primary_key) - ID пользователя в Telegram
- `username` (String, nullable) - Имя пользователя (@username)
- `first_name` (String) - Имя пользователя
- `created_at` (TIMESTAMP) - Время создания записи

## Технологии

- **aiogram 3.x** - Современный фреймворк для Telegram ботов
- **SQLAlchemy 2.x** - ORM для работы с базой данных
- **aiosqlite** - Асинхронный драйвер для SQLite
- **python-dotenv** - Управление переменными окружения

## Решение проблем

### Проблемы с установкой зависимостей

Если при установке возникают ошибки компиляции (особенно связанные с Rust):

1. **Попробуйте минимальные зависимости:**
   ```bash
   pip install -r requirements-minimal.txt
   ```

2. **Установите зависимости по одной:**
   ```bash
   pip install aiogram==3.3.0
   pip install sqlalchemy==2.0.23
   pip install aiosqlite==0.19.0
   pip install python-dotenv==1.0.0
   ```

3. **Обновите pip:**
   ```bash
   python -m pip install --upgrade pip
   ```

4. **Используйте предварительно скомпилированные пакеты:**
   ```bash
   pip install --only-binary=all -r requirements.txt
   ``` 