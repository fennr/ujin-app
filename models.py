import abc
import logging
from collections.abc import Mapping
from enum import Enum

logger = logging.getLogger(__name__)


class AppField(str, Enum):
    DATA = 'data'
    PERIOD = 'period'
    CBR = 'cbr'


class Curr(str, Enum):
    RUB = 'rub'
    EUR = 'eur'
    USD = 'usd'


class CurrencyField(abc.ABC):
    """Дескриптор для валидации валют"""

    def __set_name__(self, owner, name):
        self.name = name

    def __set__(self, instance, value):
        try:
            new_value = self.validate(self.name, value)
            instance.__dict__[self.name] = new_value
        except ValueError:
            logger.error(f'{self.name} must be > 0.')

    def validate(self, name: str, value: float | str) -> float:
        if isinstance(value, str):
            value = float(value.replace(',', '.'))
        value = round(value, 2)
        if value < 0:
            raise ValueError
        return value


class BaseCurrency(abc.ABC):
    rub = CurrencyField()
    eur = CurrencyField()
    usd = CurrencyField()

    def __repr__(self):
        return f'Currency(rub={self.rub}, usd={self.usd}, eur={self.eur})'

    @abc.abstractmethod
    def from_dict(self, json_data):
        """Загрузить из словаря"""

    @abc.abstractmethod
    def was_updated(self):
        """Проверить обновления объекта"""


class Currency(BaseCurrency):
    def __repr__(self):
        return f'Currency(rub={self.rub}, usd={self.usd}, eur={self.eur})'

    def __iter__(self):
        return (i for i in (self.rub, self.eur, self.usd))

    def __init__(self, rub=0, eur=0, usd=0):
        self.rub = rub
        self.eur = eur
        self.usd = usd
        self.__updated = False

    @property
    def updated(self):
        return self.__updated

    def __eq__(self, other):
        return (
            self.rub == other.rub
            and self.usd == other.usd
            and self.eur == other.eur
        )

    def __hash__(self):
        return hash(self.rub + self.usd + self.eur)

    def __add__(self, other: Mapping):
        old_hach = hash(self)
        if isinstance(other, Currency):
            self.rub = self.rub + other.rub
            self.eur = self.eur + other.eur
            self.usd = self.usd + other.usd
        else:
            try:
                self.rub += float(other.get(Curr.RUB, 0))
                self.eur += float(other.get(Curr.EUR, 0))
                self.usd += float(other.get(Curr.USD, 0))
            except TypeError:
                logger.error('Required object Currency')
        self.__updated = hash(self) != old_hach
        return self

    def from_dict(self, json_data: Mapping):
        old_hach = hash(self)
        self.rub = json_data.get(Curr.RUB, self.rub)
        self.eur = json_data.get(Curr.EUR, self.eur)
        self.usd = json_data.get(Curr.USD, self.usd)
        self.__updated = hash(self) != old_hach
        return self

    def was_updated(self):
        if self.__updated:
            self.__updated = False
            return True
        return False
