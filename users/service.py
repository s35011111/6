from typing import Dict, Any

import stripe
from django.conf import settings
from django.core.exceptions import ValidationError

stripe.api_key = settings.STRIPE_SECRET_KEY


class StripeService:
    @staticmethod
    def create_product(
            name: str,
            description: str = None,
            metadata: Dict[str, Any] = None
    ) -> stripe.Product:
        """Create a product in Stripe"""
        try:
            product = stripe.Product.create(
                name=name,
                description=description,
                metadata=metadata or {}
            )
            return product
        except stripe.error.StripeError as e:
            raise ValidationError(f"Stripe error creating product: {str(e)}")

    @staticmethod
    def create_price(
            product_id: str,
            unit_amount: int,
            currency: str = 'usd',
            recurring: bool = False,
            interval: str = None
    ) -> stripe.Price:
        """Create a price for a product in Stripe"""
        try:
            price_data = {
                'product': product_id,
                'unit_amount': unit_amount,  # Amount in cents
                'currency': currency,
            }

            if recurring and interval:
                price_data['recurring'] = {'interval': interval}

            price = stripe.Price.create(**price_data)
            return price
        except stripe.error.StripeError as e:
            raise ValidationError(f"Stripe error creating price: {str(e)}")

    @staticmethod
    def create_checkout_session(
            price_id: str,
            success_url: str,
            cancel_url: str,
            customer_email: str = None,
            metadata: Dict[str, Any] = None,
            mode: str = 'payment'
    ) -> stripe.checkout.Session:
        """Create a checkout session for a price"""
        try:
            session_data = {
                'line_items': [{
                    'price': price_id,
                    'quantity': 1,
                }],
                'mode': mode,
                'success_url': success_url,
                'cancel_url': cancel_url,
                'metadata': metadata or {},
            }

            if customer_email:
                session_data['customer_email'] = customer_email

            session = stripe.checkout.Session.create(**session_data)
            return session
        except stripe.error.StripeError as e:
            raise ValidationError(f"Stripe error creating checkout session: {str(e)}")

    @staticmethod
    def retrieve_checkout_session(session_id: str) -> stripe.checkout.Session:
        """Retrieve a checkout session"""
        try:
            return stripe.checkout.Session.retrieve(session_id)
        except stripe.error.StripeError as e:
            raise ValidationError(f"Stripe error retrieving session: {str(e)}")

    @staticmethod
    def deactivate_product(product_id):
        """Deactivate a product in Stripe"""
        try:
            return stripe.Product.update(product_id)
        except stripe.error.StripeError as e:
            raise ValidationError(f"Stripe error deactivating product: {str(e)}")

    @staticmethod
    def update_product_metadata(product_id: str, metadata: Dict[str, Any]):
        """Update product metadata"""
        try:
            return stripe.Product.update(product_id)
        except stripe.error.StripeError as e:
            raise ValidationError(f"Stripe error updating product: {str(e)}")