"""
Payment provider abstraction for Stripe + Razorpay.
V0: Not used (credits granted via /api/billing/v0-grant).
V1: Full implementation with webhook handlers.
"""
from dataclasses import dataclass
from app.config import get_settings


@dataclass
class CheckoutSession:
    checkout_url: str
    session_id: str
    provider: str


PLAN_MINUTES = {
    "lite": 100,
    "pro": 500,
}

PLAN_PRICES = {
    ("lite", "INR"): 49900,   # Rs 499 in paisa
    ("lite", "USD"): 700,     # $7 in cents
    ("pro", "INR"): 99900,    # Rs 999 in paisa
    ("pro", "USD"): 1300,     # $13 in cents
}

PAYG_RATES = {
    "INR": 10000,  # Rs 100 per 100 minutes in paisa
    "USD": 200,    # $2 per 100 minutes in cents
}


class PaymentService:
    """
    Unified payment service.
    Routes to Stripe (USD/international) or Razorpay (INR/Indian) based on currency.
    """

    def create_subscription_checkout(
        self, user_id: str, email: str, plan_tier: str, currency: str
    ) -> CheckoutSession:
        settings = get_settings()
        if settings.FEATURE_V0_MODE:
            raise NotImplementedError("Payments not available in V0 mode")

        if currency == "INR":
            return self._razorpay_subscription(user_id, email, plan_tier)
        else:
            return self._stripe_subscription(user_id, email, plan_tier, currency)

    def create_payg_checkout(
        self, user_id: str, email: str, minutes: int, currency: str
    ) -> CheckoutSession:
        settings = get_settings()
        if settings.FEATURE_V0_MODE:
            raise NotImplementedError("Payments not available in V0 mode")

        if currency == "INR":
            return self._razorpay_payg(user_id, minutes, currency)
        else:
            return self._stripe_payg(user_id, email, minutes, currency)

    def _stripe_subscription(
        self, user_id: str, email: str, plan_tier: str, currency: str
    ) -> CheckoutSession:
        import stripe
        settings = get_settings()
        stripe.api_key = settings.STRIPE_SECRET_KEY

        price_key = (plan_tier, currency)
        amount = PLAN_PRICES.get(price_key, 0)
        minutes = PLAN_MINUTES.get(plan_tier, 0)

        session = stripe.checkout.Session.create(
            mode="subscription",
            customer_email=email,
            line_items=[{
                "price_data": {
                    "currency": currency.lower(),
                    "unit_amount": amount,
                    "recurring": {"interval": "month"},
                    "product_data": {
                        "name": f"HookCut {plan_tier.title()} - {minutes} min/mo"
                    },
                },
                "quantity": 1,
            }],
            metadata={"user_id": user_id, "plan_tier": plan_tier},
            success_url=f"{settings.FRONTEND_URL}/billing?success=true",
            cancel_url=f"{settings.FRONTEND_URL}/billing?cancelled=true",
        )
        return CheckoutSession(
            checkout_url=session.url,
            session_id=session.id,
            provider="stripe",
        )

    def _stripe_payg(
        self, user_id: str, email: str, minutes: int, currency: str
    ) -> CheckoutSession:
        import stripe
        settings = get_settings()
        stripe.api_key = settings.STRIPE_SECRET_KEY

        amount = (minutes // 100) * PAYG_RATES.get(currency, 200)

        session = stripe.checkout.Session.create(
            mode="payment",
            customer_email=email,
            line_items=[{
                "price_data": {
                    "currency": currency.lower(),
                    "unit_amount": amount,
                    "product_data": {"name": f"HookCut PAYG - {minutes} minutes"},
                },
                "quantity": 1,
            }],
            metadata={
                "user_id": user_id,
                "purchase_type": "payg",
                "minutes": str(minutes),
            },
            success_url=f"{settings.FRONTEND_URL}/billing?success=true",
            cancel_url=f"{settings.FRONTEND_URL}/billing?cancelled=true",
        )
        return CheckoutSession(
            checkout_url=session.url,
            session_id=session.id,
            provider="stripe",
        )

    def _razorpay_subscription(
        self, user_id: str, email: str, plan_tier: str
    ) -> CheckoutSession:
        import razorpay
        settings = get_settings()
        client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )

        plan_id = (
            settings.RAZORPAY_PLAN_ID_LITE if plan_tier == "lite"
            else settings.RAZORPAY_PLAN_ID_PRO
        )

        subscription = client.subscription.create({
            "plan_id": plan_id,
            "total_count": 12,
            "notes": {"user_id": user_id, "plan_tier": plan_tier},
        })
        return CheckoutSession(
            checkout_url=subscription.get("short_url", ""),
            session_id=subscription["id"],
            provider="razorpay",
        )

    def _razorpay_payg(
        self, user_id: str, minutes: int, currency: str
    ) -> CheckoutSession:
        import razorpay
        settings = get_settings()
        client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )

        amount = (minutes // 100) * PAYG_RATES.get(currency, 10000)
        order = client.order.create({
            "amount": amount,
            "currency": currency,
            "notes": {
                "user_id": user_id,
                "purchase_type": "payg",
                "minutes": str(minutes),
            },
        })
        return CheckoutSession(
            checkout_url="",  # Razorpay uses client-side modal
            session_id=order["id"],
            provider="razorpay",
        )
