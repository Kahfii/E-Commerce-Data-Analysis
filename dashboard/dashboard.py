import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_option_menu import option_menu

def main():
    try:
        data = pd.read_csv("dashboard/e-commerce_cleaned.csv")
        df = pd.DataFrame(data)
    except Exception as e:
        st.error(f"Error loading dataset: {e}")
        return

    with st.sidebar:
        selected = option_menu(
            "Menu",
            ["Home", "RFM Analysis", "Profile"],
            icons=["house", "bar-chart", "person-circle"],
            menu_icon="cast",
            default_index=0,
        )
    
    if selected == "Home":
        st.title("Analisis Data E-Commerce")
        st.header("5 Kategori Produk yang Paling Sering Dibeli oleh Pelanggan E-Commerce (Grafik 1)")

        
        available_years = sorted(df['year'].dropna().unique())
        available_years.insert(0, "Semua Tahun")  
        selected_year = st.selectbox("Pilih Tahun:", available_years)

        if selected_year == "Semua Tahun":
            filtered_df = df
        else:
            filtered_df = df[df['year'] == int(selected_year)]

        # Top 5 kategori produk
        category_products = (
            filtered_df.groupby('product_category_name_english')
            .size()
            .reset_index(name='jumlah')
            .sort_values(by='jumlah', ascending=False)
        )
        top_5_categories = category_products.head(5)

        title_suffix = f"di Tahun {selected_year}" if selected_year != "Semua Tahun" else "untuk Semua Tahun"
        fig = px.bar(
            top_5_categories,
            x='product_category_name_english',
            y='jumlah',
            color='jumlah',
            color_continuous_scale='Blues',
            labels={'product_category_name_english': 'Nama Kategori Produk', 'jumlah': 'Jumlah'},
            title=f"5 Kategori Produk yang Paling Sering Dibeli {title_suffix}"
        )

        fig.update_layout(
            xaxis=dict(title='Nama Kategori Produk'),
            yaxis=dict(title='Jumlah'),
            title=dict(font=dict(size=16)),
            xaxis_tickangle=45
        )
        st.plotly_chart(fig)

        # Top 5 daerah dengan pendapatan tertinggi
        st.header("5 Daerah dengan Volume Pendapatan Tertinggi di Platform E-Commerce (Grafik 2)")
        
        total_revenue_per_state = (
                filtered_df.groupby('customer_state')['total_price']
                .sum()
                .reset_index(name='total_pendapatan')
                .sort_values(by='total_pendapatan', ascending=False)
            )
        top_5_states = total_revenue_per_state.head(5)

        fig_two = px.bar(
                top_5_states,
                x='customer_state',
                y='total_pendapatan',
                color='total_pendapatan',
                color_continuous_scale='Greens',
                labels={'customer_state': 'Provinsi', 'total_pendapatan': 'Total Pendapatan'},
                title=f"5 Daerah dengan Volume Pendapatan Tertinggi {title_suffix}"
            )

        fig_two.update_layout(
                xaxis=dict(title='State'),
                yaxis=dict(title='Total Pendapatan'),
                title=dict(font=dict(size=16)),
                xaxis_tickangle=45
            )
        st.plotly_chart(fig_two)    

        # Pendapatan Bulanan e-commerce
        if {'year', 'month', 'total_price'}.issubset(filtered_df.columns):
            st.header("Pendapatan Bulanan pada Platform E-Commerce (Grafik 3)")
            monthly_sales = filtered_df.groupby(['year', 'month'])['total_price'].sum().reset_index()
            monthly_sales['period'] = pd.to_datetime(monthly_sales[['year', 'month']].assign(day=1))

            fig3 = px.line(
                monthly_sales,
                x="period",
                y="total_price",
                labels={'period': 'Periode', 'total_price': 'Total Pendapatan'},
                title=f"Pendapatan Bulanan {title_suffix}"
            )

            fig3.update_layout(
                xaxis=dict(title='Periode'),
                yaxis=dict(title='Total Pendapatan'),
                title=dict(font=dict(size=16)),
                xaxis_tickangle=45
            )
            st.plotly_chart(fig3)
        else:
            st.error("Kolom 'year', 'month', atau 'total_price' tidak ditemukan dalam dataset.")
        
    elif selected == "RFM Analysis":
        st.title("RFM Analysis")
        df_use = df.copy()

        df_use['order_purchase_timestamp'] = pd.to_datetime(df_use['order_purchase_timestamp'])

        reference_date = df_use['order_purchase_timestamp'].max()

        rfm = df_use.groupby('customer_unique_id').agg({
            'order_purchase_timestamp': lambda x: (reference_date - x.max()).days,  # Recency
            'customer_id': 'count',  # Frequency
            'total_price': 'sum'  # Monetary
        }).reset_index()

        rfm.rename(columns={
            'order_purchase_timestamp': 'Recency',
            'customer_id': 'Frequency',
            'total_price': 'Monetary'
        }, inplace=True)

        #Pengelompokkan Pelanggan
        rfm['Recency_Category'] = pd.cut(rfm['Recency'], bins=[0, 30, 90, 180, 365, rfm['Recency'].max()],
                                        labels=['<30 hari', '30-90 hari', '90-180 hari', '180-365 hari', '>365 hari'])
        rfm['Frequency_Category'] = pd.cut(rfm['Frequency'], bins=[0, 1, 3, 5, 10, rfm['Frequency'].max()],
                                            labels=['1x', '2-3x', '4-5x', '6-10x', '>10x'])
        rfm['Monetary_Category'] = pd.cut(rfm['Monetary'], bins=[0, 100, 500, 1000, 5000, rfm['Monetary'].max()],
                                        labels=['<100', '100-500', '500-1000', '1000-5000', '>5000'])

        # Visualisasi Distribusi Recency
        st.subheader("Distribusi Recency")
        recency_counts = rfm['Recency_Category'].value_counts().sort_index()
        fig_recency = px.bar(
            x=recency_counts.index,
            y=recency_counts.values,
            labels={'x': 'Kategori Recency', 'y': 'Jumlah Pelanggan'},
            title="Distribusi Recency"
        )
        st.plotly_chart(fig_recency)

        # Visualisasi Distribusi Frequency
        st.subheader("Distribusi Frequency")
        frequency_counts = rfm['Frequency_Category'].value_counts().sort_index()
        fig_frequency = px.bar(
            x=frequency_counts.index,
            y=frequency_counts.values,
            labels={'x': 'Kategori Frequency', 'y': 'Jumlah Pelanggan'},
            title="Distribusi Frequency"
        )
        st.plotly_chart(fig_frequency)

        # Visualisasi Distribusi Monetary
        st.subheader("Distribusi Monetary")
        monetary_counts = rfm['Monetary_Category'].value_counts().sort_index()
        fig_monetary = px.bar(
            x=monetary_counts.index,
            y=monetary_counts.values,
            labels={'x': 'Kategori Monetary', 'y': 'Jumlah Pelanggan'},
            title="Distribusi Monetary"
        )
        st.plotly_chart(fig_monetary)

        
        st.subheader("Top 10 Customers Berdasarkan Recency, Frequency, dan Monetary")

        # Top Recency
        top_recency = rfm.sort_values(by="Recency", ascending=True).head(10)
        fig_top_recency = px.bar(
            top_recency,
            x="Recency",
            y="customer_unique_id",
            orientation='h',
            color="Recency",
            color_continuous_scale="Blues_r",
            labels={"Recency": "Recency (Hari Sejak Pembelian Terakhir)", "customer_unique_id": "Customer Unique ID"},
            title="10 Customers dengan Recency Terendah"
        )
        fig_top_recency.update_layout(yaxis=dict(title='Customer Unique ID'), xaxis=dict(title='Recency (Hari)'))
        st.plotly_chart(fig_top_recency)

        # Top Frequency
        top_frequency = rfm.sort_values(by="Frequency", ascending=False).head(10)
        fig_top_frequency = px.bar(
            top_frequency,
            x="Frequency",
            y="customer_unique_id",
            orientation='h',
            color="Frequency",
            color_continuous_scale="Greens",
            labels={"Frequency": "Frequency (Jumlah Transaksi)", "customer_unique_id": "Customer Unique ID"},
            title="10 Customers dengan Frequency Tertinggi"
        )
        fig_top_frequency.update_layout(yaxis=dict(title='Customer Unique ID'), xaxis=dict(title='Frequency (Jumlah Transaksi)'))
        st.plotly_chart(fig_top_frequency)

        # Top Monetary
        top_monetary = rfm.sort_values(by="Monetary", ascending=False).head(10)
        fig_top_monetary = px.bar(
            top_monetary,
            x="Monetary",
            y="customer_unique_id",
            orientation='h',
            color="Monetary",
            color_continuous_scale="Oranges_r",
            labels={"Monetary": "Monetary (Jumlah Pengeluaran)", "customer_unique_id": "Customer Unique ID"},
            title="10 Customers dengan Monetary Tertinggi"
        )
        fig_top_monetary.update_layout(yaxis=dict(title='Customer Unique ID'), xaxis=dict(title='Monetary (Jumlah Pengeluaran)'))
        st.plotly_chart(fig_top_monetary)

        st.subheader("Tabel RFM Analysis")
        st.dataframe(rfm)

    elif selected == "Profile":
        st.title("Profil Pengembang Aplikasi")
        st.write("Nama: Rahman Ilyas Al Kahfi")
        st.write("Email: ilyasalkahfi98@gmail.com")
        st.write("ID Dicoding: kahfii")

if __name__ == "__main__":
    main()
