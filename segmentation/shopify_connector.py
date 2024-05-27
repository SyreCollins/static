# shopify_connector.py
import shopify
from .models import Store

class ShopifyConnector:
    def __init__(self, store):
        self.store_domain = store.store_domain
        self.api_key = store.api_key
        self.password = store.password
        self.access_token = store.access_token
        self._activate_session()

    def _activate_session(self):
        if self.access_token:
            shopify.Session.setup(api_key=settings.SHOPIFY_API_KEY, secret=settings.SHOPIFY_API_SECRET)
            session = shopify.Session(self.store_domain, '2021-07', self.access_token)
            shopify.ShopifyResource.activate_session(session)
        else:
            shopify.ShopifyResource.set_site(f"https://{self.api_key}:{self.password}@{self.store_domain}/admin")

    def get_customers(self):
        return shopify.Customer.find()
