from backend.schemas.payments import MercadoPagoPaymentRequest, PaymentItem
from my_agents.openai_agents.tools.mercadopago_client import create_preference


def run_test():
    print("🧪 Testing Mercado Pago payment link creation...")

    request = MercadoPagoPaymentRequest(
        order_id="ORD-2001",
        payer_name="Fernando López",
        items=[
            PaymentItem(
                id="prod-001", title="Empanadas x12", quantity=1, unit_price=4200.0
            ),
            PaymentItem(
                id="prod-002", title="Coca-Cola", quantity=2, unit_price=1800.0
            ),
        ],
        success_url="https://example.com/success",
        failure_url="https://example.com/failure",
        pending_url="https://example.com/pending",
    )

    items = [item.model_dump() for item in request.items]

    back_urls = {
        "success": "https://example.com/success",
        "failure": "https://example.com/failure",
        "pending": "https://example.com/pending",
    }

    result = create_preference(items, back_urls)

    print("✅ Result:")
    print(result)

    assert "init_point" in result, "Missing 'init_point'"
    assert result["init_point"].startswith("https://www.mercadopago.com"), "Invalid URL"

    print("🧪 Test passed!")


if __name__ == "__main__":
    run_test()
