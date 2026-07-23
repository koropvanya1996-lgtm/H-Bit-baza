# H-Bit База — CRM на Streamlit + Supabase
# Основной файл приложения

import streamlit as st
import pandas as pd
from datetime import datetime, date
import uuid
import json

# ======================== НАСТРОЙКА СТРАНИЦЫ ========================
st.set_page_config(
    page_title="H-Bit База",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ======================== ПОДКЛЮЧЕНИЕ К SUPABASE ========================
# ⚠️ ЗАМЕНИТЕ ЭТИ ДАННЫЕ НА СВОИ ПОСЛЕ СОЗДАНИЯ ПРОЕКТА В SUPABASE
SUPABASE_URL = st.secrets.get("SUPABASE_URL", "https://ваш-проект.supabase.co")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "ваш-ключ")

try:
    from supabase import create_client, Client
    sb: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    supabase_ok = True
except Exception as e:
    supabase_ok = False
    st.sidebar.warning("⚠️ Supabase не подключён. Данные хранятся временно (до перезапуска).")

# ======================== ЛОКАЛЬНОЕ ХРАНИЛИЩЕ (ЗАГЛУШКА) ========================
if "orders_db" not in st.session_state:
    st.session_state.orders_db = []
if "stock_db" not in st.session_state:
    st.session_state.stock_db = []

# ======================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ========================

def gen_order_number():
    """Генерирует номер заказа: H-BIT-2026-XXXX"""
    year = datetime.now().year
    prefix = f"H-BIT-{year}-"
    if supabase_ok:
        try:
            resp = sb.table("orders").select("order_number").order("id", desc=True).limit(1).execute()
            if resp.data:
                last_num = int(resp.data[0]["order_number"].split("-")[-1])
                return prefix + str(last_num + 1).zfill(4)
        except:
            pass
    # Локальный генератор
    existing = [o["order_number"] for o in st.session_state.orders_db if o["order_number"].startswith(prefix)]
    if existing:
        nums = [int(n.split("-")[-1]) for n in existing]
        return prefix + str(max(nums) + 1).zfill(4)
    return prefix + "0001"

def gen_stock_id():
    """Генерирует ID товара: T-2026-XXXX"""
    year = datetime.now().year
    prefix = f"T-{year}-"
    if supabase_ok:
        try:
            resp = sb.table("stock").select("stock_id").order("id", desc=True).limit(1).execute()
            if resp.data:
                last_num = int(resp.data[0]["stock_id"].split("-")[-1])
                return prefix + str(last_num + 1).zfill(4)
        except:
            pass
    existing = [s["stock_id"] for s in st.session_state.stock_db if s["stock_id"].startswith(prefix)]
    if existing:
        nums = [int(n.split("-")[-1]) for n in existing]
        return prefix + str(max(nums) + 1).zfill(4)
    return prefix + "0001"

def save_order_to_db(order_data):
    if supabase_ok:
        try:
            sb.table("orders").insert(order_data).execute()
        except Exception as e:
            st.error(f"Ошибка сохранения в Supabase: {e}")
            st.session_state.orders_db.append(order_data)
    else:
        st.session_state.orders_db.append(order_data)

def save_stock_to_db(stock_data):
    if supabase_ok:
        try:
            sb.table("stock").insert(stock_data).execute()
        except Exception as e:
            st.error(f"Ошибка сохранения в Supabase: {e}")
            st.session_state.stock_db.append(stock_data)
    else:
        st.session_state.stock_db.append(stock_data)

def load_orders():
    if supabase_ok:
        try:
            resp = sb.table("orders").select("*").order("created_at", desc=True).execute()
            return resp.data if resp.data else st.session_state.orders_db
        except:
            return st.session_state.orders_db
    return st.session_state.orders_db

def load_stock():
    if supabase_ok:
        try:
            resp = sb.table("stock").select("*").order("created_at", desc=True).execute()
            return resp.data if resp.data else st.session_state.stock_db
        except:
            return st.session_state.stock_db
    return st.session_state.stock_db

