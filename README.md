# 📦 H-Bit База — CRM для склада и заказов

Бесплатная CRM на Streamlit + Supabase.

## 🚀 Быстрый старт

### 1. Создай проект в Supabase
1. Зайди на [supabase.com](https://supabase.com) → New Project
2. Назови, например, `h-bit-crm`
3. Создай пароль от БД (сохрани!)
4. Дождись создания (2-3 минуты)

### 2. Создай таблицы (SQL Editor)
В Supabase открой **SQL Editor** и выполни:

```sql
-- Таблица заказов
CREATE TABLE orders (
    id BIGSERIAL PRIMARY KEY,
    order_number TEXT UNIQUE NOT NULL,
    date TEXT,
    sale_type TEXT,
    customer_name TEXT,
    phone TEXT,
    address TEXT,
    sale_channel TEXT,
    payment_method TEXT,
    cost_items JSONB DEFAULT '[]',
    services JSONB DEFAULT '[]',
    delivery_cost FLOAT DEFAULT 0,
    kickback FLOAT DEFAULT 0,
    total_cost FLOAT DEFAULT 0,
    total_price FLOAT DEFAULT 0,
    profit FLOAT DEFAULT 0,
    status TEXT DEFAULT 'В процессе',
    comment TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Таблица склада
CREATE TABLE stock (
    id BIGSERIAL PRIMARY KEY,
    stock_id TEXT UNIQUE NOT NULL,
    date_added TEXT,
    name TEXT,
    type TEXT,
    quantity INTEGER DEFAULT 0,
    in_stock TEXT DEFAULT 'Да',
    unit_cost FLOAT DEFAULT 0,
    supplier TEXT,
    paid_supplier TEXT DEFAULT 'Нет',
    supplier_order TEXT,
    quality TEXT DEFAULT 'Новый',
    photo TEXT,
    comment TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 3. Получи ключи
В Supabase: **Project Settings → API** → скопируй:
- `Project URL` → вставь в `SUPABASE_URL`
- `anon public key` → вставь в `SUPABASE_KEY`

### 4. Деплой на Streamlit Cloud
1. Залей код на GitHub (репозиторий)
2. Зайди на [share.streamlit.io](https://share.streamlit.io) → New app
3. Подключи репозиторий
4. В **Settings → Secrets** добавь:
   ```
   SUPABASE_URL = "https://твой-проект.supabase.co"
   SUPABASE_KEY = "твой-anon-ключ"
   ```
5. Нажми Deploy (готово через 2-3 минуты)

### 5. Открой свою CRM
Готово! Твоя CRM будет доступна по адресу:
`https://твой-username-h-bit-baza-app-xxx.streamlit.app`

---

## 📋 Функции

- ✅ Заказы со всеми полями (себестоимость, услуги, доставка, откат)
- ✅ Склад с поставщиками и качеством товара
- ✅ Фильтры по статусу, типу, поиску
- ✅ Проваливание в карточку заказа/товара
- ✅ Автонумерация заказов (H-BIT-2026-XXXX)
- ✅ Дашборд с выручкой и статистикой
- ✅ Работает без Supabase в демо-режиме (данные временные)

## 📁 Структура проекта

```
H-Bit-Baza/
├── .streamlit/
│   └── secrets.toml      # Ключи Supabase
├── app.py                # 📄 Главный файл (весь код)
├── requirements.txt      # Зависимости
├── .gitignore           
└── README.md             # 📖 Эта инструкция
```

## 💻 Локальный запуск

```bash
pip install -r requirements.txt
streamlit run app.py
```
