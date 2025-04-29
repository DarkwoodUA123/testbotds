import discord
import os
import requests
from dotenv import load_dotenv
from discord.ext import commands

# Загружаем переменные окружения из .env файла
load_dotenv()

# Получаем данные из .env файла
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')  # Теперь токен извлекается из переменной окружения
CHANNEL_ID = int(os.getenv('CHANNEL_ID'))  # Ваш ID канала
TWITCH_USERNAME = os.getenv('TWITCH_USERNAME')
TWITCH_CLIENT_ID = os.getenv('TWITCH_CLIENT_ID')
TWITCH_CLIENT_SECRET = os.getenv('TWITCH_CLIENT_SECRET')

# Настройки клиента для использования команд
intents = discord.Intents.default()
intents.message_content = True   # Чтобы читать текст сообщений
bot = commands.Bot(command_prefix="!", intents=intents)

# Переменная для хранения ID первого сообщения
message_id = None

# URL гифки для прикрепления к сообщению
GIF_URL = "https://media.giphy.com/media/your_gif_url_here.gif"  # Замените на свой URL

# Получение токена доступа для Twitch API
def get_twitch_access_token():
    url = "https://id.twitch.tv/oauth2/token"
    params = {
        "client_id": TWITCH_CLIENT_ID,
        "client_secret": TWITCH_CLIENT_SECRET,
        "grant_type": "client_credentials"
    }
    response = requests.post(url, params=params)
    if response.status_code == 200:
        return response.json()['access_token']
    else:
        print("Ошибка при получении токена:", response.status_code)
        return None

# Получение информации о стриме
def get_stream_info():
    access_token = get_twitch_access_token()
    if access_token is None:
        return None

    url = f"https://api.twitch.tv/helix/streams?user_login={TWITCH_USERNAME}"
    headers = {
        "Client-ID": TWITCH_CLIENT_ID,
        "Authorization": f"Bearer {access_token}"
    }
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        json_data = response.json()
        if json_data.get('data'):
            stream_data = json_data['data'][0]
            game_name = stream_data['game_name']
            viewer_count = stream_data['viewer_count']
            return game_name, viewer_count
        else:
            print("Нет активного стрима или ошибка данных:", json_data)
            return None
    else:
        print("Ошибка при получении данных о стриме:", response.status_code, response.text)
        return None

@bot.event
async def on_ready():
    print(f"Зашёл как {bot.user}")

# Обработка команды !test
@bot.command()
async def test(ctx):
    global message_id  # Добавили объявление переменной как глобальной

    print("Команда !test была вызвана")

    # Получаем информацию о стриме
    stream_info = get_stream_info()
    
    # Если нет данных о стриме, устанавливаем значения по умолчанию
    if stream_info is None:
        game_name = "Неизвестно"
        viewer_count = "Нет данных"
    else:
        game_name, viewer_count = stream_info

    # Создаем красивое сообщение с использованием Embed
    embed = discord.Embed(
        title=f"🎮 {TWITCH_USERNAME} в эфире! 🔴",
        description=f"Присоединяйтесь к стриму {TWITCH_USERNAME} на Twitch.",
        color=discord.Color.red()
    )

    # Добавляем поля с информацией
    embed.add_field(name="Ссылка на стрим:", value=f"[Перейти на Twitch](https://www.twitch.tv/{TWITCH_USERNAME})", inline=False)
    embed.add_field(name="Игра:", value=game_name, inline=True)
    embed.add_field(name="Зрители:", value=viewer_count, inline=True)

    # Устанавливаем миниатюру и подпись
    embed.set_thumbnail(url="https://static-cdn.jtvnw.net/jtv_user_pictures/twitch_profile_image.png")  # Логотип Twitch
    embed.set_footer(text="Created by stupa | Discord: stupapupa___", icon_url="https://cdn.discordapp.com/icons/your_icon.png")

    # Добавляем гифку
    embed.set_image(url=GIF_URL)  # Устанавливаем гифку

    # Если сообщение не отправлялось раньше, отправляем его
    channel = bot.get_channel(CHANNEL_ID)
    if message_id is None:
        msg = await channel.send(
            f"@everyone",  # Уведомление для всех участников сервера
            embed=embed
        )
        message_id = msg.id  # Сохраняем ID первого сообщения
    else:
        # Если сообщение уже было отправлено, обновляем его
        msg = await channel.fetch_message(message_id)
        await msg.edit(
            embed=embed
        )

# Этот блок кода будет выполнен, если бот запускается как основной файл
if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
