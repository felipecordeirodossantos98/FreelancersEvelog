from datetime import datetime

import pandas as pd
import streamlit as st

from parser import montar_objeto
from calculos import (
    calcular_pagamentos,
    calcular_jornadas
)
from componentes import exibir_marcacoes

st.set_page_config(
    page_title="Controle de Pagamento de Freelancers",
    layout="wide"
)

# Marcações adicionadas manualmente
if "marcacoes_manuais" not in st.session_state:
    st.session_state["marcacoes_manuais"] = {}

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

        datas = sorted({
            m.date()
            for funcionario in pagamentos
            for m in funcionario["marcacoes"]
        })

        periodo_geral = st.select_slider(
            "Período Geral",
            options=datas,
            value=(datas[0], datas[-1]),
            format_func=lambda d: d.strftime("%d/%m/%Y")
        )

        inicio_geral, fim_geral = periodo_geral

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

        chave_funcionario = (
            f"{dados['periodo']['inicio']}_"
            f"{dados['periodo']['fim']}_"
            f"{funcionario['id']}"
        )

        if chave_funcionario not in st.session_state["marcacoes_manuais"]:
            st.session_state["marcacoes_manuais"][chave_funcionario] = []

        # Junta marcações originais + manuais
        marcacoes = (
            funcionario["marcacoes"]
            + st.session_state["marcacoes_manuais"][chave_funcionario]
        )

        marcacoes.sort()

        # Aplica filtro geral
        marcacoes = [
            m
            for m in marcacoes
            if inicio_geral <= m.date() <= fim_geral
        ]

        if not marcacoes:
            continue

        with st.container(border=True):

            st.subheader(
                f"👤 {funcionario['nome_exibicao']}"
            )

            # ==================================================
            # MARCAÇÕES ORIGINAIS E MANUAIS
            # ==================================================

            marcacoes_manuais_funcionario = (
                st.session_state["marcacoes_manuais"][
                    chave_funcionario
                ]
            )

            todas_marcacoes = sorted(
                funcionario["marcacoes"]
                + marcacoes_manuais_funcionario
            )

            # Aplica o filtro do slider geral.
            marcacoes = [
                marcacao
                for marcacao in todas_marcacoes
                if inicio_geral <= marcacao.date() <= fim_geral
            ]

            # ==================================================
            # CHAVES DO SLIDER INDIVIDUAL
            # ==================================================

            chave_slider = (
                f"slider_{funcionario['id']}_"
                f"{inicio_geral}_{fim_geral}"
            )

            chave_periodo_salvo = (
                f"periodo_salvo_{funcionario['id']}_"
                f"{inicio_geral}_{fim_geral}"
            )

            # ==================================================
            # INSERIR MARCAÇÃO
            # ==================================================

            st.markdown("##### Inserir marcação")

            col_data, col_hora, col_botao = st.columns(
                [2, 2, 1],
                vertical_alignment="bottom"
            )

            with col_data:

                data_manual = st.date_input(
                    "Data",
                    value=inicio_geral,
                    min_value=inicio_geral,
                    max_value=fim_geral,
                    key=(
                        f"data_{chave_funcionario}_"
                        f"{inicio_geral}_{fim_geral}"
                    )
                )

            with col_hora:

                hora_manual = st.time_input(
                    "Horário",
                    key=f"hora_{chave_funcionario}"
                )

            with col_botao:

                adicionar = st.button(
                    "Adicionar",
                    key=f"btn_{chave_funcionario}",
                    use_container_width=True
                )

            if adicionar:

                nova_marcacao = datetime.combine(
                    data_manual,
                    hora_manual
                )

                # Verifica duplicidade em todas as marcações,
                # inclusive as que estão fora do filtro geral.
                if nova_marcacao in todas_marcacoes:

                    st.warning(
                        "Essa marcação já existe."
                    )

                else:

                    marcacoes_manuais_funcionario.append(
                        nova_marcacao
                    )

                    marcacoes_manuais_funcionario.sort()

                    st.rerun()

            # ==================================================
            # FUNCIONÁRIO SEM MARCAÇÕES NO PERÍODO GERAL
            # ==================================================

            if not marcacoes:

                st.info(
                    "Nenhuma marcação encontrada para este "
                    "funcionário no período geral selecionado."
                )

            else:

                # ==================================================
                # SLIDER INDIVIDUAL
                # ==================================================

                if len(marcacoes) == 1:

                    inicio = marcacoes[0]
                    fim = marcacoes[0]

                    st.session_state[
                        chave_periodo_salvo
                    ] = (
                        inicio,
                        fim
                    )

                    st.caption(
                        "Período: "
                        f"{inicio.strftime('%d/%m/%Y %H:%M')}"
                    )

                else:

                    periodo_padrao = (
                        marcacoes[0],
                        marcacoes[-1]
                    )

                    periodo_salvo = st.session_state.get(
                        chave_periodo_salvo,
                        periodo_padrao
                    )

                    inicio_salvo, fim_salvo = periodo_salvo

                    # Caso uma marcação usada como limite tenha sido
                    # removida, escolhe a opção disponível mais próxima.
                    inicio_salvo = min(
                        marcacoes,
                        key=lambda marcacao: abs(
                            marcacao - inicio_salvo
                        )
                    )

                    fim_salvo = min(
                        marcacoes,
                        key=lambda marcacao: abs(
                            marcacao - fim_salvo
                        )
                    )

                    if inicio_salvo > fim_salvo:

                        inicio_salvo = marcacoes[0]
                        fim_salvo = marcacoes[-1]

                    inicio, fim = st.select_slider(
                        "Período",
                        options=marcacoes,
                        value=(
                            inicio_salvo,
                            fim_salvo
                        ),
                        format_func=lambda dt: (
                            dt.strftime(
                                "%d/%m/%Y %H:%M"
                            )
                        ),
                        key=chave_slider
                    )

                    st.session_state[
                        chave_periodo_salvo
                    ] = (
                        inicio,
                        fim
                    )

                # ==================================================
                # FILTRAR MARCAÇÕES PELO SLIDER INDIVIDUAL
                # ==================================================

                marcacoes_filtradas = [
                    marcacao
                    for marcacao in marcacoes
                    if inicio <= marcacao <= fim
                ]

                # ==================================================
                # CALCULAR JORNADAS
                # ==================================================

                jornadas = calcular_jornadas(
                    marcacoes_filtradas
                )

                total = sum(
                    jornada.get("valor", 0)
                    for jornada in jornadas
                )

                # ==================================================
                # PIX E VALOR
                # ==================================================

                pix = PIX.get(
                    funcionario["nome"].lower(),
                    "Não cadastrado"
                )

                col_pix, col_valor = st.columns(
                    [3, 1]
                )

                with col_pix:

                    st.markdown(
                        f"#### **PIX:** `{pix}`"
                    )

                with col_valor:

                    st.metric(
                        "Valor a Receber",
                        f"R$ {total:.2f}"
                    )

                # ==================================================
                # TABELA DE MARCAÇÕES
                # ==================================================

                exibir_marcacoes(
                    marcacoes=marcacoes,
                    marcacoes_manuais=(
                        marcacoes_manuais_funcionario
                    ),
                    chave_funcionario=chave_funcionario,
                    inicio_periodo=inicio,
                    fim_periodo=fim
                )

                # ==================================================
                # TABELA DE JORNADAS
                # ==================================================

                tabela = []

                st.markdown("##### Jornadas")

                for jornada in jornadas:

                    entrada = jornada.get("entrada")
                    saida = jornada.get("saida")

                    tabela.append(
                        {
                            "Entrada": (
                                entrada.strftime(
                                    "%d/%m/%Y %H:%M"
                                )
                                if entrada
                                else ""
                            ),

                            "Saída": (
                                saida.strftime(
                                    "%d/%m/%Y %H:%M"
                                )
                                if saida
                                else "Sem saída"
                            ),

                            "Horas": jornada.get(
                                "horas",
                                ""
                            ),

                            "Valor": (
                                f"R$ "
                                f"{jornada.get('valor', 0):.2f}"
                            )
                        }
                    )

                if tabela:

                    st.dataframe(
                        pd.DataFrame(tabela),
                        use_container_width=True,
                        hide_index=True
                    )

                else:

                    st.info(
                        "Nenhuma jornada encontrada "
                        "para o período selecionado."
                    )
