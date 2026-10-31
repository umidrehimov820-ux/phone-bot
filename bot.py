import telebot

# Вставьте ваш токен от BotFather
TOKEN = "9250292473:AAGr-pERBe5ZKRM9egN1OEgGIXFEb6yuGwc"
# Вставьте юзернейм вашего канала
CHANNEL_ID = "@my_phones_channel"

bot = telebot.TeleBot(TOKEN)
user_drafts = {}  # Здесь временно храним черновики объявлений


@bot.message_handler(commands=["start"])
def start(message):
  bot.send_message(
      message.chat.id,
      "Привет! Хотите выложить телефон? Нажмите команду /post",
  )


@bot.message_handler(commands=["post"])
def post(message):
  user_drafts[message.chat.id] = {"waiting": True}
  bot.send_message(
      message.chat.id,
      "Пожалуйста, отправьте фото и описание телефона (модель, состояние, цена,"
      " контакты) одним сообщением:",
  )


@bot.message_handler(content_types=["text", "photo"])
def handle_incoming_media(message):
  chat_id = message.chat.id

  if user_drafts.get(chat_id, {}).get("waiting"):
    phone_text = message.text or message.caption or "Без описания"
    username = message.from_user.username or "аноним"

    post_text = (
        f"📱 Новое объявление!\n\n{phone_text}\n\n👤 Отправитель: @{username}"
    )

    # Сохраняем черновик для этого пользователя
    user_drafts[chat_id] = {
        "waiting": False,
        "text": post_text,
        "photo": message.photo[-1].file_id if message.photo else None,
    }

    # Создаем инлайн-кнопки
    markup = telebot.types.InlineKeyboardMarkup()
    btn_publish = telebot.types.InlineKeyboardButton(
        "✅ Выставить", callback_data="publish"
    )
    btn_delete = telebot.types.InlineKeyboardButton(
        "❌ Удалить", callback_data="delete"
    )
    markup.add(btn_publish, btn_delete)

    # Показываем пользователю превью с кнопками
    if user_drafts[chat_id]["photo"]:
      bot.send_photo(
          chat_id,
          user_drafts[chat_id]["photo"],
          caption=(
              "Вот так будет выглядеть ваше объявление. Опубликовать его в"
              f" канале?\n\n{post_text}"
          ),
          parse_mode="Markdown",
          reply_markup=markup,
      )
    else:
      bot.send_message(
          chat_id,
          "Вот так будет выглядеть ваше объявление. Опубликовать его в"
          f" канале?\n\n{post_text}",
          parse_mode="Markdown",
          reply_markup=markup,
      )
  else:
    bot.send_message(chat_id, "Чтобы выложить телефон, отправьте команду /post")


# Обработка нажатий на кнопки
@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
  chat_id = call.message.chat.id
  draft = user_drafts.get(chat_id)

  if not draft or "text" not in draft:
    bot.answer_callback_query(call.id, "Срок действия черновика истек.")
    return

  if call.data == "publish":
    try:
      # Публикуем в канал
      if draft["photo"]:
        bot.send_photo(
            CHANNEL_ID,
            draft["photo"],
            caption=draft["text"],
            parse_mode="Markdown",
        )
      else:
        bot.send_message(CHANNEL_ID, draft["text"], parse_mode="Markdown")

      bot.answer_callback_query(call.id, "Успешно опубликовано!")
      bot.edit_message_caption(
          "✅ Объявление успешно опубликовано в канале!",
          chat_id=chat_id,
          message_id=call.message.message_id,
      )
    except Exception as e:
      print(e)
      bot.answer_callback_query(call.id, "Ошибка публикации в канал.")

    user_drafts[chat_id] = {}

  elif call.data == "delete":
    bot.answer_callback_query(call.id, "Объявление удалено.")
    try:
      bot.delete_message(chat_id, call.message.message_id)
    except Exception:
      pass
    bot.send_message(
        chat_id, "❌ Публикация отменена. Чтобы начать заново, отправьте /post"
    )
    user_drafts[chat_id] = {}


print("Бот запущен...")
bot.infinity_polling()
