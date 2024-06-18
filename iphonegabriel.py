import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import matplotlib.pyplot as plt

# Função para raspar preços de iPhones no site da Nomad
def get_usa_prices():
    url = "https://www.nomadglobal.com/conteudos/comprar-iphone-nos-eua"
    response = requests.get(url)
    content = response.content
    soup = BeautifulSoup(content, "html.parser")
    price_table = soup.find("table")
    
    iphones_usa = {}
    if price_table:
        rows = price_table.find_all("tr")
        for row in rows[1:]:
            cols = row.find_all("td")
            model = cols[0].text.strip()
            price_text = cols[1].text.strip().replace('US$', '').replace(',', '')
            try:
                # Verifica se o valor é uma string de número corretamente formatada
                if '.' in price_text:
                    price = float(price_text)
                else:
                    price = int(price_text)
            except ValueError:
                price = None
            iphones_usa[model] = price
    return iphones_usa

# Função para raspar preços de iPhones no site FazCapital
def get_brazil_prices():
    url_brasil = "https://fazcapital.com.br/quanto-custa-um-iphone/"
    response_brasil = requests.get(url_brasil)
    content_brasil = response_brasil.content
    soup_brasil = BeautifulSoup(content_brasil, "html.parser")
    prices_section = soup_brasil.find_all("h2", string="Quanto custa um iPhone novo em 2024?")[0].find_next("table")
    
    iphones_brasil = {}
    if prices_section:
        rows_brasil = prices_section.find_all("tr")
        for row in rows_brasil[1:]:
            cols = row.find_all("td")
            model = cols[0].text.strip().replace("Quanto custa um ", "")
            price_64GB = cols[1].text.strip() if len(cols) > 1 else ""
            price_128GB = cols[2].text.strip() if len(cols) > 2 else ""
            price_256GB = cols[3].text.strip() if len(cols) > 3 else ""
            price_512GB = cols[4].text.strip() if len(cols) > 4 else ""
            price_1TB = cols[5].text.strip() if len(cols) > 5 else ""
            try:
                if price_64GB and price_64GB != '–':
                    iphones_brasil[model + " - 64GB"] = float(price_64GB.replace('R$', '').replace('.', '').replace(',', '.'))
                if price_128GB and price_128GB != '–':
                    iphones_brasil[model + " - 128GB"] = float(price_128GB.replace('R$', '').replace('.', '').replace(',', '.'))
                if price_256GB and price_256GB != '–':
                    iphones_brasil[model + " - 256GB"] = float(price_256GB.replace('R$', '').replace('.', '').replace(',', '.'))
                if price_512GB and price_512GB != '–':
                    iphones_brasil[model + " - 512GB"] = float(price_512GB.replace('R$', '').replace('.', '').replace(',', '.'))
                if price_1TB and price_1TB != '–':
                    iphones_brasil[model + " - 1TB"] = float(price_1TB.replace('R$', '').replace('.', '').replace(',', '.'))
            except ValueError:
                pass
    return iphones_brasil

# Função para obter as cotações de moedas
def get_exchange_rates():
    url = 'https://api.exchangerate-api.com/v4/latest/USD'
    response = requests.get(url)
    data = response.json()
    return data['rates']

# Função para converter valores para BRL
def convert_to_brl(amount, rate):
    return amount * rate

# Função para calcular a economia
def calculate_savings(usa_price, brazil_price, exchange_rate):
    converted_usa_price = convert_to_brl(usa_price, exchange_rate)
    savings = brazil_price - converted_usa_price
    return savings, converted_usa_price

# Obter preços
usa_prices = get_usa_prices()
brazil_prices = get_brazil_prices()
all_models = sorted(set(usa_prices.keys()).union(set(brazil_prices.keys())))

# Streamlit App
st.title("Comparação de Preços de iPhones - Brasil vs EUA")

# Parte 1: Visualização de Preços
st.header("Visualização de Preços")
selected_model = st.selectbox("Selecione um modelo de iPhone:", all_models)

