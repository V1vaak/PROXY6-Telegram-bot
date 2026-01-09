"""
Proxy6 API Client

Copyright (c) 2026 Alexsey Novikov

Распространяется под лицензией MIT.
Подробнее см. в файле LICENSE или на https://opensource.org/licenses/MIT.
"""


import requests
import aiohttp 


class Proxy6Error(Exception):
    """
    Исключение, возникающее при ошибках взаимодействия с API Proxy6.

    Используется для обозначения:
    - сетевых ошибок (таймауты, обрывы соединения);
    - ошибок HTTP-уровня;
    - ошибок, возвращаемых самим API Proxy6.
    """
    ...


class Proxy6:
    """
    Синхронный клиент для взаимодействия с API Proxy6.

    API документация: https://px6.me/ru/developers

    Parameters
    ----------
    api : str
        API-ключ для аутентификации в сервисе Proxy6.
    """

    BASE_URL = 'https://px6.link/api'

    def __init__(self, api: str) -> None:
        """
        Инициализация клиента.

        Parameters
        ----------
        api : str
            API-ключ для Proxy6.
        """
        self.api = api
        self.url = f'{self.BASE_URL}/{self.api}/'
        self.session: requests.Session = requests.Session()

    def _prepare_params(self, params: dict) -> dict:
        """
        Подготавливает параметры запроса:
        - удаляет None
        - кортежи преобразует в строку формата '1,2,3'
        - булевы значения переводит в '1' или None

        Parameters
        ----------
        params : dict[str, object]
            Сырые параметры запроса.

        Returns
        -------
        dict[str, object]
            Подготовленные параметры запроса.
        """
        prepared = {}
        for key, value in params.items():
            if value is None:
                continue
            if isinstance(value, tuple):
                prepared[key] = ','.join(map(str, value))
            elif isinstance(value, bool):
                prepared[key] = '1' if value else None
            else:
                prepared[key] = value
        return prepared

    def _make_request(self, method_name: str, **params: object) -> dict:
        """
        Выполняет GET-запрос к API Proxy6.

        Parameters
        ----------
        method_name : str
            Название метода API.
        **params
            Параметры запроса.

        Returns
        -------
        dict[str, object]
            Ответ API в формате JSON.

        Raises
        ------
        Proxy6Error
            При ошибке HTTP или если статус ответа != 'yes'.
        """
        url: str = f'{self.url}{method_name}'
        prepared_params = self._prepare_params(params)

        try:
            response = self.session.get(url, params=prepared_params, timeout=15)
            response.raise_for_status()
            data: dict[str, object] = response.json()
        except requests.RequestException as e:
            raise Proxy6Error(f'HTTP error: {e}') from e
        except ValueError:
            raise Proxy6Error('Invalid JSON response from API')

        if data.get('status') != 'yes':
            raise Proxy6Error(data.get('error', 'Unknown API error'))

        return data

    def get_price(self, *, count: int, period: int, version: int = 6) -> float | int:
        """
        Получает стоимость покупки прокси.

        Parameters
        ----------
        count : int
            Количество прокси.
        period : int
            Период в днях.
        version : int, optional
            Версия прокси: 4 - IPv4, 3 - IPv4 Shared, 6 - IPv6. По умолчанию 6.

        Returns
        -------
        float | int
            Стоимость в рублях.
        """
        data = self._make_request('getprice', count=count, period=period, version=version)
        return data['price']

    def get_count(self, *, country: str, version: int = 6) -> int:
        """
        Получает количество доступных прокси по стране.

        Parameters
        ----------
        country : str
            Код страны (ISO2).
        version : int, optional
            Версия прокси. По умолчанию 6.

        Returns
        -------
        int
            Количество доступных прокси.
        """
        data = self._make_request('getcount', country=country, version=version)
        return data['count']

    def get_country(self, *, version: int = 6) -> list[str]:
        """
        Получает список стран, в которых доступны прокси.

        Parameters
        ----------
        version : int, optional
            Версия прокси. По умолчанию 6.

        Returns
        -------
        list[str]
            Список кодов стран (ISO2).
        """
        data = self._make_request('getcountry', version=version)
        return data['list']

    def get_proxy(
        self,
        *,
        state: str = 'all',
        descr: str | None = None,
        page: int = 1,
        limit: int = 1000,
    ) -> dict:
        """
        Получает список прокси пользователя.

        Parameters
        ----------
        state : str, optional
            Статус прокси: 'active', 'expired', 'expiring' или 'all'. По умолчанию 'all'.
        descr : str | None, optional
            Фильтр по комментарию.
        page : int, optional
            Номер страницы. По умолчанию 1.
        limit : int, optional
            Количество прокси на страницу. По умолчанию 1000.

        Returns
        -------
        dict[str, object]
            Список прокси.
        """
        data = self._make_request(
            'getproxy',
            state=state,
            descr=descr,
            page=page,
            limit=limit,
        )
        return data['list']

    def set_type(self, *, ids: tuple[int, ...], type: str) -> bool:
        """
        Изменяет тип протокола прокси.

        Parameters
        ----------
        ids : tuple[int, ...]
            Внутренние ID прокси.
        type : str
            Устанавливаемый тип (протокол): http - HTTPS, либо socks - SOCKS5

        Returns
        -------
        bool
            True при успешной смене типа.
        """
        self._make_request('settype', ids=ids, type=type)
        return True

    def set_descr(
        self,
        *,
        new: str,
        old: str | None = None,
        ids: tuple[int, ...] | None = None,
    ) -> tuple[bool, int]:
        """
        Обновляет технический комментарий прокси.

        Parameters
        ----------
        new : str
            Новый комментарий.
        old : str | None, optional
            Старый комментарий.
        ids : tuple[int, ...] | None, optional
            ID прокси.

        Returns
        -------
        tuple[bool, int]
            Кортеж: (успех операции, количество обновленных прокси)
        
        Notes
        -----
        Обязательно должен присутствовать один из параметров: либо 'ids', либо 'old'.
        """
        data = self._make_request('setdescr', new=new, old=old, ids=ids)
        return True, data['count']

    def buy(
        self,
        *,
        count: int,
        period: int,
        country: str,
        version: int = 6,
        type: str = 'http',
        descr: str | None = None,
        auto_prolong: bool = False,
    ) -> dict:
        """
        Покупает прокси.

        Parameters
        ----------
        count : int
            Количество прокси.
        period : int
            Период в днях.
        country : str
            Код страны (ISO2).
        version : int, optional
            Версия прокси. По умолчанию 6.
        type : str, optional
            Тип протокола: 'http' или 'socks'. По умолчанию 'http'.
        descr : str | None, optional
            Комментарий для прокси.
        auto_prolong : bool, optional
            Автоматическое продление. По умолчанию False.

        Returns
        -------
        dict[str, object]
            Список купленных прокси.
        """
        data = self._make_request(
            'buy',
            count=count,
            period=period,
            country=country,
            version=version,
            type=type,
            descr=descr,
            auto_prolong=auto_prolong,
        )
        return data

    def prolong(self, *, period: int, ids: int | tuple[int, ...]) -> bool:
        """
        Продлевает прокси.

        Parameters
        ----------
        period : int
            Период продления в днях.
        ids : int | tuple[int, ...]
            ID прокси.

        Returns
        -------
        bool
            True при успешном продлении.
        """
        self._make_request('prolong', period=period, ids=ids)
        return True

    def delete(self, *, ids: int | None = None, descr: str | None = None) -> bool:
        """
        Удаляет прокси.

        Parameters
        ----------
        ids : int | None, optional
            ID прокси.
        descr : str | None, optional
            Комментарий для фильтрации.

        Returns
        -------
        bool
            True при успешном удалении.

        Notes
        -----
        Обязательно должен присутствовать один из параметров: либо 'ids', либо 'old'.
        """
        self._make_request('delete', ids=ids, descr=descr)
        return True

    def check(self, *, ids: int | None = None, proxy: str | None = None) -> bool:
        """
        Проверяет валидность прокси.

        Parameters
        ----------
        ids : int, optional
            Внутренний номер прокси в системе (обязательный если не указан proxy).
        proxy : str, optional
            Строка прокси в формате: ip:port:user:pass (обязательный если не указан ids).

        Returns
        -------
        bool
            True если прокси валиден.
        """
        data = self._make_request('check', ids=ids, proxy=proxy)
        return True if data['proxy_status'] == 'true' else False

    def close(self) -> None:
        """
        Закрывает HTTP-сессию.
        """
        self.session.close()

    def __str__(self) -> str:
        """
        Возвращает базовую информацию об аккаунте.

        Returns
        -------
        str
            Информация об аккаунте в формате JSON.
        """
        response = self.session.get(f'{self.BASE_URL}/{self.api}')
        response.raise_for_status()
        return str(response.json())


