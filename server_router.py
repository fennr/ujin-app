import logging

from aiohttp import web
from aiohttp.web_request import Request
from aiohttp.web_response import Response

from models import AppField, Currency

logger = logging.getLogger(__name__)
routes = web.RouteTableDef()


@routes.get('/rub/get')
async def get_rub(request: Request) -> Response:
    text = f'rub: {str(request.app[AppField.DATA].rub)}'
    logger.debug(text)
    return Response(text=text)  # text = text/plain


@routes.get('/eur/get')
async def get_eur(request: Request) -> Response:
    text = f'eur: {str(request.app[AppField.DATA].eur)}'
    logger.debug(text)
    return Response(text=text)


@routes.get('/usd/get')
async def get_usd(request: Request) -> Response:
    text = f'usd: {str(request.app[AppField.DATA].usd)}'
    logger.debug(text)
    return Response(text=text)


@routes.get('/amount/get')
async def get_amount(request: Request) -> Response:
    data: Currency = request.app[AppField.DATA]
    cbr: Currency = request.app[AppField.CBR]
    sum_rub = data.rub + round(data.eur * cbr.eur) + round(data.usd * cbr.usd)
    text = (
        f'rub: {data.rub}\neur: {data.eur}\nusd: {data.usd}\n'
        f'sum: {sum_rub} rub / '
        f'{round(sum_rub / cbr.eur, 4)} eur / '
        f'{round(sum_rub / cbr.usd, 4)} usd'
    )
    logger.debug(text)
    return Response(text=text)


@routes.post('/amount/set')
async def set_amount(request: Request) -> Response:
    req = await request.json()
    request.app[AppField.DATA].from_dict(req)
    logger.debug(f'POST /amount/set {req}')
    logger.debug(f'response: {request.app[AppField.DATA]}')
    return web.json_response({'message': 'ok'})


@routes.post('/modify')
async def modify_data(request: Request) -> Response:
    req = await request.json()
    request.app[AppField.DATA] += req
    logger.debug(f'POST /modify {req}')
    logger.debug(f'response: {request.app[AppField.DATA]}')
    return web.json_response({'message': 'ok'})