def update_order_status(order_id, new_status):
    if supabase_ok:
        try:
            sb.table("orders").update({"status": new_status}).eq("order_number", order_id).execute()
        except:
            pass
    else:
        for o in st.session_state.orders_db:
            if o["order_number"] == order_id:
                o["status"] = new_status

# ======================== ИНТЕРФЕЙС ========================

st.title("📦 H-Bit База")
st.caption("CRM для склада и заказов")

# Боковое меню
menu = st.sidebar.radio(
    "📋 Навигация",
    ["📊 Дашборд", "📋 Заказы", "📦 Склад", "➕ Новый заказ", "➕ Новый товар"]
)

# ======================== ДАШБОРД ========================
if menu == "📊 Дашборд":
    st.header("📊 Дашборд")
    
    orders = load_orders()
    stock = load_stock()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Всего заказов", len(orders))
    with col2:
        active = len([o for o in orders if o.get("status") in ["В процессе", "В доставке"]])
        st.metric("В работе", active)
    with col3:
        completed = len([o for o in orders if o.get("status") == "Завершен"])
        st.metric("Завершено", completed)
    with col4:
        total_sum = sum(float(o.get("total_price", 0) or 0) for o in orders)
        st.metric("Выручка", f"{total_sum:,.0f} ₽")
    
    # Последние заказы
    st.subheader("Последние заказы")
    if orders:
        df = pd.DataFrame(orders)
        cols = ["order_number", "date", "customer_name", "total_price", "status"]
        cols = [c for c in cols if c in df.columns]
        if cols:
            st.dataframe(df[cols].head(10), use_container_width=True, hide_index=True)
    else:
        st.info("Пока нет заказов")
    
    # Склад — заканчивается
    st.subheader("📦 Склад")
    if stock:
        df_stock = pd.DataFrame(stock)
        st.dataframe(df_stock[["stock_id", "name", "quantity", "in_stock", "supplier"]].head(10) if all(c in df_stock.columns for c in ["stock_id","name","quantity","in_stock","supplier"]) else df_stock, use_container_width=True, hide_index=True)
    else:
        st.info("Склад пуст")

# ======================== ЗАКАЗЫ ========================
elif menu == "📋 Заказы":
    st.header("📋 Все заказы")
    
    orders = load_orders()
    
    # Фильтры
    col1, col2, col3 = st.columns(3)
    with col1:
        status_filter = st.selectbox("Статус", ["Все", "В процессе", "В доставке", "Завершен"])
    with col2:
        sale_type_filter = st.selectbox("Тип продажи", ["Все", "Услуга", "Ремонт", "Диагностика", "Товар", "Сборка ПК", "Иное"])
    with col3:
        search = st.text_input("🔍 Поиск (имя, номер, телефон)", "")
    
    # Применяем фильтры
    filtered = orders
    if status_filter != "Все":
        filtered = [o for o in filtered if o.get("status") == status_filter]
    if sale_type_filter != "Все":
        filtered = [o for o in filtered if o.get("sale_type") == sale_type_filter]
    if search:
        filtered = [o for o in filtered if search.lower() in str(o.get("customer_name", "")).lower() 
                    or search.lower() in str(o.get("order_number", "")).lower()
                    or search.lower() in str(o.get("phone", "")).lower()]
    
    if not filtered:
        st.info("Заказов не найдено")
    else:
        df = pd.DataFrame(filtered)
        # Выбираем основные колонки
        display_cols = ["order_number", "date", "customer_name", "phone", "total_price", "status", "sale_type", "payment_method"]
        display_cols = [c for c in display_cols if c in df.columns]
        if display_cols:
            st.dataframe(df[display_cols], use_container_width=True, hide_index=True)
        else:
            st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Карточка заказа
        st.subheader("🔍 Провалиться в заказ")
        order_select = st.selectbox("Выберите номер заказа", [o["order_number"] for o in filtered], format_func=lambda x: f"{x} — {next((o['customer_name'] for o in filtered if o['order_number']==x), '')}")
        
        if order_select:
            order = next((o for o in filtered if o["order_number"] == order_select), None)
            if order:
                with st.expander(f"📄 Заказ {order['order_number']}", expanded=True):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Дата:** {order.get('date', '—')}")
                        st.write(f"**Клиент:** {order.get('customer_name', '—')}")
                        st.write(f"**Телефон:** {order.get('phone', '—')}")
                        st.write(f"**Адрес:** {order.get('address', '—')}")
                        st.write(f"**Тип продажи:** {order.get('sale_type', '—')}")
                    with col2:
                        st.write(f"**Способ продажи:** {order.get('sale_channel', '—')}")
                        st.write(f"**Оплата:** {order.get('payment_method', '—')}")
                        st.write(f"**Статус:** {order.get('status', '—')}")
                        # Кнопки смены статуса
                        new_status = st.selectbox("Изменить статус", ["В процессе", "В доставке", "Завершен"], 
                                                   index=["В процессе", "В доставке", "Завершен"].index(order.get("status", "В процессе")) if order.get("status") in ["В процессе", "В доставке", "Завершен"] else 0)
                        if st.button("🔄 Обновить статус"):
                            update_order_status(order["order_number"], new_status)
                            st.success("Статус обновлён!")
                            st.rerun()
                    
                    st.divider()
                    st.write("**💰 Себестоимость и цена:**")
                    
                    # Себестоимость (товары со склада)
                    if order.get("cost_items"):
                        st.write("**Товары со склада:**")
                        cost_df = pd.DataFrame(order["cost_items"])
                        st.dataframe(cost_df, use_container_width=True, hide_index=True)
                    
                    # Услуги
                    if order.get("services"):
                        st.write("**Услуги:**")
                        for i, svc in enumerate(order["services"]):
                            st.write(f"  {i+1}. {svc.get('name', '')} — {svc.get('price', 0)} ₽")
                    
                    st.write(f"**Доставка:** {order.get('delivery_cost', 0)} ₽")
                    st.write(f"**Откат:** {order.get('kickback', 0)} ₽")
                    st.write(f"**💰 Итого цена продажи:** {order.get('total_price', 0)} ₽")
                    
                    if order.get("comment"):
                        st.write(f"**💬 Комментарий:** {order['comment']}")

