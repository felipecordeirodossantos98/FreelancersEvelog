from datetime import datetime, time

import pandas as pd
import streamlit as st

from parser import montar_objeto
from calculos import (
    calcular_pagamentos,
    calcular_jornadas,
    calcular_periodo_pagamento,
    DIA_PAGAMENTO,
    ROTULO_DIA_PAGAMENTO
)
from componentes import exibir_marcacoes
from exportacao import gerar_planilha_presenca

st.set_page_config(
    page_title="Freelancers Evelog",
    page_icon="images/evelog-favicon.svg",
    layout="wide"
)

import streamlit.components.v1 as components

components.html(
    """
    <script>
        window.parent.addEventListener("beforeunload", function (event) {
            event.preventDefault();
            event.returnValue = "";
        });
    </script>
    """,
    height=0,
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

st.title("Freelancers Evelog")

col1, _ = st.columns([1, 2])

with col1:

    arquivo = st.file_uploader(
        "Selecione a planilha",
        type=["xls", "xlsx"]
    )


if arquivo:

    dados = montar_objeto(arquivo)

    # O período é sempre o ciclo de pagamento configurado.
    data_referencia_relatorio = datetime.strptime(
        dados["periodo"]["fim"],
        "%Y-%m-%d"
    ).date()

    inicio_pagamento, fim_pagamento = calcular_periodo_pagamento(
        data_referencia_relatorio
    )

    inicio_geral = inicio_pagamento
    fim_geral = fim_pagamento

    pagamentos = calcular_pagamentos(
        dados,
        data_inicio_pagamento=inicio_pagamento,
        data_fim_pagamento=fim_pagamento,
    )

    col2, _ = st.columns([1, 2])

    with col2:
        st.info(
            f"{dados['periodo']['inicio']} até {dados['periodo']['fim']}"
        )

        st.success(
            f"Período de pagamento ({DIA_PAGAMENTO}): "
            f"{inicio_geral.strftime('%d/%m/%Y')} até "
            f"{fim_geral.strftime('%d/%m/%Y')}"
        )

        pesquisa = st.text_input("Pesquisar funcionário")

        # ==================================================
        # EXPORTAR FOLHA DE PRESENÇA
        # ==================================================
        arquivo_presenca, quantidade_ativos = gerar_planilha_presenca(
            pagamentos=pagamentos,
            marcacoes_manuais=st.session_state["marcacoes_manuais"],
            periodo_origem=dados["periodo"],
            inicio_periodo=inicio_geral,
            fim_periodo=fim_geral,
        )

        st.download_button(
            "📄 Baixar folha de presença",
            data=arquivo_presenca,
            file_name=(
                "presenca_"
                f"{inicio_geral.strftime('%Y-%m-%d')}_a_"
                f"{fim_geral.strftime('%Y-%m-%d')}.xlsx"
            ),
            mime=(
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            ),
            use_container_width=True,
            help=(
                f"Gera a planilha para impressão com {quantidade_ativos} "
                "funcionário(s) que possuem marcações no período. "
                "Marcações adicionadas manualmente aparecem em verde."
            ),
        )

        st.caption(
            f"Folha de presença: {quantidade_ativos} funcionário(s) ativo(s) "
            "no período."
        )

    inicio = datetime.combine(inicio_pagamento, time.min)
    fim = datetime.combine(fim_pagamento, time.max)

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

        marcacoes_manuais_funcionario = (
            st.session_state["marcacoes_manuais"][chave_funcionario]
        )

        todas_marcacoes = sorted(
            funcionario["marcacoes"] + marcacoes_manuais_funcionario
        )

        # Sem filtro livre: exibe e calcula somente o ciclo de pagamento.
        marcacoes = [
            marcacao
            for marcacao in todas_marcacoes
            if inicio_geral <= marcacao.date() <= fim_geral
        ]

        if not marcacoes:
            continue

        with st.container(border=True):

            st.subheader(f"👤 {funcionario['nome_exibicao']}")

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

                if nova_marcacao in todas_marcacoes:
                    st.warning("Essa marcação já existe.")
                else:
                    marcacoes_manuais_funcionario.append(nova_marcacao)
                    marcacoes_manuais_funcionario.sort()
                    st.rerun()

            st.caption(
                "Período de pagamento: "
                f"{inicio_pagamento.strftime('%d/%m/%Y')} até "
                f"{fim_pagamento.strftime('%d/%m/%Y')}"
            )

            # ==================================================
            # CALCULAR JORNADAS
            # ==================================================
            jornadas = calcular_jornadas(
                marcacoes,
                data_inicio_pagamento=inicio_pagamento,
                data_fim_pagamento=fim_pagamento,
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

            col_pix, col_valor = st.columns([3, 1])

            with col_pix:
                st.markdown(f"#### **PIX:** `{pix}`")

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
                marcacoes_manuais=marcacoes_manuais_funcionario,
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
                tipo = jornada.get("tipo", "")
                valor = jornada.get("valor", 0)
                horas_extras = jornada.get("horas_extras", 0)

                if tipo == "diaria":
                    tipo_exibicao = "Diária"
                    valor_exibicao = f"R$ {valor:.2f}"

                elif tipo == "diaria_com_horas_extras":
                    tipo_exibicao = "Diária + horas extras"
                    valor_exibicao = f"R$ {valor:.2f}"

                elif tipo == "horas_extras_complemento_pagamento":
                    tipo_exibicao = (
                        "Horas extras — complemento "
                        f"{ROTULO_DIA_PAGAMENTO}"
                    )
                    valor_exibicao = f"+ R$ {valor:.2f}"

                elif tipo == "diaria_ja_paga_pagamento":
                    tipo_exibicao = (
                        "Diária — já paga "
                        f"{ROTULO_DIA_PAGAMENTO} anterior"
                    )
                    valor_exibicao = f"R$ {valor:.2f}"

                elif tipo == "adiantamento_dia_pagamento":
                    tipo_exibicao = (
                        "Adiantamento "
                        f"{ROTULO_DIA_PAGAMENTO}"
                    )
                    valor_exibicao = f"R$ {valor:.2f}"

                elif tipo == "adiantamento_marcacao_unica":
                    tipo_exibicao = "Adiantamento"
                    valor_exibicao = f"R$ {valor:.2f}"

                else:
                    tipo_exibicao = ""
                    valor_exibicao = f"R$ {valor:.2f}"

                horas_extras_exibicao = (
                    f"{horas_extras}h"
                    if horas_extras
                    else ""
                )

                tabela.append(
                    {
                        "Entrada": (
                            entrada.strftime("%d/%m/%Y %H:%M")
                            if entrada
                            else ""
                        ),
                        "Saída": (
                            saida.strftime("%d/%m/%Y %H:%M")
                            if saida
                            else "Sem saída"
                        ),
                        "Horas": jornada.get("horas", ""),
                        "Horas extras": horas_extras_exibicao,
                        "Tipo": tipo_exibicao,
                        "Valor": valor_exibicao,
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
                    "Nenhuma jornada encontrada para o período de pagamento."
                )
