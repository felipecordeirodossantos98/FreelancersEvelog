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
    "agda munhoz": "11914713728",
    "aline tuany": "39258452836",
    "ana paula godoy": "42898858889",
    "ana paula cesar": "43039982818",
    "ana paula silva": "23437649809",
    "brayan": "11951695591",
    "catiane souza": "57750108840",
    "cristina ferreira": "38133973864",
    "daiane lopes": "47183807827",
    "douglas": "11930109539",
    "ednaldo": "11958572381",
    "francisca regia": "11940220513",
    "fredson barbos": "",
    "gabriele rosario": "11963576137",
    "gisele rufino": "942965526",
    "igor lopes": "11930889568",
    "jackson pedroso": "11972912437",
    "janisson martins": "94538379387",
    "jaqueline santos": "11914770363",
    "joseane alves": "",
    "kelly cristina": "948623050",
    "mara emilia": "11959045387",
    "matheus gabriel": "11999497102",
    "miqueias gomes": "49034321819",
    "paloma costa": "40698268822",
    "pedro barbosa": "58091970862",
    "pedro guilherme": "11326378481",
    "prescila andrade": "11984451066",
    "priscila": "",
    "roney silva": "49550945898",
    "roniele cazumba": "8475363512",
    "sebastiao silva": "75991583823",
    "sheila": "11951672697",
    "thalita": "",
    "vitoria caroline": "73981762804",
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