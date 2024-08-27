import streamlit as st
import pandas as pd
import requests
import plotly.express as px

def formata_numero(valor, prefixo = ''):
    for unidade in ['', 'mil']:
        if valor < 1000:
            return f'{prefixo} {valor:.2f} {unidade}'
        valor /= 1000
    return f'{prefixo} {valor:.2f} milhões'

st.title('Dashboard de vendas :shopping_trolley:')

url = 'https://labdados.com/produtos'
regioes = ['Brasil', 'Centro-Oeste', 'Nordeste', 'Norte', 'Sudeste', 'Sul']

st.sidebar.title('Filtros')
regiao = st.sidebar.selectbox('Região', regioes)

if regiao == 'Brasil':
    regiao = ''

todos_anos = st.sidebar.checkbox('Dados de todo o período', value = True)
if todos_anos:
    ano = ''
else:
    ano = st.sidebar.slider('Ano', 2020, 2023)

query_string = {'regiao' : regiao.lower(), 'ano' : ano}

response = requests.get(url, params = query_string)
dados = pd.DataFrame.from_dict(response.json())
dados['Data da Compra'] = pd.to_datetime(dados['Data da Compra'], format = '%d/%m/%Y')

filtro_vendedores = st.sidebar.multiselect('Vendedores', dados['Vendedor'].unique())

if filtro_vendedores:
    dados = dados[dados['Vendedor'].isin(filtro_vendedores)]

# Tabelas
## Tabelas de receita
receita_estados = dados.groupby('Local da compra')[['Preço']].sum()
receita_estados = dados\
        .drop_duplicates(subset = 'Local da compra')[['Local da compra', 'lat', 'lon']]\
        .merge(receita_estados, left_on='Local da compra', right_index=True)\
        .sort_values('Preço', ascending=False)

receita_mensal = dados.set_index('Data da Compra').groupby(pd.Grouper(freq = 'M'))[['Preço']].sum().reset_index()
receita_mensal['Ano'] = receita_mensal['Data da Compra'].dt.year
receita_mensal['Mês'] = receita_mensal['Data da Compra'].dt.month_name()

receita_categoria = dados.groupby('Categoria do Produto')[['Preço']].sum().sort_values('Preço', ascending=False)

## Tabelas de quantidade de vendas
qtd_vendas_estados = dados.groupby('Local da compra')['Preço'].count()
qtd_vendas_estados = dados\
        .drop_duplicates(subset = 'Local da compra')[['Local da compra', 'lat', 'lon']]\
        .merge(qtd_vendas_estados, left_on='Local da compra', right_index=True)\
        .sort_values('Preço', ascending=False)

vendas_mensal = pd.DataFrame(dados.set_index('Data da Compra').groupby(pd.Grouper(freq = 'M'))['Preço'].count()).reset_index()
vendas_mensal['Ano'] = vendas_mensal['Data da Compra'].dt.year
vendas_mensal['Mês'] = vendas_mensal['Data da Compra'].dt.month_name()

## Tabela de vendas por categoria
qtd_vendas_categoria = dados.groupby('Categoria do Produto')['Preço'].count().sort_values(ascending = False)

## Tabelas de vendedores
vendedores = pd.DataFrame(dados.groupby('Vendedor')['Preço'].agg(['sum', 'count']))

# Gráficos
fig_mapa_receita = px.scatter_geo(receita_estados,
                                  lat = 'lat',
                                  lon = 'lon',
                                  scope = 'south america',
                                  size = 'Preço',
                                  template = 'seaborn',
                                  hover_name = 'Local da compra',
                                  hover_data = {'lat' : False, 'lon' : False},
                                  title = 'Receita por estado')

fig_receita_mensal = px.line(receita_mensal, 
                            x = 'Mês',
                            y = 'Preço',
                            markers = True,
                            range_y = (0, receita_mensal.max()),
                            color = 'Ano',
                            line_dash='Ano',
                            title = 'Receita Mensal')
fig_receita_mensal.update_layout(yaxis_title = 'Receita')

fig_receita_estado = px.bar(receita_estados.head(),
                            x = 'Local da compra',
                            y = 'Preço',
                            text_auto=True,
                            title = 'Top 5 estados em vendas')