# ======================== СКЛАД ========================
elif menu == "📦 Склад":
    st.header("📦 Склад")
    
    stock = load_stock()
    
    # Фильтры
    col1, col2 = st.columns(2)
    with col1:
        only_in_stock = st.checkbox("Только в наличии")
    with col2:
        search_stock = st.text_input("🔍 Поиск по названию/артикулу", "")
    
    filtered_stock = stock
    if only_in_stock:
        filtered_stock = [s for s in filtered_stock if s.get("in_stock") == "Да"]
    if search_stock:
        filtered_stock = [s for s in filtered_stock if search_stock.lower() in str(s.get("name", "")).lower() 
                         or search_stock.lower() in str(s.get("stock_id", "")).lower()]
    
    if filtered_stock:
        df = pd.DataFrame(filtered_stock)
        display_cols = ["stock_id", "date_added", "name", "type", "quantity", "in_stock", "unit_cost", "supplier", "paid_supplier", "quality"]
        display_cols = [c for c in display_cols if c in df.columns]
        st.dataframe(df[display_cols] if display_cols else df, use_container_width=True, hide_index=True)
        
        # Карточка товара
        st.subheader("🔍 Провалиться в товар")
        item_select = st.selectbox("Выберите товар", [s["stock_id"] + " — " + s["name"] for s in filtered_stock])
        
        if item_select:
            item_id = item_select.split(" — ")[0]
            item = next((s for s in filtered_stock if s["stock_id"] == item_id), None)
            if item:
                with st.expander(f"📄 {item['name']}", expanded=True):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**ID:** {item.get('stock_id', '—')}")
                        st.write(f"**Дата добавления:** {item.get('date_added', '—')}")
                        st.write(f"**Тип товара:** {item.get('type', '—')}")
                        st.write(f"**В наличии:** {item.get('in_stock', '—')}")
                        st.write(f"**Качество:** {item.get('quality', '—')}")
                    with col2:
                        st.write(f"**Количество:** {item.get('quantity', 0)}")
                        st.write(f"**Себестоимость:** {item.get('unit_cost', '—')} ₽")
                        st.write(f"**Поставщик:** {item.get('supplier', '—')}")
                        st.write(f"**Рассчитались:** {item.get('paid_supplier', '—')}")
                        st.write(f"**Номер накладной:** {item.get('supplier_order', '—')}")
                    
                    if item.get("comment"):
                        st.write(f"**💬 Комментарий:** {item['comment']}")
                    
                    # Фото
                    if item.get("photo"):
                        st.image(item['photo'], width=300, caption=item['name'])
    else:
        st.info("Склад пуст. Добавьте товар через меню.")

