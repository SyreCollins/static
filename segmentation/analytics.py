import matplotlib.pyplot as plt

def plot_segments(customer_df):
    plt.scatter(customer_df['total_spent'], customer_df['orders_count'], c=customer_df['segment'])
    plt.xlabel('Total Spent')
    plt.ylabel('Orders Count')
    plt.title('Customer Segments')
    plt.show()