class AsyncProxy6:
    """
    Асинхронный класс для взаимодействия с API PROXY6. Сайт (https://px6.me/ru/)
    
    Parameters
    ----------
    api : str
        API-ключ для аутентификации в сервисе Proxy6.
    """
    
    def __init__(self, api: str):
        self.api = api
        self.url = f'https://px6.link/api/{self.api}/'
        self.session: aiohttp.ClientSession | None = None

    async def __aenter__(self):
        """
        Входит в асинхронный контекст и инициализирует HTTP-сессию.

        Создает aiohttp.ClientSession с настроенным таймаутом,
        чтобы предотвратить зависание запросов при проблемах с сетью
        или медленном ответе API.

        Returns
        -------
        AsyncProxy6
            Экземпляр клиента Proxy6 с активной HTTP-сессией.
        """
        timeout = aiohttp.ClientTimeout(
                                        total=30,
                                        connect=10,
                                        sock_read=30
                                        )
        self.session = aiohttp.ClientSession(timeout=timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Завершает асинхронный контекст и корректно закрывает HTTP-сессию.

        Гарантирует освобождение сетевых ресурсов независимо от того,
        завершился ли блок `async with` успешно или с исключением.
        """
        if self.session:
            await self.session.close()
            self.session = None


    async def __get_session(self) -> aiohttp.ClientSession:
        """
        Возвращает активную HTTP-сессию клиента.

        Raises
        ------
        RuntimeError
            Если сессия не была инициализирована и клиент используется
            вне асинхронного контекстного менеджера.
        """
        if not self.session:
            raise RuntimeError("ClientSession not initialized. Use 'async with AsyncProxy6(...)'")
        return self.session

    async def __make_request(self, method_name: str, **params) -> dict:
        """
        Выполняет асинхронный HTTP-запрос к API Proxy6.

        Формирует GET-запрос к указанному методу API, подготавливает параметры
        и обрабатывает сетевые ошибки.

        Parameters
        ----------
        method_name : str
            Название метода API Proxy6.
        **params : dict
            Параметры запроса, передаваемые в API.

        Returns
        -------
        dict
            Ответ API в формате JSON.

        Raises
        ------
        Proxy6Error
            При сетевых ошибках, таймаутах или HTTP-ошибках.
        RuntimeError
            Если HTTP-сессия не была инициализирована.
        """
        session = await self.__get_session()
        url = f'{self.url}{method_name}'

        prepared_params = {}
        for key, value in params.items():
            if value is not None:
                if isinstance(value, tuple):
                    value = ','.join(map(str, value))
                prepared_params[key] = value

        try:
            async with session.get(url, params=prepared_params) as response:
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientError as e:
            raise Proxy6Error(f'HTTP error while calling {method_name}: {e}')


    def __check_status(self, data: dict) -> None:
        """
        Проверяет успешность ответа API Proxy6.

        Анализирует поле `status` в ответе API и выбрасывает исключение
        в случае ошибки.

        Parameters
        ----------
        data : dict
            Ответ API Proxy6.

        Raises
        ------
        Proxy6Error
            Если API вернул статус, отличный от успешного.
        """
        if data.get('status') != 'yes':
            raise Proxy6Error(f'API error: {data}')

    
    async def get_price(self, *, count: int, period: int, version: int = 6) -> int | float:
        """
        Возвращает стоимость покупки прокси.

        Parameters
        ----------
        count : int
            Количество приобретаемых прокси.
        period : int
            Период аренды в днях.
        version : int, optional
            Версия прокси (по умолчанию IPv6).

        Returns
        -------
        int | float
            Стоимость прокси в рублях.

        Raises
        ------
        Proxy6Error
            При ошибке API или сетевой ошибке.
        """
        data = await self.__make_request('getprice', count=count, period=period, version=version)
        self.__check_status(data)
        return data['price']

    async def get_count(self, *, country: str, version: int = 6) -> int:
        """
        Получает количество доступных прокси для определенной страны.

        Parameters
        ----------
        country : str
            Код страны в формате ISO2 (обязательный параметр).
        version : int, optional
            Версия прокси: <b>4</b> - IPv4, <b>3</b> - IPv4 Shared, <b>6</b> - IPv6 (по умолчанию 6).

        Returns
        -------
        int  
            Количество доступных прокси.
        """
        data = await self.__make_request('getcount', country=country, version=version)

        self.__check_status(data)
        return data['count']
    
    async def get_country(self, *, version: int = 6) -> list[str]:
        """
        Возвращает список стран, в которых доступны прокси указанной версии.

        Parameters
        ----------
        version : int, optional
            Версия прокси:
            - 4 — IPv4
            - 3 — IPv4 Shared
            - 6 — IPv6 (по умолчанию)

        Returns
        -------
        list[str]
            Список кодов стран в формате ISO 3166-1 alpha-2.

        Raises
        ------
        Proxy6Error
            При ошибке API или сетевой ошибке.
        """
        data = await self.__make_request('getcountry', version=version)
        self.__check_status(data)
        return data['list']

    async def get_proxy(self, *, state: str = 'all', descr: str = None, 
                       page: int = 1, limit: int = 1000) -> dict:
        """
        Получает информацию о прокси объекта класса AsyncProxy6.

        Parameters
        ----------
        state : str, optional
            Состояние прокси: 'active' - активные, 'expired' - неактивные, 
            'expiring' - заканчивающиеся, 'all' - все (по умолчанию 'all').
        descr : str, optional
            Технический комментарий, указанный при покупке прокси.
        page : int, optional
            Номер страницы для пагинации (по умолчанию 1).
        limit : int, optional
            Количество прокси для вывода (по умолчанию 1000, максимальное).

        Returns
        -------
        dict
            Информация о прокси.
        """
        data = await self.__make_request('getproxy', state=state, descr=descr, 
                                        page=page, limit=limit)

        self.__check_status(data)
        return data['list']
        
    async def set_type(self, *, ids: tuple, type: str) -> bool:
        """
        Изменяет тип (протокол) ваших прокси.

        Parameters
        ----------
        ids : tuple
            Внутренние номера прокси в системе, кортежем (обязательный параметр).
        type : str
            Устанавливаемый тип: 'http' - HTTPS, или 'socks' - SOCKS5 (обязательный параметр).

        Returns
        -------
        True, если успешно.
        """
        data = await self.__make_request('settype', ids=ids, type=type)

        self.__check_status(data)
        return True

    async def set_descr(self, *, new: str, old: str = None, ids: tuple = None) -> tuple:
        """
        Обновляет технический комментарий у ваших прокси.

        Parameters
        ----------
        new : str
            Новый технический комментарий, макс. 50 символов (обязательный параметр).
        old : str, optional
            Старый технический комментарий для изменения.
        ids : tuple, optional
            Внутренние номера прокси в системе.

        Returns
        -------
        tuple
            (True, count), если успешно. count - число обновленных прокси.

        Notes
        -----
        Обязательно должен присутствовать один из параметров: либо 'ids', либо 'old'.
        """
        data = await self.__make_request('setdescr', new=new, old=old, ids=ids)

        self.__check_status(data)
        return True, data['count']
                
    async def buy(self, *, count: int, period: int, country: str, version: int = 6, 
                  type: str = 'http', descr: str = None, auto_prolong: bool = False) -> dict:
        """
        Покупает прокси.

        Parameters
        ----------
        count : int
            Количество прокси для покупки (обязательный параметр).
        period : int
            Период в днях (обязательный параметр).
        country : str
            Код страны в формате ISO2 (обязательный параметр).
        version : int, optional
            Версия прокси: <b>4</b> - IPv4, <b>3</b> - IPv4 Shared, <b>6</b> - IPv6 (по умолчанию 6).
        type : str, optional
            Тип прокси: 'socks' или 'http' (по умолчанию 'http').
        descr : str, optional
            Технический комментарий для списка прокси, макс. 50 символов.
        auto_prolong : bool, optional
            Включить автопродление для купленных прокси.

        Returns
        -------
        dict
            Список купленных прокси.
        """
        auto_prolong = auto_prolong if auto_prolong else None
        
        data = await self.__make_request('buy', count=count, period=period, 
                                        country=country, version=version, 
                                        type=type, descr=descr, auto_prolong=auto_prolong)

        self.__check_status(data)
        return data
        
    async def prolong(self, *, period: int, ids: int | tuple) -> bool:
        """
        Продлевает текущие прокси.

        Parameters
        ----------
        period : int
            Период продления в днях (обязательный параметр).
        ids : int or tuple
            Внутренние номера прокси в системе (обязательный параметр).

        Returns
        -------
        True, если успешно.
        """
        data = await self.__make_request('prolong', period=period, ids=ids)
        
        self.__check_status(data)
        return True
        
    async def delete(self, *, ids: int = None, descr: str = None) -> bool:
        """
        Удаляет прокси.

        Parameters
        ----------
        ids : int, optional
            Внутренние номера прокси в системе.
        descr : str, optional
            Технический комментарий, указанный при покупке прокси.

        Returns
        -------
        True, если успешно.

        Notes
        -----
        Обязательно должен присутствовать один из параметров: либо 'ids', либо 'descr'.
        """
        data = await self.__make_request('delete', ids=ids, descr=descr)

        self.__check_status(data)
        return True
        
    async def check(self, *, ids: int = None, proxy: str = None) -> bool:
        """
        Проверяет валидность прокси.

        Parameters
        ----------
        ids : int, optional
            Внутренний номер прокси в системе (обязательный если не указан proxy).
        proxy : str, optional
            Строка прокси в формате: ip:port:user:pass (обязательный если не указан ids).

        Returns
        -------
        bool
            True если прокси валиден, False в противном случае.
        """
        data = await self.__make_request('check', ids=ids, proxy=proxy)

        self.__check_status(data)
        return data['proxy_status']

    async def info(self) -> dict:
        """
        Возвращает базовую информацию об аккаунте Proxy6.

        Returns
        -------
        dict
            Информация об аккаунте и текущем статусе API.

        Raises
        ------
        Proxy6Error
            При сетевой ошибке или ошибке API.
        """
        session = await self.__get_session()
        async with session.get(f'https://px6.link/api/{self.api}') as response:
            response.raise_for_status()
            return await response.json()

    async def close(self):
        """Закрывает сессию вручную."""
        if self.session:
            await self.session.close()
            self.session = None