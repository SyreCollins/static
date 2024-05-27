from sklearn.cluster import KMeans

def segment_customers(customer_df, n_segments):
    kmeans = KMeans(n_clusters=n_segments)
    customer_df['segment'] = kmeans.fit_predict(customer_df[['total_spent', 'orders_count']])
    return customer_df