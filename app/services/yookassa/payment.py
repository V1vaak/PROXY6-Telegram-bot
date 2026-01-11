from yookassa import Payment, Configuration
import uuid

from config import YOOKASSA_SHOP_ID, YOOKASSA_API_KEY


Configuration.account_id = YOOKASSA_SHOP_ID
Configuration.secret_key = YOOKASSA_API_KEY


def create_payment(amount: str) -> tuple[str, str]:
    """
    Создаёт платёж в системе ЮKassa и возвращает данные для перенаправления пользователя.

    Формирует платёж с автоматическим списанием средств (``capture=True``)
    и редирект-подтверждением. Используется для инициализации оплаты
    в Telegram-боте.

    Parameters
    ----------
    amount : str
        Сумма платежа в рублях в строковом формате
        (например: ``"199.00"``).

    Returns
    -------
    tuple[str, str]
        Кортеж из:
        - URL для перехода пользователя на страницу оплаты;
        - идентификатора платежа в системе ЮKassa.
    """
    idempotence_key = str(uuid.uuid4())

    payment = Payment.create(
        {
            "amount": {
                "value": amount,
                "currency": "RUB"
            },
            "capture": True,
            "payment_method_data": {
                "type": "bank_card"
            },
            "confirmation": {
                "type": "redirect",
                "return_url": "https://t.me/Proxy6TestBot"
            },
            "description": "Покупка прокси"
        },
        idempotence_key
    )

    return payment.confirmation.confirmation_url, payment.id


def get_status(payment_id: str) -> str:
    """
    Получает текущий статус платежа в системе ЮKassa.

    Используется для проверки состояния оплаты
    (например: ``pending``, ``waiting_for_capture``, ``succeeded``, ``canceled``).

    Parameters
    ----------
    payment_id : str
        Уникальный идентификатор платежа в ЮKassa.

    Returns
    -------
    str
        Статус платежа.
    """
    res = Payment.find_one(payment_id)
    return res.status



# ============================ не требуется для проекта ===========================================

def cancel_payment(payment_id: str) -> None:
    """
    Отменяет платёж в системе ЮKassa.

    Используется для отмены платежа, который ещё не был завершён
    или подтверждён.

    Parameters
    ----------
    payment_id : str
        Уникальный идентификатор платежа в ЮKassa.

    Returns
    -------
    None
        Функция не возвращает значение.
    """
    Payment.cancel(payment_id)



def payment_confirmation(payment_id: str, value: str) -> dict:
    """
    Подтверждает платёж в системе ЮKassa (capture).

    Используется для перевода платежа из статуса
    ``waiting_for_capture`` в ``succeeded``.
    В текущем проекте не применяется.

    Parameters
    ----------
    payment_id : str
        Уникальный идентификатор платежа в ЮKassa.
    value : str
        Сумма подтверждаемого платежа в рублях
        (например: ``"199.00"``).

    Returns
    -------
    dict
        Ответ от ЮKassa после подтверждения платежа.
    """
    idempotence_key = str(uuid.uuid4())
    response = Payment.capture(
        payment_id,
        {
            "amount": {
                "value": value,
                "currency": "RUB"
            }
        },
        idempotence_key
    )

    return response