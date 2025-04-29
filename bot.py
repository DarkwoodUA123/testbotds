import discord
import os
import requests
import asyncio
import json
from discord.ext import commands, tasks
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
TWITCH_CLIENT_ID = os.getenv("TWITCH_CLIENT_ID")
TWITCH_CLIENT_SECRET = os.getenv("TWITCH_CLIENT_SECRET")

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# Где храним: { "streamer_name": channel_id }
SETTINGS_FILE = "streamers.json"
GIF_URL = "https://media.giphy.com/media/your_gif_url_here.gif"

# Храним статус каждого стримера, чтобы не спамить
streamer_status = {}

# ---------- Настройки ----------
def load_streamers():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_streamers(data):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(data, f, indent=2)

# ---------- Twitch ----------
def get_twitch_token():
    url = "https://id.twitch.tv/oauth2/token"
    params = {
        "client_id": TWITCH_CLIENT_ID,
        "client_secret": TWITCH_CLIENT_SECRET,
        "grant_type": "client_credentials"
    }
    response = requests.post(url, params=params)
    return response.json().get("access_token")

def get_stream_info(username, token):
    url = f"https://api.twitch.tv/helix/streams?user_login={username}"
    headers = {
        "Client-ID": TWITCH_CLIENT_ID,
        "Authorization": f"Bearer {token}"
    }
    resp = requests.get(url, headers=headers)
    data = resp.json()
    if resp.status_code == 200 and data.get("data"):
        return data["data"][0]
    return None

# ---------- Команды ----------
@bot.tree.command(name="settings", description="Связать стримера с этим каналом")
async def settings(interaction: discord.Interaction, streamer: str):
    streamer = streamer.lower()
    data = load_streamers()
    data[streamer] = interaction.channel_id
    save_streamers(data)
    await interaction.response.send_message(f"✅ Стример **{streamer}** теперь отслеживается в этом канале!", ephemeral=True)

# ---------- Проверка стримов ----------
@tasks.loop(seconds=60)
async def check_streams():
    streamers = load_streamers()
    token = get_twitch_token()
    if not token:
        print("Не удалось получить токен Twitch")
        return

    for streamer, channel_id in streamers.items():
        info = get_stream_info(streamer, token)
        was_live = streamer_status.get(streamer, False)
        is_live = info is not None

        if is_live and not was_live:
            # Стрим начался
            streamer_status[streamer] = True

            title = info.get("title", "Без названия")
            game = info.get("game_name", "Неизвестно")
            viewers = info.get("viewer_count", 0)

            embed = discord.Embed(
                title=f"🔴 {streamer} начал стрим!",
                description=title,
                color=discord.Color.red()
            )
            embed.add_field(name="Игра", value=game, inline=True)
            embed.add_field(name="Зрители", value=viewer_count, inline=True)
            embed.add_field(name="Ссылка", value=f"[Смотреть стрим](https://twitch.tv/{streamer})", inline=False)
            embed.set_image(url=GIF_URL)
            embed.set_footer(text="Оповещение о стриме")

            channel = bot.get_channel(channel_id)
            if channel:
                await channel.send("@everyone", embed=embed)

        elif not is_live:
            streamer_status[streamer] = False

@bot.event
async def on_ready():
    await bot.wait_until_ready()
    try:
        synced = await bot.tree.sync()
        print(f"Синхронизировано {len(synced)} команд")
    except Exception as e:
        print(f"Ошибка sync: {e}")
    check_streams.start()
    print(f"Бот запущен как {bot.user}")

# ---------- Запуск ----------
if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
