import altair as alt
import pandas as pd
from stock_analysis.stock_data import insert_fibonacci_levels
import datetime


def altair_chart(symbol: str, data: pd.DataFrame, timescale: str, moving_averages):
    df = data.copy()
    insert_fibonacci_levels(df)  # refresh fibonaccis with reduced data
    df = df[df.date > df.date.iloc[-1] - pd.to_timedelta(f"{timescale}day")]
    df = df.assign(label=df.index.strftime('%d.%m'))
    df = df.assign(idx=pd.RangeIndex(len(df)))
    fib_values = df[["fib_0", "fib_24", "fib_38", "fib_50", "fib_62", "fib_79", "fib_100"]].iloc[0].tolist()
    highest_fibo = [f for f in fib_values if f - df.high.max() >= 0.][0]
    lowest_fibo = [f for f in fib_values if f - df.low.min() <= 0.][-1]
    y_domain = min([lowest_fibo] + [df[m.lower()].min() for m in moving_averages]) if len(moving_averages) > 0 else lowest_fibo, \
               max([highest_fibo] + [df[m.lower()].max() for m in moving_averages]) if len(moving_averages) > 0 else highest_fibo
    # now create plot
    open_close_color = alt.condition("datum.open <= datum.close", alt.value("#06982d"), alt.value("#ae1325"))
    base = alt.Chart(df).encode(x=alt.X('label:O', axis=alt.Axis(labelAngle=-45, title='Date', grid=True), sort=df.idx.values), color=open_close_color).properties(title=f'{symbol} Chart')
    # base = alt.Chart(df).encode(alt.X('date:T', axis=alt.Axis(format='%d.%m', labelAngle=-45, title='Date', grid=True)), color=open_close_color).properties(title=f'{symbol} Chart')
    rule = base.mark_rule().encode(alt.Y('low:Q', title='Price', axis=alt.Axis(values=fib_values, format="$.2f", tickCount=len(fib_values)), scale=alt.Scale(zero=False, domain=y_domain)), alt.Y2('high:Q'))
    bar = base.mark_bar().encode(alt.Y('open:Q'), alt.Y2('close:Q'))
    fib_layers = []
    for fib_name, fib_val in zip(('fib_0', 'fib_24', 'fib_38', 'fib_50', 'fib_62', 'fib_79', 'fib_100'), fib_values):
        if fib_val > highest_fibo or fib_val < lowest_fibo:
            continue
        fib_layers.append(base.mark_line(size=1.3, strokeDash=[3, 7]).encode(y=fib_name, color=alt.value('grey')))
    ma21 = base.mark_line().encode(y='ma21', color=alt.value('grey'))
    ma50 = base.mark_line().encode(y='ma50', color=alt.value('blue'))
    ma200 = base.mark_line().encode(y='ma200', color=alt.value('green'))
    ema21 = base.mark_line().encode(y='ema21', color=alt.value('grey'))
    ema50 = base.mark_line().encode(y='ema50', color=alt.value('blue'))
    ema200 = base.mark_line().encode(y='ema200', color=alt.value('green'))
    mas = [m for m, ml in zip([ma21, ma50, ma200, ema21, ema50, ema200], ["MA21", "MA50", "MA200", "EMA21", "EMA50", "EMA200"]) if ml in moving_averages]
    plot = alt.layer(*tuple(fib_layers), *tuple(mas), rule , bar).properties(height=400)
    return plot

    # start_date = df.label.iloc[0]
    # tfib0 = base.mark_text(align='left', baseline='bottom').transform_filter(alt.datum.label == start_date).encode(y=alt.Y('fib_0:Q', title=None), x=alt.X('label:O', sort=df.idx.values), text='fib_0:Q', color=alt.value('#000'))
    # tfib24 = base.mark_text(align='left', baseline='bottom').transform_filter(alt.datum.label == start_date).encode(y=alt.Y('fib_24:Q', title=None), x=alt.X('label:O', sort=df.idx.values), text='fib_24:Q', color=alt.value('#000'))
    # tfib38 = base.mark_text(align='left', baseline='bottom').transform_filter(alt.datum.label == start_date).encode(y=alt.Y('fib_38:Q', title=None), x=alt.X('label:O', sort=df.idx.values), text='fib_38:Q', color=alt.value('#000'))
    # tfib50 = base.mark_text(align='left', baseline='bottom').transform_filter(alt.datum.label == start_date).encode(y=alt.Y('fib_50:Q', title=None), x=alt.X('label:O', sort=df.idx.values), text='fib_50:Q', color=alt.value('#000'))
    # tfib63 = base.mark_text(align='left', baseline='bottom').transform_filter(alt.datum.label == start_date).encode(y=alt.Y('fib_63:Q', title=None), x=alt.X('label:O', sort=df.idx.values), text='fib_64:Q', color=alt.value('#000'))
    # tfib79 = base.mark_text(align='left', baseline='bottom').transform_filter(alt.datum.label == start_date).encode(y=alt.Y('fib_79:Q', title=None), x=alt.X('label:O', sort=df.idx.values), text='fib_79:Q', color=alt.value('#000'))
    # tfib100 = base.mark_text(align='left', baseline='bottom').transform_filter(alt.datum.label == start_date).encode(y=alt.Y('fib_100:Q', title=None), x=alt.X('label:O', sort=df.idx.values), text='fib_100:Q', color=alt.value('#000'))
    # return fib0 + fib24 + fib38 + fib50 + fib63 + fib79 + fib100 + ma21 + rule + bar + tfib0 + tfib24 + tfib38 + tfib50 + tfib63 + tfib79 + tfib100
    # nearest = alt.selection(type='single', nearest=True, on='mouseover', fields=['y'], empty='none')
    # selectors = base.mark_point().encode(x='label:O', opacity=alt.value(0)).add_selection(nearest)
    # points = base.mark_point().encode(opacity=alt.condition(nearest, alt.value(1), alt.value(0)))
    # text = base.mark_text(align='left', dx=5, dy=-5).encode(text=alt.condition(nearest, 'y:Q', alt.value(' ')))
    # rules = alt.Chart(df).mark_rule(color='gray').encode(y='y:Q').transform_filter(nearest)
    # return alt.layer(plot, selectors , points, text, rules )