# ======================== НОВЫЙ ЗАКАЗ ========================
elif menu == "➕ Новый заказ":
    st.header("➕ Новый заказ")
    
    stock = load_stock()
    
    with st.form("new_order_form"):
        # Основная информация
        col1, col2 = st.columns(2)
        with col1:
            order_date = st.date_input("📅 Дата заказа", date.today())
            auto_number = st.checkbox("Авто-номер", value=True)
            if auto_number:
                order_number = gen_order_number()
                st.text_input("Номер заказа", order_number, disabled=True)
            else:
                order_number = st.text_input("Номер заказа (вручную)", "")
        with col2:
            sale_type = st.selectbox("🏷️ Тип продажи", ["Услуга", "Ремонт", "Диагностика", "Товар", "Сборка ПК", "Иное"])
            if sale_type == "Иное":
                sale_type = st.text_input("Укажите свой вариант", "Иное")
        
        # Клиент
        st.subheader("👤 Клиент")
        col1, col2, col3 = st.columns(3)
        with col1:
            customer_name = st.text_input("Имя заказчика *")
        with col2:
            phone = st.text_input("📞 Телефон")
        with col3:
            address = st.text_input("📍 Адрес заказчика")
        
        col1, col2 = st.columns(2)
        with col1:
            sale_channel = st.selectbox("📢 Способ продажи", ["Сайт", "Магазин", "Авито", "Другое"])
        with col2:
            payment_method = st.selectbox("💳 Способ оплаты", ["Счёт", "Нал", "Карта", "Другое"])
        
        # Себестоимость
        st.subheader("💰 Себестоимость")
        
        # Товары со склада
        st.write("**Товары со склада:**")
        if stock:
            stock_names = [s["name"] + f" ({s.get('stock_id','')})" for s in stock]
            selected_items = st.multiselect("Выберите товары", stock_names)
            cost_items = []
            for sel in selected_items:
                item = next(s for s in stock if s["name"] + f" ({s.get('stock_id','')})" == sel)
                qty = st.number_input(f"Кол-во: {item['name']}", min_value=1, value=1, key=f"qty_{item['stock_id']}")
                cost_items.append({
                    "stock_id": item.get("stock_id"),
                    "name": item["name"],
                    "unit_cost": float(item.get("unit_cost", 0) or 0),
                    "qty": qty,
                    "total": float(item.get("unit_cost", 0) or 0) * qty
                })
        else:
            st.info("Склад пуст. Сначала добавьте товары.")
            cost_items = []
        
        # Услуги
        st.write("**Услуги (добавьте несколько):**")
        services = []
        num_services = st.number_input("Количество услуг", min_value=0, max_value=10, value=0, step=1)
        for i in range(int(num_services)):
            col1, col2 = st.columns(2)
            with col1:
                svc_name = st.text_input(f"Название услуги {i+1}", key=f"svc_name_{i}")
            with col2:
                svc_price = st.number_input(f"Цена услуги {i+1}", min_value=0.0, step=0.01, key=f"svc_price_{i}")
            if svc_name and svc_price:
                services.append({"name": svc_name, "price": svc_price})
        
        # Доставка
        delivery_cost = st.number_input("🚚 Стоимость доставки", min_value=0.0, step=0.01, value=0.0)
        
        # Откат
        kickback = st.number_input("🔄 Откат (учитывается в себестоимости)", min_value=0.0, step=0.01, value=0.0)
        
        # Итоговая цена
        st.divider()
        st.subheader("💵 Итоговая цена продажи")
        
        # Подсчёт себестоимости
        total_cost = sum(c["total"] for c in cost_items) + sum(s["price"] for s in services) + delivery_cost + kickback
        st.write(f"**Себестоимость (расчётная):** {total_cost:,.2f} ₽")
        
        total_price = st.number_input("Цена продажи (итоговая)", min_value=0.0, step=0.01, value=0.0)
        profit = total_price - total_cost
        st.write(f"**Прибыль:** {profit:,.2f} ₽")
        
        # Комментарий
        comment = st.text_area("💬 Комментарий к заказу")
        
        # Кнопка
        st.divider()
        submitted = st.form_submit_button("💾 Сохранить заказ", type="primary", use_container_width=True)
        
        if submitted:
            if not customer_name:
                st.error("⚠️ Введите имя заказчика")
            else:
                order_data = {
                    "order_number": order_number,
                    "date": str(order_date),
                    "sale_type": sale_type,
                    "customer_name": customer_name,
                    "phone": phone,
                    "address": address,
                    "sale_channel": sale_channel,
                    "payment_method": payment_method,
                    "cost_items": cost_items,
                    "services": services,
                    "delivery_cost": delivery_cost,
                    "kickback": kickback,
                    "total_cost": total_cost,
                    "total_price": total_price,
                    "profit": profit,
                    "status": "В процессе",
                    "comment": comment,
                    "created_at": datetime.now().isoformat()
                }
                save_order_to_db(order_data)
                st.success(f"✅ Заказ {order_number} создан!")
                st.balloons()

