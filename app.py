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

    # O período automático usa a data final informada pelo próprio
    # relatório. Assim também funciona ao consultar arquivos antigos.
    data_referencia_relatorio = datetime.strptime(
        dados["periodo"]["fim"],
        "%Y-%m-%d"
    ).date()

    inicio_pagamento, fim_pagamento = calcular_periodo_pagamento(
        data_referencia_relatorio
    )

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

        datas = sorted({
            m.date()
            for funcionario in pagamentos
            for m in funcionario["marcacoes"]
        })

        periodo_livre = st.toggle(
            "Período livre",
            value=False,
            help=(
                "Desativado: usa automaticamente o período de pagamento. "
                "Ativado: libera os filtros como eram antes."
            )
        )

        if periodo_livre:

            periodo_geral = st.select_slider(
                "Período Geral",
                options=datas,
                value=(datas[0], datas[-1]),
                format_func=lambda d: d.strftime("%d/%m/%Y")
            )

            inicio_geral, fim_geral = periodo_geral

        else:

            inicio_geral = inicio_pagamento
            fim_geral = fim_pagamento

            st.success(
                f"Período de pagamento ({DIA_PAGAMENTO}): "
                f"{inicio_geral.strftime('%d/%m/%Y')} até "
                f"{fim_geral.strftime('%d/%m/%Y')}"
            )

        pesquisa = st.text_input(
            "Pesquisar funcionário"
        )

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
            "Baixar folha de presença",
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
            "no período. Correções manuais serão destacadas em verde."
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

            chave_slider_base = (
                f"slider_{funcionario['id']}_"
                f"{inicio_geral}_{fim_geral}"
            )

            # O select_slider mantém estado próprio no navegador. A versão
            # faz com que uma correção que amplie o período gere um widget
            # novo no rerun, garantindo que o ponteiro acompanhe o horário
            # recém-adicionado em vez de restaurar o limite antigo.
            chave_slider_versao = f"{chave_slider_base}_versao"

            if chave_slider_versao not in st.session_state:
                st.session_state[chave_slider_versao] = 0

            chave_slider = (
                f"{chave_slider_base}_"
                f"v{st.session_state[chave_slider_versao]}"
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

                    # No período livre, faz o slider individual acompanhar
                    # automaticamente uma correção adicionada fora dos
                    # limites atuais. Se a nova marcação já estiver dentro
                    # do intervalo selecionado, preserva o filtro do usuário.
                    if periodo_livre:

                        periodo_atual = st.session_state.get(
                            chave_periodo_salvo
                        )

                        if periodo_atual:
                            inicio_atual, fim_atual = periodo_atual

                            novo_inicio = min(
                                inicio_atual,
                                nova_marcacao
                            )
                            novo_fim = max(
                                fim_atual,
                                nova_marcacao
                            )

                            if (
                                novo_inicio != inicio_atual
                                or novo_fim != fim_atual
                            ):
                                st.session_state[
                                    chave_periodo_salvo
                                ] = (
                                    novo_inicio,
                                    novo_fim
                                )

                                # Força a criação de uma nova instância
                                # visual do slider no próximo rerun. Só fazemos
                                # isso quando a correção realmente ficou fora
                                # do intervalo atual; se estiver dentro, o
                                # filtro escolhido pelo usuário é preservado.
                                st.session_state[
                                    chave_slider_versao
                                ] += 1

                                # Limpa o estado da versão antiga para não
                                # acumular chaves de widgets na sessão.
                                st.session_state.pop(
                                    chave_slider,
                                    None
                                )

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
                # PERÍODO INDIVIDUAL
                # ==================================================

                if not periodo_livre:

                    # No modo padrão, o período é fixo pelo ciclo de
                    # pagamento. O usuário não precisa ajustar funcionário
                    # por funcionário.
                    inicio = datetime.combine(
                        inicio_pagamento,
                        time.min
                    )
                    fim = datetime.combine(
                        fim_pagamento,
                        time.max
                    )

                    st.caption(
                        "Período de pagamento: "
                        f"{inicio_pagamento.strftime('%d/%m/%Y')} até "
                        f"{fim_pagamento.strftime('%d/%m/%Y')}"
                    )

                elif len(marcacoes) == 1:

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

                    # Período livre: mantém exatamente o slider antigo.
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

                # A regra financeira é calculada usando TODAS as
                # marcações disponíveis do funcionário. O slider abaixo
                # funciona somente como filtro de exibição e do total,
                # sem alterar se uma jornada é normal, dobrada,
                # complemento ou adiantamento.
                if periodo_livre:
                    # No modo livre, mantém o cálculo antigo das jornadas
                    # completas. A única regra adicional é que qualquer
                    # dia com exatamente uma marcação vale R$ 110 como
                    # adiantamento.
                    jornadas_calculadas = calcular_jornadas(
                        todas_marcacoes,
                        adiantamento_em_qualquer_dia=True,
                    )
                else:
                    # No modo de pagamento, aplica a regra especial do
                    # ciclo configurado (por padrão, quinta a quinta).
                    jornadas_calculadas = calcular_jornadas(
                        todas_marcacoes,
                        data_inicio_pagamento=inicio_pagamento,
                        data_fim_pagamento=fim_pagamento,
                    )

                # Mantém no resultado apenas jornadas inteiramente dentro
                # do período individual selecionado. Para o adiantamento,
                # que não possui saída, basta a entrada estar no período.
                jornadas = []

                for jornada in jornadas_calculadas:

                    entrada_jornada = jornada.get("entrada")
                    saida_jornada = jornada.get("saida")

                    if entrada_jornada is None:
                        continue

                    if not (inicio <= entrada_jornada <= fim):
                        continue

                    if (
                        saida_jornada is not None
                        and not (inicio <= saida_jornada <= fim)
                    ):
                        continue

                    jornadas.append(jornada)

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
                    tipo = jornada.get("tipo", "")
                    valor = jornada.get("valor", 0)

                    if tipo == "normal":
                        tipo_exibicao = "Normal"
                        valor_exibicao = f"R$ {valor:.2f}"

                    elif tipo == "dobrada":
                        tipo_exibicao = "Dobrada"
                        valor_exibicao = f"R$ {valor:.2f}"

                    elif tipo == "dobrada_complemento_pagamento":
                        tipo_exibicao = (
                            "Dobrada — complemento "
                            f"{ROTULO_DIA_PAGAMENTO}"
                        )
                        valor_exibicao = f"+ R$ {valor:.2f}"

                    elif tipo == "normal_ja_pago_pagamento":
                        tipo_exibicao = (
                            "Normal — já pago "
                            f"{ROTULO_DIA_PAGAMENTO} anterior"
                        )
                        valor_exibicao = f"R$ {valor:.2f}"

                    elif tipo == "adiantamento_dia_pagamento":
                        tipo_exibicao = (
                            "Adiantamento "
                            f"{ROTULO_DIA_PAGAMENTO}"
                        )
                        valor_exibicao = f"R$ {valor:.2f}"

                    elif tipo in {
                        "adiantamento_periodo_livre",
                        "adiantamento_marcacao_unica",
                    }:
                        tipo_exibicao = "Adiantamento"
                        valor_exibicao = f"R$ {valor:.2f}"

                    else:
                        tipo_exibicao = ""
                        valor_exibicao = f"R$ {valor:.2f}"

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

                            "Tipo": tipo_exibicao,

                            "Valor": valor_exibicao
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
