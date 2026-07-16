import pandas as pd
import streamlit as st

from parser import montar_objeto
from calculos import (
    calcular_pagamentos,
    calcular_jornadas
)

st.set_page_config(
    page_title="Controle de Freelancers",
    layout="wide"
)

PIX = {
    "aline tuany": "39258452836",
    "ana paula godoy": "42898858889",
    "catiane souza": "57750108840",
    "cristina ferreira": "38133973864",
    "daiane lopes": "47183807827",
    "francisca regia": "11940220513",
    "fredson barbos": "",
    "gabriele rosario": "11963576137",
    "gisele rufino": "942965526",
    "jackson pedroso": "11972912437",
    "janisson martins": "94538379387",
    "jaqueline santos": "11914770363",
    "joseane alves": "",
    "kelly cristina": "948623050",
    "mara emilia": "11959045387",
    "miqueias gomes": "49034321819",
    "pedro guilherme": "11326378481",
    "prescila andrade": "11984451066",
    "roney silva": "49550945898",
    "roniele cazumba": "8475363512",
    "sebastiao silva": "75991583823",
    "vitoria caroline": "73981762804",
}

NOMES = {
    "aline tuany": "Aline Tuany",
    "ana paula godoy": "Ana Paula Godoy",
    "catiane souza": "Catiane Souza",
    "cristina ferreira": "Cristina Ferreira",
    "daiane lopes": "Daiane Lopes",
    "francisca regia": "Francisca Regia",
    "fredson barbos": "Fredson Barbos",
    "gabriele rosario": "Gabriele Rosario",
    "gisele rufino": "Gisele Rufino",
    "jackson pedroso": "Jackson Pedroso",
    "janisson martins": "Janisson Martins",
    "jaqueline santos": "Jaqueline Santos",
    "joseane alves": "Joseane Alves",
    "kelly cristina": "Kelly Cristina",
    "mara emilia": "Mara Emilia",
    "miqueias gomes": "Miqueias Gomes",
    "pedro guilherme": "Pedro Guilherme",
    "prescila andrade": "Prescila Andrade",
    "roney silva": "Roney Silva",
    "roniele cazumba": "Roniele Cazumba",
    "sebastiao silva": "Sebastiao Silva",
    "vitoria caroline": "Vitoria Caroline",
}

st.title("Controle de Pagamento de Freelancers")

col1, _ = st.columns([1, 2])

with col1:

    arquivo = st.file_uploader(
        "Selecione a planilha",
        type=["xls", "xlsx"]
    )

if arquivo:

    dados = montar_objeto(arquivo)

    pagamentos = calcular_pagamentos(dados)

    col2, _ = st.columns([1, 2])

    with col2:

        st.info(
            f"{dados['periodo']['inicio']} até {dados['periodo']['fim']}"
        )

        pesquisa = st.text_input(
            "Pesquisar funcionário"
        )

    for funcionario in pagamentos:

        if (
            pesquisa
            and pesquisa.lower() not in funcionario["nome"].lower()
        ):
            continue

        if not funcionario["marcacoes"]:
            continue

        with st.container(border=True):

            st.subheader(f"👤 {funcionario['nome_exibicao']}")

            marcacoes = funcionario["marcacoes"]

            if len(marcacoes) == 1:

                periodo = (
                    marcacoes[0],
                    marcacoes[0]
                )

            else:

                periodo = st.select_slider(
                    "Período",
                    options=marcacoes,
                    value=(
                        marcacoes[0],
                        marcacoes[-1]
                    ),
                    format_func=lambda dt: dt.strftime("%d/%m/%Y %H:%M"),
                    key=f"slider_{funcionario['id']}"
                )

            inicio, fim = periodo

            marcacoes_filtradas = [
                m
                for m in marcacoes
                if inicio <= m <= fim
            ]

            jornadas = calcular_jornadas(
                marcacoes_filtradas
            )

            total = sum(
                j["valor"]
                for j in jornadas
            )

            pix = PIX.get(
                funcionario["nome"].lower(),
                "Não cadastrado"
            )

            col_pix, col_valor = st.columns([3, 1])

            with col_pix:
                st.write(f"**PIX:** `{pix}`")

            with col_valor:
                st.metric(
                    "Valor a Receber",
                    f"R$ {total:.2f}"
                )

            tabela = []

            for jornada in jornadas:

                tabela.append({

                    "Entrada":
                        jornada["entrada"].strftime("%d/%m/%Y %H:%M"),

                    "Saída":
                        jornada["saida"].strftime("%d/%m/%Y %H:%M"),

                    "Horas":
                        jornada["horas"],

                    "Valor":
                        f"R$ {jornada['valor']:.2f}"

                })

            if tabela:

                st.dataframe(
                    pd.DataFrame(tabela),
                    use_container_width=True,
                    hide_index=True
                )

            else:

                st.info(
                    "Nenhuma jornada encontrada para o período selecionado."
                )