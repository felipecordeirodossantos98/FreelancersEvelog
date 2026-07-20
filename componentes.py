from collections import defaultdict
from html import escape

import streamlit as st


def exibir_marcacoes(
    marcacoes,
    marcacoes_manuais,
    chave_funcionario,
    inicio_periodo,
    fim_periodo
):
    st.markdown("##### Marcações")

    marcacoes_filtradas = [
        marcacao
        for marcacao in marcacoes
        if inicio_periodo <= marcacao <= fim_periodo
    ]

    marcacoes_por_dia = defaultdict(list)
    conjunto_manuais = set(marcacoes_manuais)

    for marcacao in sorted(marcacoes_filtradas):
        marcacoes_por_dia[marcacao.date()].append(
            {
                "data_hora": marcacao,
                "manual": marcacao in conjunto_manuais
            }
        )

    if not marcacoes_por_dia:
        st.info("Nenhuma marcação encontrada no período selecionado.")
        return

    dias = sorted(marcacoes_por_dia)

    max_linhas = max(
        len(marcacoes_por_dia[dia])
        for dia in dias
    )

    cabecalho_datas = "".join(
        f"<th>{dia.strftime('%d/%m/%Y')}</th>"
        for dia in dias
    )

    linhas_html = []

    for indice_linha in range(max_linhas):
        celulas = []

        for dia in dias:
            registros = marcacoes_por_dia[dia]

            if indice_linha >= len(registros):
                celulas.append("<td>&nbsp;</td>")
                continue

            registro = registros[indice_linha]
            marcacao = registro["data_hora"]
            horario = escape(marcacao.strftime("%H:%M"))

            classe = (
                "marcacao-manual"
                if registro["manual"]
                else "marcacao-original"
            )

            celulas.append(
                f'<td><span class="{classe}">{horario}</span></td>'
            )

        if indice_linha == 0:
            legenda = (
                f'<td class="coluna-legenda coluna-horarios" '
                f'rowspan="{max_linhas}">HORÁRIOS</td>'
            )
        else:
            legenda = ""

        linhas_html.append(
            f"<tr>{legenda}{''.join(celulas)}</tr>"
        )

    css = """
<style>
.tabela-marcacoes-wrapper {
    width: 100%;
    overflow-x: auto;
    margin-top: 0.5rem;
    margin-bottom: 0.5rem;
}

.tabela-marcacoes {
    width: 100%;
    border-collapse: collapse;
    table-layout: fixed;
    min-width: 900px;
    font-size: 0.92rem;
}

.tabela-marcacoes th,
.tabela-marcacoes td {
    border: 1px solid rgba(128, 128, 128, 0.35);
    box-sizing: border-box;
}

.tabela-marcacoes th {
    background-color: rgba(128, 128, 128, 0.16);
    padding: 10px 8px;
    text-align: center;
    font-weight: 700;
    white-space: nowrap;
}

.tabela-marcacoes td {
    height: 42px;
    padding: 8px;
    text-align: center;
    vertical-align: middle;
    white-space: nowrap;
}

.coluna-legenda {
    width: 110px;
    min-width: 110px;
    text-align: left !important;
    padding-left: 10px !important;
    font-weight: 700;
    background-color: rgba(128, 128, 128, 0.10);
}

.coluna-horarios {
    vertical-align: middle !important;
}

.marcacao-original {
    display: inline-block;
    min-width: 46px;
}

.marcacao-manual {
    display: inline-block;
    min-width: 46px;
    padding: 4px 8px;
    border-radius: 6px;
    background-color: rgba(46, 160, 67, 0.18);
    border: 1px solid rgba(46, 160, 67, 0.55);
    font-weight: 700;
}

.legenda-manual {
    font-size: 0.82rem;
    opacity: 0.75;
    margin-bottom: 0.8rem;
}
</style>
"""

    tabela = (
        '<div class="tabela-marcacoes-wrapper">'
        '<table class="tabela-marcacoes">'
        "<thead>"
        "<tr>"
        '<th class="coluna-legenda">DATA</th>'
        f"{cabecalho_datas}"
        "</tr>"
        "</thead>"
        "<tbody>"
        f"{''.join(linhas_html)}"
        "</tbody>"
        "</table>"
        "</div>"
        '<div class="legenda-manual">'
        "</div>"
    )

    st.markdown(
        css + tabela,
        unsafe_allow_html=True
    )

    # Lista fixa das marcações inseridas manualmente
    if marcacoes_manuais:
        st.markdown("###### Marcações adicionadas manualmente")

        for indice, marcacao in enumerate(sorted(marcacoes_manuais)):

            with st.container(border=True):

                col_data, col_botao = st.columns(
                    [10, 1],
                    vertical_alignment="center"
                )

                with col_data:
                    st.markdown(
                        f"""
        **{marcacao.strftime("%d/%m/%Y")}**
        &nbsp;&nbsp;—&nbsp;&nbsp;
        {marcacao.strftime("%H:%M")}
        """
                    )

                with col_botao:
                    if st.button(
                        "🗑️",
                        key=(
                            f"remover_{indice}_"
                            f"{marcacao.isoformat()}"
                        ),
                        use_container_width=True
                    ):
                        marcacoes_manuais.remove(marcacao)
                        st.rerun()