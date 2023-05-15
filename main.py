import asyncio
import logging

import asyncclick as click
import httpx
from aiohttp import web

from models import AppField, Curr, Currency
from server_router import routes

logger = logging.getLogger(__name__)

RATE_URL = 'https://www.cbr-xml-daily.ru/daily_json.js'
MINUTE = 60


def get_logger(debug):
    if debug:
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s %(name)-16s %(levelname)-8s %(message)s',
            datefmt='%m-%d %H:%M',
        )
    else:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s %(name)-16s %(levelname)-8s %(message)s',
            datefmt='%H:%M',
        )
    return logging.getLogger(__name__)


async def get_rate(url) -> dict:
    """Получить обновления курсов валют

    Args:
        url (str): ссылка на страницу с курсами

    Returns:
        Словарь с валютами
    """
    logger.info('Check new rate ...')
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        valutes = resp.json()['Valute']
        return {
            Curr.RUB: 1,
            Curr.USD: valutes['USD']['Value'],
            Curr.EUR: valutes['EUR']['Value'],
        }


async def update_rate(*, curr_obj: Currency, period: int, url: str):
    """Обновления курсов с заданной частотой

    Args:
        curr_obj: объект хранящий валюту
        period: частота обновления в минутах
        url: ссылка на страницу с курсами
    """
    logger.info('Start check cbr ...')
    while True:
        await asyncio.sleep(period * MINUTE)
        curr_obj.from_dict(await get_rate(url=url))


async def check_update(**kwargs) -> None:
    """Проверить обновления объектов валют
    **kwargs: Словарь проверяемых объектов
    """
    logger.info('Start check updated ...')
    while True:
        await asyncio.sleep(MINUTE)
        for name, currency in kwargs.items():
            if currency.was_updated():
                logger.info(f'{name} updated: {currency}')


async def start_server(user_currency: Currency, cbr_currency: Currency):
    """Запуск API

    Args:
        user_currency: хранимая валюта
        cbr_currency: курс валют
    """
    logger.info('Start server ...')
    app = web.Application()
    app[AppField.DATA] = user_currency
    app[AppField.CBR] = cbr_currency

    app.add_routes(routes)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, 'localhost', 8080)
    await site.start()
    while True:
        await asyncio.sleep(MINUTE * MINUTE)


@click.command()
@click.option(
    '--period',
    '-p',
    type=int,
    default=5,
    show_default=True,
    help='Период обновления в минутах',
)
@click.option(
    '--rub', '-r', type=float, required=True, help='Начальный объем рублей'
)
@click.option(
    '--eur', '-e', type=float, required=True, help='Начальный объем евро'
)
@click.option(
    '--usd', '-u', type=float, required=True, help='Начальный объем долларов'
)
@click.option('--debug', default=False)
async def main(period, rub, eur, usd, debug):
    logger.info('Start app ...')
    get_logger(debug)

    cbr_currency = Currency().from_dict(await get_rate(url=RATE_URL))
    user_currency = Currency(rub=rub, eur=eur, usd=usd)

    tasks = [
        asyncio.create_task(
            update_rate(curr_obj=cbr_currency, period=period, url=RATE_URL)
        ),
        asyncio.create_task(
            check_update(user=user_currency, cbr=cbr_currency)
        ),
        asyncio.create_task(start_server(user_currency, cbr_currency)),
    ]
    try:
        await asyncio.wait(tasks)
    except asyncio.CancelledError:
        logger.info('Shutting down ...')


if __name__ == '__main__':
    asyncio.run(main())
