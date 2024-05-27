import pandas as pd

def process_customer_data(customers):
    customer_list = []
    for customer in customers:
        customer_data = {
            'id': customer.id,
            'email': customer.email,
            'created_at': customer.created_at,
            'total_spent': customer.total_spent,
            'orders_count': customer.orders_count,
            'last_order_id': customer.last_order_id
        }
        customer_list.append(customer_data)
    return pd.DataFrame(customer_list)