fig_receita_estado.update_layout(yaxis_title = 'Receita')

fig_receita_categoria = px.bar(receita_categoria,
                               text_auto=True,
                               title = 'Receita por categoria')
fig_receita_categoria.update_layout(yaxis_title = 'Receita')

fig_mapa_qtd_vendas = px.scatter_geo(qtd_vendas_estados,
                                    lat = 'lat',
                                    lon = 'lon',
                                    scope = 'south america',
                                    size = 'Preço',
                                    template = 'seaborn',
                                    hover_name = 'Local da compra',
                                    hover_data = {'lat' : False, 'lon' : False},
                                    title = 'Vendas por estado')

fig_qtd_vendas_mensal = px.line(vendas_mensal, 
                                x = 'Mês',
                                y = 'Preço',
                                markers = True, 
                                range_y = (0,vendas_mensal.max()), 
                                color = 'Ano', 
                                line_dash = 'Ano',
                                title = 'Quantidade de vendas mensal')

fig_vendas_estado = px.bar(qtd_vendas_estados.head(),
                           x = 'Local da compra',
                           y = 'Preço',
                           text_auto=True,
                           title = 'Top 5 estados')
fig_vendas_estado.update_layout(yaxis_title = 'Quantidade de vendas')

fig_vendas_categoria = px.bar(qtd_vendas_categoria,
                              text_auto = True,
                              title = 'Top 5 categorias')
fig_vendas_categoria.update_layout(showlegend = False, yaxis_title = 'Quantidade de vendas')

# Visualização do streamlit
aba1, aba2, aba3 = st.tabs(['Receita', 'Qtd de vendas', 'Vendedores'])

with aba1: #Receitas

    col1, col2 = st.columns(2)

    with col1:
        st.metric('Receita:', formata_numero(dados['Preço'].sum(), 'R$'))
        st.plotly_chart(fig_mapa_receita, use_container_width=True)
        st.plotly_chart(fig_receita_estado, use_container_width=True)

    with col2:
        st.metric('Quantidade de vendas:', formata_numero(dados.shape[0]))
        st.plotly_chart(fig_receita_mensal, use_container_width=True)
        st.plotly_chart(fig_receita_categoria, use_container_width=True )

    st.dataframe(dados)
    st.dataframe(qtd_vendas_estados)

with aba2: # Quantidade de vendas

    col1, col2 = st.columns(2)

    with col1:
        st.metric('Receita:', formata_numero(dados['Preço'].sum(), 'R$'))
        st.plotly_chart(fig_mapa_qtd_vendas, use_container_width = True)
        st.plotly_chart(fig_vendas_estado, use_container_width = True)

    with col2:
        st.metric('Quantidade de vendas:', formata_numero(dados.shape[0]))
        st.plotly_chart(fig_qtd_vendas_mensal, use_container_width = True)
        st.plotly_chart(fig_vendas_categoria, use_container_width = True)

with aba3: # Vendedores

    qtd_vendedores = st.number_input('Quantidade de vendedores', 2, 10, 5)
    col1, col2 = st.columns(2)

    with col1:
        st.metric('Receita:', formata_numero(dados['Preço'].sum(), 'R$'))
        fig_receita_vendedores = px.bar(
            vendedores[['sum']].sort_values('sum').head(qtd_vendedores),
            x='sum',
            y=vendedores[['sum']].sort_values(['sum'], ascending=False).head(qtd_vendedores).index,
            text_auto=True,
            title=f'Top {qtd_vendedores} vendedores (receita)')
        st.plotly_chart(fig_receita_vendedores)

    with col2:
        st.metric('Quantidade de vendas:', formata_numero(dados.shape[0]))
        fig_vendas_vendedores = px.bar(
            vendedores[['count']].sort_values('count').head(qtd_vendedores),
            x='count',
            y=vendedores[['count']].sort_values(['count'], ascending=False).head(qtd_vendedores).index,
            text_auto=True,
            title=f'Top {qtd_vendedores} vendedores (quantidade de vendas)')
        st.plotly_chart(fig_vendas_vendedores)
