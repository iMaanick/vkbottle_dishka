from dishka import FromDishka
from vkbottle import Bot
from vkbottle.bot import Message
from vkbottle.framework.labeler import BotLabeler

from interactors import ReqInteractor, AppInteractor
from src.vkbottle_dishka.vk_dishka import inject

example_labeler = BotLabeler()


@example_labeler.message(text="привет")
async def hi_handler(
        message: Message,
) -> None:
    await message.answer(f"Привет!")


@example_labeler.message(text="req")
@inject
async def req_handler(
        message: Message,
        interactor: FromDishka[ReqInteractor],
) -> None:
    text = await interactor()
    await message.answer(text)


@example_labeler.message(text="app")
@inject
async def app_handler(
        message: Message,
        interactor: FromDishka[AppInteractor],
) -> None:
    text = await interactor()
    await message.answer(text)


def setup_labelers(bot: Bot, labelers: list[BotLabeler]) -> None:
    for labeler in labelers:
        bot.labeler.load(labeler)
