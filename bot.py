import discord
import os
from discord.ext import commands
from discord.ui import Modal, TextInput, View
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

# Получаем данные из .env файла
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_ID = int(os.getenv('CHANNEL_ID'))

# Настройки клиента для использования команд
intents = discord.Intents.default()
intents.message_content = True   # Чтобы читать текст сообщений
bot = commands.Bot(command_prefix="!", intents=intents)

# Переменная для хранения ID первого сообщения
message_id = None

# Словарь для хранения информации о стримерах для каждого сервера (guild)
server_stream_settings = {}

# Создание модального окна
class StreamerSettingsModal(Modal):
    def __init__(self):
        super().__init__(title="Настройка стримера")

        # Поле для ввода имени стримера
        self.streamer_input = TextInput(label="Введите имя стримера (например: twitch_username)", placeholder="Твич логин стримера", required=True)
        self.add_item(self.streamer_input)

    async def on_submit(self, interaction: discord.Interaction):
        # Сохраняем имя стримера в словарь для текущего сервера
        server_id = str(interaction.guild.id)
        server_stream_settings[server_id] = self.streamer_input.value
        await interaction.response.send_message(f"Стример {self.streamer_input.value} настроен для отслеживания на этом сервере.", ephemeral=True)

    async def on_error(self, interaction: discord.Interaction, error: Exception):
        await interaction.response.send_message(f"Произошла ошибка: {error}", ephemeral=True)

# Обработка команды /settings с вызовом модального окна
@bot.command()
async def settings(ctx):
    modal = StreamerSettingsModal()
    await ctx.send_modal(modal)

# Команда теста для проверки настроек
@bot.command()
async def test(ctx):
    server_id = str(ctx.guild.id)
    if server_id in server_stream_settings:
        streamer = server_stream_settings[server_id]
        await ctx.send(f"На этом сервере настроен стример: {streamer}")
    else:
        await ctx.send("Стример не настроен. Используйте команду /settings, чтобы настроить стримера.")

# Этот блок кода будет выполнен, если бот запускается как основной файл
if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
