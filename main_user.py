from telethon import TelegramClient, events
import sqlite3

# API identifikatorlari
api_id = 29589563
api_hash = "15cfa140e1c6599459427686bdae638f"

# Klientni yaratish
client = TelegramClient("userbot_session", api_id, api_hash)

# Ma'lumotlar bazasiga ulanish funksiyasi
def connect_db():
    return sqlite3.connect('keywords.db', timeout=30)



# Bazadan kalit so'zlarni olish funksiyasi
def get_keywords_from_db():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('SELECT word FROM keywords')
    keywords = [row[0] for row in cursor.fetchall()]
    conn.close()
    return keywords

# Bazadan target guruh ID'sini olish funksiyasi
def get_target_group_id():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('SELECT group_id FROM target_group LIMIT 1')
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

# Target guruh ID'sini o'zgartirish funksiyasi
def set_target_group_id(group_id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM target_group')
    cursor.execute('INSERT INTO target_group (group_id) VALUES (?)', (group_id,))
    conn.commit()
    conn.close()
    return f"Target guruh ID muvaffaqiyatli o'zgartirildi: {group_id}"

# So'z qo'shish funksiyasi
def add_keyword(word):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO keywords (word) VALUES (?)', (word,))
    conn.commit()
    conn.close()
    return f"'{word}' so'zi muvaffaqiyatli qo'shildi."

# So'z o'chirish funksiyasi
def delete_keyword(word):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM keywords WHERE word = ?', (word,))
    conn.commit()
    conn.close()
    if cursor.rowcount > 0:
        return f"'{word}' so'zi muvaffaqiyatli o'chirildi."
    else:
        return f"'{word}' so'zi topilmadi."

# Bazadagi so'zlar ro'yxatini ko'rish funksiyasi
def list_keywords():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('SELECT word FROM keywords')
    keywords = cursor.fetchall()
    conn.close()
    if keywords:
        return "Hozirgi so'zlar ro'yxati:\n" + "\n".join([kw[0] for kw in keywords])
    else:
        return "Hozircha birorta ham so'z yo'q."

# Xabarlar qayta yuborilishining oldini olish uchun tekshirish
sent_messages = set()


@client.on(events.NewMessage(incoming=True, func=lambda e: e.is_group))
async def handle_new_message(event):
    keywords = get_keywords_from_db()
    target_group_id = get_target_group_id()

    if target_group_id:
        # Matn uzunligini tekshirish
        if len(event.raw_text) <= 80:
            if any(keyword in event.raw_text for keyword in keywords):
                if event.id not in sent_messages:
                    sent_messages.add(event.id)
                    try:
                        sender = await event.get_sender()

                        # Username ni optimallashtirish
                        if sender.username:
                            username = f"@{sender.username}"
                        else:
                            username = f"[None](tg://openmessage?user_id={sender.id})"

                        # Profil nomi va username bilan birga xabar matni
                        profile_name = sender.first_name if sender.first_name else "Ismi yo'q"
                        text = (f"💬 Xabar matni: {event.raw_text}\n"
                                f"#️⃣ Username: {username}\n"
                                f"👤 Profil: [{profile_name}](tg://user?id={sender.id})")

                        # Xabarni yuborish
                        await client.send_message(target_group_id, text)
                        print(f"Xabar yuborildi: {event.raw_text}")
                    except Exception as e:
                        print(f"Xabar yuborishda xatolik: {e}")
        else:
            print("Xabar uzunligi 80 belgidan oshdi va e'tiborsiz qoldirildi.")




# Target guruh ID'sini o'zgartirish buyruq handleri
@client.on(events.NewMessage(pattern=r'^/setgroup'))
async def handle_setgroup(event):
    try:
        group_id = int(event.message.message.split(" ", 1)[1])
        response = set_target_group_id(group_id)
    except (IndexError, ValueError):
        response = "Iltimos, to'g'ri guruh ID'sini kiriting."
    await event.respond(response)

# So'z qo'shish buyruq handleri
@client.on(events.NewMessage(pattern=r'^/addword'))
async def handle_addword(event):
    try:
        word = event.message.message.split(" ", 1)[1]
        response = add_keyword(word)
    except IndexError:
        response = "Iltimos, qo'shmoqchi bo'lgan so'zni kiriting."
    await event.respond(response)

# So'z o'chirish buyruq handleri
@client.on(events.NewMessage(pattern=r'^/delword'))
async def handle_delword(event):
    try:
        word = event.message.message.split(" ", 1)[1]
        response = delete_keyword(word)
    except IndexError:
        response = "Iltimos, o'chirmoqchi bo'lgan so'zni kiriting."
    await event.respond(response)

# So'zlar ro'yxatini ko'rish buyruq handleri
@client.on(events.NewMessage(pattern=r'^/listwords'))
async def handle_listwords(event):
    response = list_keywords()
    await event.respond(response)

# Botni ishga tushirish
client.start()
client.run_until_disconnected()
