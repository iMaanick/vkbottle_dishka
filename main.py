import os

from dishka import make_async_container, AsyncContainer
from dotenv import load_dotenv
from vkbottle.bot import Bot

from handlers import example_labeler, setup_labelers
from providers import StrProvider, InteractorProvider
from vk_dishka import setup_dishka


async def startup_task() -> None:
    print("This is startup")


async def shutdown_task(container: AsyncContainer) -> None:
    print("This is shutdown")
    await container.close()


def main() -> None:
    load_dotenv()
    token = os.environ.get('TOKEN')
    bot = Bot(token=token)
    container = make_async_container(StrProvider(), InteractorProvider())
    setup_labelers(bot, [example_labeler])
    setup_dishka(container, bot)
    bot.loop_wrapper.on_startup.append(startup_task())
    bot.loop_wrapper.on_shutdown.append(shutdown_task(container))
    bot.run_forever()


if __name__ == '__main__':
    main()
