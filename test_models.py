from models import Currency

data = {'rub': 10, 'eur': '3', 'usd': '1,5'}


async def test_currency():
    """Проверяем оба способа создания и что дескриптор обрабатывает строки и запятые"""

    user1 = Currency(rub=data['rub'], eur=data['eur'], usd=data['usd'])
    user2 = Currency().from_dict(data)
    assert user1 == user2
    assert user1.eur == 3
    assert user2.usd == 1.5


async def test_curr_updated():
    """
    Проверяем что работает установка валюты
    сложение со словарем и устанавливается флаг обновления
    """
    user = Currency().from_dict({'rub': 10})
    user += data
    assert user.rub == 20
    assert user.was_updated()
