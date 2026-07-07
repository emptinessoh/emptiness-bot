import discord
from discord import app_commands
from discord.ui import Button, View, Modal, TextInput, Select
import os
import asyncio

# ===== НАСТРОЙКИ =====
TOKEN = os.getenv('DISCORD_TOKEN')  # Токен из переменных окружения
ADMIN_ID = 250246659366191104  # ВАШ ID (уже вставлен!)

# ===== БАЗОВЫЙ КЛИЕНТ =====
class Client(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.synced = False

    async def on_ready(self):
        await self.wait_until_ready()
        if not self.synced:
            await tree.sync()
            self.synced = True
        print(f'✅ Бот {self.user} запущен!')

client = Client()
tree = app_commands.CommandTree(client)

# ===== МОДАЛЬНОЕ ОКНО (ФОРМА ЗАКАЗА) =====
class OrderModal(Modal, title='📝 Оформление заказа'):
    def __init__(self, service: str):
        super().__init__()
        self.service = service

    # Поле 1: Описание задачи
    task = TextInput(
        label='📌 Опишите задачу или вопрос',
        placeholder='Например: нужно смонтировать видео для YouTube...',
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=1000
    )

    # Поле 2: Срок
    deadline = TextInput(
        label='⏳ Желаемый срок',
        placeholder='1 день / до 3 дней / до 7 дней',
        required=True,
        max_length=50
    )

    # Поле 3: Бюджет
    budget = TextInput(
        label='💰 Предполагаемый бюджет',
        placeholder='Например: 5000 руб, 100$ или договорная',
        required=True,
        max_length=50
    )

    async def on_submit(self, interaction: discord.Interaction):
        # Формируем красивый отчет
        embed = discord.Embed(
            title='🆕 НОВЫЙ ЗАКАЗ!',
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow()
        )
        embed.add_field(name='👤 Клиент', value=f'{interaction.user.mention}\n`{interaction.user.id}`', inline=False)
        embed.add_field(name='📂 Услуга', value=f'**{self.service}**', inline=False)
        embed.add_field(name='📝 Описание', value=self.task.value, inline=False)
        embed.add_field(name='⏳ Срок', value=self.deadline.value, inline=False)
        embed.add_field(name='💰 Бюджет', value=self.budget.value, inline=False)

        # Отправляем клиенту подтверждение
        await interaction.response.send_message(
            f'✅ **Заказ принят!**\n\n'
            f'📂 Услуга: **{self.service}**\n'
            f'💰 Бюджет: {self.budget.value}\n'
            f'⏳ Срок: {self.deadline.value}\n\n'
            f'Скоро я свяжусь с вами в этом чате для обсуждения деталей!',
            ephemeral=True  # Видит только клиент
        )

        # Отправляем уведомление АДМИНУ (в ЛС)
        admin = await client.fetch_user(ADMIN_ID)
        if admin:
            await admin.send(embed=embed)

        # ДОПОЛНИТЕЛЬНО: можно отправить в канал на сервере
        # channel = client.get_channel(123456789)  # ID канала
        # if channel:
        #     await channel.send(embed=embed)

# ===== КОМАНДА ВЫБОРА УСЛУГИ (С КНОПКАМИ) =====
@tree.command(name='order', description='📝 Оформить заказ на услугу')
async def order(interaction: discord.Interaction):
    # Создаем кнопки-услуги (разбиты на 2 ряда для удобства)
    services = [
        ('🎬 Полноформатное видео', 'full'),
        ('📱 Вертикальный контент', 'vertical'),
        ('✨ Хайлайт', 'highlight'),
        ('🎨 Аниме эдит', 'anime'),
        ('👀 Превью', 'preview'),
        ('📺 Оформление канала', 'channel'),
        ('🖼️ Анимация статичной картинки', 'anim_static'),
        ('🎮 3D анимация', 'anim_3d'),
        ('💬 Другое', 'other')
    ]

    view = View()
    # Добавляем кнопки (максимум 5 в ряду, поэтому делаем 2 ряда)
    for label, value in services[:5]:  # Первый ряд
        view.add_item(Button(label=label, custom_id=f'service_{value}', style=discord.ButtonStyle.primary))
    for label, value in services[5:]:  # Второй ряд
        view.add_item(Button(label=label, custom_id=f'service_{value}', style=discord.ButtonStyle.secondary))

    await interaction.response.send_message(
        '🎯 **Выберите услугу, которая вам нужна:**\n'
        '*(после выбора откроется форма для заполнения)*',
        view=view
    )

# ===== ОБРАБОТЧИК НАЖАТИЙ НА КНОПКИ =====
@client.event
async def on_interaction(interaction: discord.Interaction):
    if interaction.type != discord.InteractionType.component:
        return

    custom_id = interaction.data.get('custom_id')
    if not custom_id or not custom_id.startswith('service_'):
        return

    # Расшифровываем название услуги
    service_map = {
        'service_full': '🎬 Полноформатное видео',
        'service_vertical': '📱 Вертикальный контент',
        'service_highlight': '✨ Хайлайт',
        'service_anime': '🎨 Аниме эдит',
        'service_preview': '👀 Превью',
        'service_channel': '📺 Оформление канала',
        'service_anim_static': '🖼️ Анимация статичной картинки',
        'service_anim_3d': '🎮 3D анимация',
        'service_other': '💬 Другое'
    }

    service_name = service_map.get(custom_id, 'Неизвестная услуга')

    # Открываем модальное окно с формой
    await interaction.response.send_modal(OrderModal(service=service_name))

# ===== ДОПОЛНИТЕЛЬНАЯ КОМАНДА ДЛЯ АДМИНА (ПРОВЕРКА) =====
@tree.command(name='ping', description='🏓 Проверить, жив ли бот')
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f'🏓 Pong! Задержка: {round(client.latency * 1000)} мс', ephemeral=True)

# ===== ЗАПУСК =====
if __name__ == '__main__':
    if TOKEN is None:
        raise Exception('❌ Ошибка: переменная DISCORD_TOKEN не найдена!')
    client.run(TOKEN)