# ======================== НОВЫЙ ТОВАР ========================
elif menu == "➕ Новый товар":
    st.header("➕ Новый товар на склад")
    
    with st.form("new_stock_form"):
        col1, col2 = st.columns(2)
        with col1:
            date_added = st.date_input("📅 Дата (когда завели)", date.today())
            name = st.text_input("🏷️ Наименование товара *")
            item_type = st.selectbox("📂 Тип товара", ["Комплектующее", "Периферия", "Расходник", "Мебель", "Инструмент", "Другое"])
            if item_type == "Другое":
                item_type = st.text_input("Свой тип товара", "Другое")
        with col2:
            quantity = st.number_input("🔢 Количество", min_value=0, step=1, value=1)
            unit_cost = st.number_input("💰 Себестоимость за единицу", min_value=0.0, step=0.01)
            in_stock = st.selectbox("📦 В наличии сейчас?", ["Да", "Нет"])
        
        # Объединение одинаковых позиций
        merge_same = st.checkbox("Объединять с одинаковыми товарами (по названию)", value=True)
        
        # Поставщик
        st.subheader("🏭 Поставщик")
        col1, col2, col3 = st.columns(3)
        with col1:
            supplier = st.text_input("Поставщик")
        with col2:
            paid_supplier = st.selectbox("Рассчитались?", ["Нет", "Да", "Частично"])
        with col3:
            supplier_order = st.text_input("Номер заказа/накладной поставщика")
        
        # Качество
        quality = st.selectbox("🔧 Качество товара", ["Новый", "Б/У", "После ремонта"])
        
        # Фото
        photo = st.text_input("🖼️ Ссылка на фото (необязательно)")
        
        # Комментарий
        comment = st.text_area("💬 Комментарий")
        
        submitted = st.form_submit_button("💾 Сохранить товар", type="primary", use_container_width=True)
        
        if submitted:
            if not name:
                st.error("⚠️ Введите наименование товара")
            else:
                stock_data = {
                    "stock_id": gen_stock_id(),
                    "date_added": str(date_added),
                    "name": name,
                    "type": item_type,
                    "quantity": quantity,
                    "in_stock": in_stock,
                    "unit_cost": unit_cost,
                    "supplier": supplier,
                    "paid_supplier": paid_supplier,
                    "supplier_order": supplier_order,
                    "quality": quality,
                    "photo": photo,
                    "comment": comment,
                    "created_at": datetime.now().isoformat()
                }
                save_stock_to_db(stock_data)
                st.success(f"✅ Товар {stock_data['stock_id']} — {name} добавлен на склад!")
                st.balloons()
