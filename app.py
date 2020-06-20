import streamlit as st

import stock_analysis.SessionState as sst
from stock_analysis.stock_data import load_stock_data, available_stocks, modify_available_stocks, search_symbol
from stock_analysis.stock_plots import altair_chart

if __name__ == "__main__":
    st.title('Stock Viewer')
    modify_checkbox = st.sidebar.checkbox("Modify stock list")
    if modify_checkbox:
        selected_stocks = st.empty()
        modified_stocks = st.sidebar.multiselect('Modify stocks', available_stocks(), available_stocks())
        save_button = st.sidebar.button("Save")
        if save_button:
            modify_available_stocks(modified_stocks)
    else:
        selected_stocks = st.sidebar.multiselect('Select stocks', available_stocks())

    timescale = st.sidebar.selectbox('Timeframe', [30, 60, 90, 200], index=1)
    moving_averages = st.sidebar.multiselect('Include moving averages', ["MA21", "MA50", "MA200", "EMA21", "EMA50", "EMA200"], default=["MA21"])
    state = sst.get(key=0)
    ta_placeholder = st.sidebar.empty()
    search_stock = ta_placeholder.text_input("Search for a stock", key=state.key)

    if len(search_stock) > 0:
        st.header("Stock search")
        df = search_symbol(search_stock)
        st.dataframe(df)
        if len(df) > 0:
            select_button_1 = st.button(f"Add {df['1. symbol'].iloc[0]}")
            select_button_2, select_button_3 = False, False
            if len(df) > 1: select_button_2 = st.button(f"Add {df['1. symbol'].iloc[1]}")
            if len(df) > 2: select_button_3 = st.button(f"Add {df['1. symbol'].iloc[2]}")
            stock_list = available_stocks()
            if select_button_1: stock_list.append(df['1. symbol'].iloc[0])
            if len(df) > 1 and select_button_2: stock_list.append(df['1. symbol'].iloc[1])
            if len(df) > 2 and select_button_3: stock_list.append(df['1. symbol'].iloc[2])
            if select_button_1 or select_button_2 or select_button_3:
                state.key += 1
                modify_available_stocks(stock_list)
                # selected_stocks = st.sidebar.multiselect('Select stocks', available_stocks(), selected_stocks)

    if isinstance(selected_stocks, (tuple, list)) and len(selected_stocks) > 0 and not modify_checkbox:
        st.header("Visualization")
        for s in selected_stocks:
            source = load_stock_data(s)
            st.altair_chart(altair_chart(s, source, timescale, moving_averages), use_container_width=True)

    if not isinstance(selected_stocks, (tuple, list))  or (len(search_stock) == 0 and len(selected_stocks) == 0):
        st.text("nothing to do here :)")