if selected_model:
    usa_price = usa_prices.get(selected_model, "Preço não disponível")
    brazil_price = brazil_prices.get(selected_model, "Preço não disponível")
    
    st.write(f"**Modelo:** {selected_model}")
    st.write(f"**Preço nos EUA:** {usa_price if usa_price != 'Preço não disponível' else 'N/A'}")
    st.write(f"**Preço no Brasil:** {brazil_price if brazil_price != 'Preço não disponível' else 'N/A'}")

# Parte 2: Gráficos Comparativos
st.header("Gráficos Comparativos")
valor_iphone_eua = st.number_input("Insira o valor do iPhone nos EUA (em dólares): ", min_value=0.0)
valor_iphone_brasil = st.number_input("Insira o valor do iPhone no Brasil (em reais): ", min_value=0.0)

if valor_iphone_eua > 0 and valor_iphone_brasil > 0:
    data = {
        'País': ['EUA', 'Brasil'],
        'Salário Mensal': [4400, 2879],
        'Despesas Mensais': [3230, 2383],
        'Valor do iPhone': [valor_iphone_eua, valor_iphone_brasil],
        'Inflação Anual': [0.02, 0.05]
    }

    df = pd.DataFrame(data)
    df['Poupança Mensal'] = df['Salário Mensal'] - df['Despesas Mensais']
    df['Poupança Anual Ajustada'] = df['Poupança Mensal'] * 12 * (1 - df['Inflação Anual'])
    df['Porcentagem do iPhone Economizado'] = (df['Poupança Anual Ajustada'] / df['Valor do iPhone']) * 100
    df['Dias Necessários para Pagar o iPhone'] = df['Valor do iPhone'] / (df['Salário Mensal'] / 22)

    st.write(df)

    fig, axes = plt.subplots(nrows=2, ncols=1, figsize=(12, 12))
    axes[0].bar(df['País'], df['Porcentagem do iPhone Economizado'], color=['blue', 'green'], width=0.2)
    axes[0].set_title('Porcentagem do Valor do iPhone Economizado até o Final do Ano')
    axes[0].set_xlabel('País')
    axes[0].set_ylabel('Porcentagem do Valor do iPhone Economizado (%)')
    for i, v in enumerate(df['Porcentagem do iPhone Economizado']):
        axes[0].text(i, v + 1, f'{v:.2f}%', ha='center', fontsize=12)

    axes[1].bar(df['País'], df['Dias Necessários para Pagar o iPhone'], color=['blue', 'green'], width=0.2)
    axes[1].set_title('Dias Necessários de Trabalho para Pagar o iPhone')
    axes[1].set_xlabel('País')
    axes[1].set_ylabel('Dias de Trabalho')
    for i, v in enumerate(df['Dias Necessários para Pagar o iPhone']):
        axes[1].text(i, v + 1, f'{v:.2f} dias', ha='center', fontsize=12)

    st.pyplot(fig)

# Parte 3: Comparação de Valores Convertidos
st.header("Comparação de Valores Convertidos")
selected_model_comparison = st.selectbox("Selecione um modelo de iPhone para comparação de valores:", all_models)

if selected_model_comparison:
    usa_price_comparison = usa_prices.get(selected_model_comparison, None)
    brazil_price_comparison = brazil_prices.get(selected_model_comparison, None)

    if usa_price_comparison and brazil_price_comparison:
        rates = get_exchange_rates()
        rate_to_brl = rates.get('BRL', None)

        if rate_to_brl:
            savings, converted_usa_price = calculate_savings(usa_price_comparison, brazil_price_comparison, rate_to_brl)
            st.write(f"**Modelo:** {selected_model_comparison}")
            st.write(f"**Preço nos EUA:** ${usa_price_comparison:.2f}")
            st.write(f"**Preço no Brasil:** R${brazil_price_comparison:.2f}")
            st.write(f"**Preço nos EUA convertido para reais:** R${converted_usa_price:.2f}")
            st.write(f"**Economia comprando nos EUA:** R${savings:.2f}")
        else:
            st.write("Erro ao carregar a cotação do BRL.")
    else:
        st.write("Preços não disponíveis para o modelo selecionado.")
