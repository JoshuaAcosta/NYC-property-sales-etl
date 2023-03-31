import os
import glob
from pathlib import Path
import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(page_title='NYC Property Sales Dashboard', page_icon=':bar_chart:', layout='wide')
st.title("NYC Property Sales between 2003 and 2022")

#Reading data from csv file
#parent_dir = Path(os.getenv("PARENT_DIR"))
data_path = PATH("https://github.com/JoshuaAcosta/NYC-property-sales-etl/tree/master/data")
raw_path = data_path.joinpath("raw")
#stage_path = data_path.joinpath("stage")
production_path = data_path.joinpath("production")

../data

@st.cache_data
def read_sales_data(csv_path):
    all_files = glob.glob(str(production_path) + "/*.csv")
    df_list = [pd.read_csv(csv_file, header=0) for csv_file in all_files]
    df = pd.concat(df_list, ignore_index=True)
    df['sale_date'] = pd.to_datetime(df['sale_date'])
    df['month_year'] = df['sale_date'].dt.strftime('%Y-%m')
    df['year'] = df['sale_date'].dt.strftime('%Y')
    return df

df = read_sales_data(production_path)

#neighborhood selection box
neighborhoods_list = sorted(df.neighborhood.unique()) 
neighborhood_selection = st.sidebar.selectbox(label="Select a neighborhood:", options=neighborhoods_list, index=3)

#building class check box
BUILDING_CLASS = ['01 ONE FAMILY HOMES',
                       '02 TWO FAMILY HOMES',
                       '03 THREE FAMILY HOMES',
                       '04 TAX CLASS 1 CONDOS',
                       '07 RENTALS - WALKUP APARTMENTS',
                       '08 RENTALS - ELEVATOR APARTMENTS',
                       '09 COOPS - WALKUP APARTMENTS',
                       '10 COOPS - ELEVATOR APARTMENTS',
                       '12 CONDOS - WALKUP APARTMENTS',
                       '13 CONDOS - ELEVATOR APARTMENTS',
                       '14 RENTALS - 4-10 UNIT',
                       '15 CONDOS - 2-10 UNIT RESIDENTIAL']

building_class_selection = st.sidebar.multiselect(label="Select one of more building class:", options=BUILDING_CLASS, default='01 ONE FAMILY HOMES')

#sort data for options selected
filtered_sales_df = df[df["neighborhood"] == neighborhood_selection]
filtered_sales_df = filtered_sales_df[filtered_sales_df["building_class_category"].isin(building_class_selection )]

with st.container():
    col1, col2 = st.columns(2)

    # Chart No. 1: Total Number of Monthly Sales By Property Class
    with col1:
        total_num_sales = filtered_sales_df.groupby(['month_year','building_class_category'])['neighborhood'].count().reset_index(name='count')
        title1 = alt.TitleParams("Total Number of Sales By Property Class", anchor='middle')
        chart1 = alt.Chart(total_num_sales, title=title1).mark_bar().encode(
                    x= alt.X('month_year', title='Date'), 
                    y= alt.Y('count', title='Number of Sales') , 
                    color= alt.Color('building_class_category', legend=None))
        
        st.altair_chart(chart1, use_container_width=True)

    # Chart No. 2: Group by type of home and month, and calculate the average sale price
    with col2:
        avg_price_by_home_type = filtered_sales_df.groupby(['month_year','building_class_category'])['sale_price'].mean().reset_index(name='sale_price')
        title2 = alt.TitleParams("Average Sale Price by Property Class", anchor='middle')
        chart2 = alt.Chart(avg_price_by_home_type, title=title2).mark_line().encode(
                    x= alt.X('month_year', title='Date'), 
                    y= alt.Y('sale_price', title='Average Sale Price'), 
                    color= alt.Color('building_class_category', legend=None))
        st.altair_chart(chart2, use_container_width=True)

with st.container():
    col3, col4 = st.columns(2)
    # Chart No. 3: Calculate the year-over-year growth for each type of home
    with col3:
        avg_price_growth_by_home_type = filtered_sales_df.groupby(['year','building_class_category']).agg({'sale_price':'mean'}).sort_values(by=['building_class_category', 'year'])
        avg_price_growth_by_home_type['per_change'] = (avg_price_growth_by_home_type.groupby('building_class_category')['sale_price'].apply(pd.Series.pct_change) * 100)

        title3 = alt.TitleParams("Annual Average Sale Price Growth Rate by Property Class", anchor='middle')
        chart3 = alt.Chart(avg_price_growth_by_home_type.reset_index(), title=title3).mark_line().encode(
                    x= alt.X('year', title='Year'),
                    y= alt.Y('per_change', title='Average Year Sale Price Growth'),
                    color= alt.Color('building_class_category', legend=None))
        st.altair_chart(chart3, use_container_width=True)

    # Chart No. 4: Calculate the average price per square foot for each property type
    with col4:
        filtered_sqft_sale_df = filtered_sales_df[filtered_sales_df.gross_square_feet != 0]
        filtered_sqft_sale_df['price_per_square_feet'] = filtered_sqft_sale_df['sale_price'] / filtered_sqft_sale_df['gross_square_feet']
        avg_sqft_by_home_type = filtered_sqft_sale_df.groupby(['year','building_class_category']).agg({'price_per_square_feet':'mean'}).sort_values(by=['building_class_category', 'year'])
        avg_sqft_by_home_type['sqft_per_change'] = (avg_sqft_by_home_type.groupby('building_class_category')['price_per_square_feet'].apply(pd.Series.pct_change) * 100)
        title4 = alt.TitleParams("Annual Average Price Per Square Feet by Property Class", anchor='middle')
        chart4 = alt.Chart(avg_sqft_by_home_type.reset_index(), title=title4).mark_line().encode(
                    x= alt.X('year', title='Year'), 
                    y= alt.Y('sqft_per_change', title='Average Year Sale Price Growth'), 
                    color= alt.Color('building_class_category', legend=None))
        st.altair_chart(chart4, use_container_width=True)