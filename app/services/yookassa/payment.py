from yookassa import Payment, Configuration
import uuid

from config import YOOKASSA_SHOP_ID, YOOKASSA_API_KEY


Configuration.account_id = YOOKASSA_SHOP_ID
Configuration.secret_key = YOOKASSA_API_KEY


def create_payment(amount: str):
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

def get_status(payment_id: str):   
    
    res = Payment.find_one(payment_id)
    return res.status


# ============================ не требуется для проекта ===========================================

def cancel_payment(payment_id: str):
    res = Payment.cancel(payment_id)


def payment_confirmation(payment_id: str):
    idempotence_key = str(uuid.uuid4())
    response = Payment.capture(payment_id,
                                {
                                 "amount": {
                                    "value": "2.00",
                                    "currency": "RUB"
                                    }
                                },
                                idempotence_key
                                )

    return response