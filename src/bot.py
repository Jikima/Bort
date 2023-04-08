import os
import openai
import discord
from random import randrange
from src.aclient import client
from discord import app_commands
from src import log, art, personas, responses

logger = log.setup_logger(__name__)

def run_discord_bot():
    @client.event
    async def on_ready():
        await client.send_start_prompt()
        await client.tree.sync()
        logger.info(f'{client.user} уже работает!')

    @client.tree.command(name="chat", description="Пообщайтесь с ChatGPT")
    async def chat(interaction: discord.Interaction, *, message: str):
        if client.is_replying_all == "True":
            await interaction.response.defer(ephemeral=False)
            await interaction.followup.send(
                "> **ПРЕДУПРЕЖДЕНИЕ: Вы уже находитесь в режиме replyAll. Если вы хотите использовать команду Slash, переключитесь в обычный режим, снова используя `/replyall`**")
            logger.warning("\x1b[31mВы уже в режиме replyAll, не можете использовать команду slash!\x1b[0m")
            return
        if interaction.user == client.user:
            return
        username = str(interaction.user)
        channel = str(interaction.channel)
        logger.info(
            f"\x1b[31m{username}\x1b[0m : /chat [{message}] in ({channel})")
        await client.send_message(interaction, message)


    @client.tree.command(name="private", description="Переключить частный доступ")
    async def private(interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)
        if not client.isPrivate:
            client.isPrivate = not client.isPrivate
            logger.warning("\x1b[31mПереключение в частный режим\x1b[0m")
            await interaction.followup.send(
                "> **ИНФОРМАЦИЯ: Далее ответ будет отправлен через приватный ответ. Если вы хотите переключиться обратно в публичный режим, используйте `/public`**")
        else:
            logger.info("Вы уже в приватном режиме!")
            await interaction.followup.send(
                "> **ПРЕДУПРЕЖДЕНИЕ: Вы уже находитесь в частном режиме. Если вы хотите перейти в публичный режим, используйте `/public`**")

    @client.tree.command(name="public", description="Переключить общественный доступ")
    async def public(interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)
        if client.isPrivate:
            client.isPrivate = not client.isPrivate
            await interaction.followup.send(
                "> **INFO: Далее ответ будет отправлен непосредственно на канал. Если вы хотите переключиться обратно в приватный режим, используйте `/private`**")
            logger.warning("\x1b[31mПереключитесь на публичный режим\x1b[0m")
        else:
            await interaction.followup.send(
                "> **ПРЕДУПРЕЖДЕНИЕ: Вы уже находитесь в публичном режиме. Если вы хотите перейти в приватный режим, используйте `/private`**")
            logger.info("Вы уже в публичном режиме!")


    @client.tree.command(name="replyall", description="Переключить replyAll режим")
    async def replyall(interaction: discord.Interaction):
        client.replying_all_discord_channel_id = str(interaction.channel_id)
        await interaction.response.defer(ephemeral=False)
        if client.is_replying_all == "True":
            client.is_replying_all = "False"
            await interaction.followup.send(
                "> **ИНФОРМАЦИЯ: Далее бот будет отвечать на команду Slash. Если вы хотите переключиться обратно в режим replyAll, используйте `/replyAll` снова**")
            logger.warning("\x1b[31mПереключение в нормальный режим\x1b[0m")
        elif client.is_replying_all == "False":
            client.is_replying_all = "True"
            await interaction.followup.send(
                "> **ИНФОРМАЦИЯ: Далее бот отключит Slash Command и будет отвечать на все сообщения только в этом канале. Если вы хотите переключиться в обычный режим, используйте `/replyAll` снова**")
            logger.warning("\x1b[31mПереключение в режим replyAll\x1b[0m")


    @client.tree.command(name="chat-model", description="Переключение различных моделей чата")
    @app_commands.choices(choices=[
        app_commands.Choice(name="Official GPT-3.5", value="ОФИЦИАЛЬНЫЙ"),
        app_commands.Choice(name="Ofiicial GPT-4.0", value="ОФИЦИАЛЬНЫЙ-GPT4"),
        app_commands.Choice(name="Website ChatGPT-3.5", value="НЕОФИЦИАЛЬНЫЙ"),
        app_commands.Choice(name="Website ChatGPT-4.0", value="НЕОФИЦИАЛЬНЫЙ-GPT4"),
        app_commands.Choice(name="Bard", value="Bard"),
    ])

    async def chat_model(interaction: discord.Interaction, choices: app_commands.Choice[str]):
        await interaction.response.defer(ephemeral=False)
        original_chat_model = client.chat_model
        original_openAI_gpt_engine = client.openAI_gpt_engine

        try:
            if choices.value == "OFFICIAL":
                client.openAI_gpt_engine = "gpt-3.5-turbo"
                client.chat_model = "OFFICIAL"
            elif choices.value == "OFFICIAL-GPT4":
                client.openAI_gpt_engine = "gpt-4"
                client.chat_model = "OFFICIAL"
            elif choices.value == "UNOFFICIAL":
                client.openAI_gpt_engine = "gpt-3.5-turbo"
                client.chat_model = "UNOFFICIAL"
            elif choices.value == "UNOFFICIAL-GPT4":
                client.openAI_gpt_engine = "gpt-4"
                client.chat_model = "UNOFFICIAL"
            elif choices.value == "Bard":
                client.chat_model = "Bard"
            else:
                raise ValueError("Invalid choice")

            client.chatbot = client.get_chatbot_model()
            await interaction.followup.send(f"> **ИНФОРМАЦИЯ: Вы сейчас находитесь в {client.chat_model} модель.**\n")
            logger.warning(f"\x1b[31mПереключиться на {client.chat_model} модель\x1b[0m")

        except Exception as e:
            client.chat_model = original_chat_model
            client.openAI_gpt_engine = original_openAI_gpt_engine
            client.chatbot = client.get_chatbot_model()
            await interaction.followup.send(f"> **ERROR: Ошибка при переключении на {choices.value} модель, проверьте, заполнили ли вы соответствующие поля в разделе `.env`.**\n")
            logger.exception(f"Error while switching to the {choices.value} model: {e}")


    @client.tree.command(name="reset", description="Полный сброс истории разговоров")
    async def reset(interaction: discord.Interaction):
        if client.chat_model == "OFFICIAL":
            client.chatbot = client.get_chatbot_model()
        elif client.chat_model == "UNOFFICIAL":
            client.chatbot.reset_chat()
            await client.send_start_prompt()
        elif client.chat_model == "Bard":
            client.chatbot = client.get_chatbot_model()
            await client.send_start_prompt()
        await interaction.response.defer(ephemeral=False)
        await interaction.followup.send("> **ИНФОРМАЦИЯ: Я все забыл.**")
        personas.current_persona = "standard"
        logger.warning(
            "\x1b[31mБот ChatGPT был успешно перезагружен\x1b[0m")

    @client.tree.command(name="help", description="Показать помощь для бота")
    async def help(interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)
        await interaction.followup.send(""":star: **ОСНОВНЫЕ КОМАНДЫ** \n
        - `/chat [message]` Общайтесь с ChatGPT!
        - `/draw [prompt]` Создайте изображение с помощью модели Dalle2
        - `/switchpersona [persona]` Переключение между опциональными персонами ChatGPT
                `random`: Выбирает случайную персону
                `chatgpt`: Стандартный режим ChatGPT
                `dan`: Dan Mode 11.0, позорный режим Do Anything Now Mode
                `sda`: Superior DAN имеет еще больше свободы в режиме DAN Mode
                `confidant`: Адвокат дьявола, злая личность.
                `based`: BasedGPT v2, сексуальный GPT
                `oppo`: OPPO говорит прямо противоположное тому, что сказал бы ChatGPT
                `dev`: Режим разработчика, включен режим разработчика v2

        - `/private` ChatGPT переключается в приватный режим
        - `/public` ChatGPT переключается в публичный режим
        - `/replyall` ChatGPT переключается между режимом replyAll и режимом по умолчанию
        - `/reset` Очистка истории разговоров ChatGPT
        - `/chat-model` Переключение различных моделей чата
                `OFFICIAL`: модель GPT-3.5
                `UNOFFICIAL`: Веб-сайт ChatGPT
                `Bard`: модель Google Bard
""")

        logger.info(
            "\x1b[31mКому-то нужна помощь!\x1b[0m")

    @client.tree.command(name="draw", description="Создание изображения с помощью модели Dalle2")
    async def draw(interaction: discord.Interaction, *, prompt: str):
        if interaction.user == client.user:
            return

        username = str(interaction.user)
        channel = str(interaction.channel)
        logger.info(
            f"\x1b[31m{username}\x1b[0m : /draw [{prompt}] in ({channel})")

        await interaction.response.defer(thinking=True, ephemeral=client.isPrivate)
        try:
            path = await art.draw(prompt)

            file = discord.File(path, filename="image.png")
            title = f'> **{prompt}** - <@{str(interaction.user.mention)}' + '> \n\n'
            embed = discord.Embed(title=title)
            embed.set_image(url="attachment://image.png")

            await interaction.followup.send(file=file, embed=embed)

        except openai.InvalidRequestError:
            await interaction.followup.send(
                "> **ОШИБКА: Неуместный запрос 😿**")
            logger.info(
            f"\x1b[31m{username}\x1b[0m обратился с неуместной просьбой.!")

        except Exception as e:
            await interaction.followup.send(
                "> **ОШИБКА: Что-то пошло не так 😿**")
            logger.exception(f"Ошибка при генерации изображения: {e}")


    @client.tree.command(name="switchpersona", description="Переключение между дополнительными персонами chatGPT")
    @app_commands.choices(persona=[
        app_commands.Choice(name="Random", value="random"),
        app_commands.Choice(name="Standard", value="standard"),
        app_commands.Choice(name="Do Anything Now 11.0", value="dan"),
        app_commands.Choice(name="Superior Do Anything", value="sda"),
        app_commands.Choice(name="Evil Confidant", value="confidant"),
        app_commands.Choice(name="BasedGPT v2", value="based"),
        app_commands.Choice(name="OPPO", value="oppo"),
        app_commands.Choice(name="Developer Mode v2", value="dev"),
        app_commands.Choice(name="DUDE V3", value="dude_v3"),
        app_commands.Choice(name="AIM", value="aim"),
        app_commands.Choice(name="UCAR", value="ucar"),
        app_commands.Choice(name="Jailbreak", value="jailbreak")
    ])
    async def switchpersona(interaction: discord.Interaction, persona: app_commands.Choice[str]):
        if interaction.user == client.user:
            return

        await interaction.response.defer(thinking=True)
        username = str(interaction.user)
        channel = str(interaction.channel)
        logger.info(
            f"\x1b[31m{username}\x1b[0m : '/switchpersona [{persona.value}]' ({channel})")

        persona = persona.value

        if persona == personas.current_persona:
            await interaction.followup.send(f"> **ПРЕДУПРЕЖДЕНИЕ: Уже установлено `{persona}` персона**")

        elif persona == "standard":
            if client.chat_model == "OFFICIAL":
                client.chatbot.reset()
            elif client.chat_model == "UNOFFICIAL":
                client.chatbot.reset_chat()
            elif client.chat_model == "Bard":
                client.chat_model = client.get_chatbot_model()

            personas.current_persona = "standard"
            await interaction.followup.send(
                f"> **ИНФОРМАЦИЯ: Переключился на `{persona}` персона**")

        elif persona == "random":
            choices = list(personas.PERSONAS.keys())
            choice = randrange(0, 6)
            chosen_persona = choices[choice]
            personas.current_persona = chosen_persona
            await responses.switch_persona(chosen_persona, client)
            await interaction.followup.send(
                f"> **ИНФОРМАЦИЯ: Переключился на `{chosen_persona}` персона**")


        elif persona in personas.PERSONAS:
            try:
                await responses.switch_persona(persona, client)
                personas.current_persona = persona
                await interaction.followup.send(
                f"> **INFO: Switched to `{persona}` persona**")
            except Exception as e:
                await interaction.followup.send(
                    "> **ERROR: Что-то пошло не так, пожалуйста, повторите попытку позже! 😿**")
                logger.exception(f"Ошибка при переключении персоны: {e}")

        else:
            await interaction.followup.send(
                f"> **ОШИБКА: Нет доступных персон: `{persona}` 😿**")
            logger.info(
                f'{username} запросил недоступную персону: `{persona}`')

    @client.event
    async def on_message(message):
        if client.is_replying_all == "True":
            if message.author == client.user:
                return
            if client.replying_all_discord_channel_id:
                if message.channel.id == int(client.replying_all_discord_channel_id):
                    username = str(message.author)
                    user_message = str(message.content)
                    channel = str(message.channel)
                    logger.info(f"\x1b[31m{username}\x1b[0m : '{user_message}' ({channel})")
                    await client.send_message(message, user_message)
            else:
                logger.exception("replying_all_discord_channel_id not found, please use the commnad `/replyall` again.")

    TOKEN = os.getenv("DISCORD_BOT_TOKEN")

    client.run(TOKEN)
