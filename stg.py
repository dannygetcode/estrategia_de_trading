#en colab solo es instalar yfinance y ipywidgets para la lista desplegable
#pip install yfinance
#pip install ipywidgets

import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from ipywidgets import widgets, interact

# dependiendo del activo habria que hacer una funcion para que cada ticker tenga el valor del punto por contrato adecuado o manulamente cambiar en 'contract_value_per_point'el valor adecuado que corresponda
def backtest_strategy(ticker, start_date='1997-01-01', end_date='2024-06-30', initial_capital=1000, stop_loss=10, contract_value_per_point=20):
    data = yf.download(ticker, start=start_date, end=end_date)

    # Calcular medias móviles
    data['SMA200'] = data['Close'].rolling(window=200).mean()
    data['SMA5'] = data['Close'].rolling(window=5).mean()

    # Inicializar variables
    position_size = 1
    capital = initial_capital
    capital_history = []
    in_position = False
    entry_price = 0.0
    annual_stats = {}

    # Agregar columnas de resultados
    data['IsDownDay'] = data['Close'] < data['Open']
    data['ConsecDownDays'] = data['IsDownDay'].rolling(window=3).sum().shift(1).fillna(0)
    data['LongCondition'] = (data['ConsecDownDays'] >= 3) & (data['Close'] > data['SMA200'])
    data['ExitCondition'] = data['Close'] > data['SMA5']

    # Simulación del backtesting
    for year, year_data in data.groupby(data.index.year):
        annual_stats[year] = {
            'total_positions': 0,
            'winning_positions': 0,
            'losing_positions': 0,
            'total_points_gained': 0.0,
            'total_points_lost': 0.0,
            'capital_start': capital,
            'capital_end': capital
        }
        for i in range(len(year_data)):
            close = year_data['Close'].iloc[i]
            long_condition = year_data['LongCondition'].iloc[i]
            exit_condition = year_data['ExitCondition'].iloc[i]

            if long_condition and not in_position:
                in_position = True
                entry_price = close
                annual_stats[year]['total_positions'] += 1
            elif in_position:
                if close < entry_price - stop_loss:
                    # Aplicar stop loss
                    in_position = False
                    points_lost = position_size * stop_loss
                    capital -= points_lost * contract_value_per_point
                    annual_stats[year]['losing_positions'] += 1
                    annual_stats[year]['total_points_lost'] += stop_loss
                elif exit_condition:
                    in_position = False
                    if close > entry_price:
                        points_gained = position_size * (close - entry_price)
                        capital += points_gained * contract_value_per_point
                        annual_stats[year]['winning_positions'] += 1
                        annual_stats[year]['total_points_gained'] += points_gained
                    else:
                        points_lost = position_size * (entry_price - close)
                        capital -= points_lost * contract_value_per_point
                        annual_stats[year]['losing_positions'] += 1
                        annual_stats[year]['total_points_lost'] += points_lost
            capital_history.append(capital)
            annual_stats[year]['capital_end'] = capital
        annual_stats[year]['return_pct'] = ((annual_stats[year]['capital_end'] - annual_stats[year]['capital_start']) / annual_stats[year]['capital_start']) * 100

    # Crear un DataFrame con los resultados anuales
    summary_df = pd.DataFrame(annual_stats).T
    summary_df.index.name = 'Year'
    summary_df['Return'] = summary_df['capital_end'] - summary_df['capital_start']
    summary_df['Return %'] = summary_df['return_pct']
    summary_df['Avg Winning Points'] = summary_df['total_points_gained'] / summary_df['winning_positions'].replace(0, np.nan)
    summary_df['Avg Losing Points'] = summary_df['total_points_lost'] / summary_df['losing_positions'].replace(0, np.nan)
    summary_df['Total Trades'] = summary_df['total_positions']
    summary_df['Winning Trades'] = summary_df['winning_positions']
    summary_df['Losing Trades'] = summary_df['losing_positions']
    summary_df['Points Gained'] = summary_df['total_points_gained']
    summary_df['Points Lost'] = summary_df['total_points_lost']

    # Mostrar resultados del backtesting
    print(f"\nResultados para {ticker}:")
    print(summary_df[['Total Trades', 'Return %', 'Points Gained', 'Points Lost']])

    # Mostrar resumen general
    total_positions = summary_df['Total Trades'].sum()
    winning_positions = summary_df['Winning Trades'].sum()
    losing_positions = summary_df['Losing Trades'].sum()
    total_points_gained = summary_df['Points Gained'].sum()
    total_points_lost = summary_df['Points Lost'].sum()
    total_return = summary_df['Return'].sum()
    total_return_pct = ((capital - initial_capital) / initial_capital) * 100
    average_winning_points = total_points_gained / winning_positions
    average_losing_points = total_points_lost / losing_positions

    print(f"\nResumen General para {ticker}:\n")
    print(f"Total posiciones: {total_positions}, \nPosiciones ganadoras: {winning_positions}, \nPosiciones perdedoras: {losing_positions}\n")
    print(f"Capital inicial: ${initial_capital:.2f}")
    print(f"Capital final: ${capital:.2f}\n")
    print(f"Retorno total: ${total_return:.2f}")
    print(f"Retorno total %: {total_return_pct:.2f}%\n")
    print(f"Puntos ganados totales: {total_points_gained:.2f}")
    print(f"Puntos perdidos totales: {total_points_lost:.2f}\n")
    print(f"Promedio de puntos ganados por operación ganadora: {average_winning_points:.2f}")
    print(f"Promedio de puntos perdidos por operación perdedora: {average_losing_points:.2f}")

    # Calcular retorno acumulado del activo
    data['Cumulative_Return'] = (data['Close'] / data['Close'].iloc[0])

    # Graficar el rendimiento de la estrategia vs el rendimiento del activo en términos porcentuales
    plt.figure(figsize=(14,7))
    strategy_returns = (np.array(capital_history) - initial_capital) / initial_capital * 100
    plt.plot(data.index, strategy_returns, label='Rendimiento de la Estrategia (%)', color='blue')
    plt.plot(data.index, (data['Cumulative_Return'] - 1) * 100, label=f'Rendimiento de {ticker} (%)', color='orange')
    plt.title(f'Comparación del Rendimiento de la Estrategia vs {ticker}')
    plt.xlabel('Fecha')
    plt.ylabel('Rendimiento (%)')
    plt.legend()
    plt.show()

# Lista de activos para el análisis, aqui se pueden agregar mas, pero hay que tomar en cuenta el valor por contrato o accion de cada activo
activos = ['^GSPC', 'AAPL', 'MSFT', 'GOOGL', 'AMZN', '^DJI ', '^IXIC', '^RUT', '^NYA']

# Crear una interfaz interactiva de la lista desplegable 'Activo'
dropdown = widgets.Dropdown(
    options=activos,
    value='^GSPC',
    description='Activo:',
)

interact(lambda activo: backtest_strategy(activo), activo=dropdown)
