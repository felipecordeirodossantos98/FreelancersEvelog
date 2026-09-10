from collections import defaultdict
from datetime import datetime, timedelta
from io import BytesIO

import xlsxwriter


DEPARTAMENTO_PADRAO = "Operacao"

# O relatório original reserva 31 colunas para os dias (B:AF), mesmo quando
# o período possui apenas alguns dias. Mantemos essa estrutura para a folha
# gerada pelo app ficar visualmente o mais próxima possível da original.
QUANTIDADE_COLUNAS_DIAS_ORIGINAL = 31
COLUNA_INICIAL_DIAS = 1  # B


def _datas_do_periodo(inicio, fim):
    data = inicio
    while data <= fim:
        yield data
        data += timedelta(days=1)


def _escrever_horarios(
    worksheet,
    linha,
    coluna,
    registros,
    formato_horario,
    formato_horario_manual,
    formato_manual_fonte,
    formato_original_fonte,
):
    if not registros:
        worksheet.write_blank(linha, coluna, None, formato_horario)
        return

    textos = [registro["data_hora"].strftime("%H:%M") for registro in registros]
    tem_manual = any(registro["manual"] for registro in registros)
    tem_original = any(not registro["manual"] for registro in registros)

    if tem_manual and not tem_original:
        worksheet.write(
            linha,
            coluna,
            "\n".join(textos),
            formato_horario_manual,
        )
        return

    if not tem_manual:
        worksheet.write(
            linha,
            coluna,
            "\n".join(textos),
            formato_horario,
        )
        return

    # Quando a célula contém ponto original e correção manual, deixa somente
    # o horário incluído no app em verde, preservando o restante em preto.
    fragmentos = []

    for indice, registro in enumerate(registros):
        if indice:
            fragmentos.append("\n")

        fragmentos.extend([
            formato_manual_fonte if registro["manual"] else formato_original_fonte,
            registro["data_hora"].strftime("%H:%M"),
        ])

    worksheet.write_rich_string(
        linha,
        coluna,
        *fragmentos,
        formato_horario,
    )


def gerar_planilha_presenca(
    pagamentos,
    marcacoes_manuais,
    periodo_origem,
    inicio_periodo,
    fim_periodo,
    departamento=DEPARTAMENTO_PADRAO,
):
    """
    Gera a folha de presença seguindo de perto o layout do relatório original.

    Diferenças intencionais em relação ao arquivo bruto:
    - inclui somente funcionários que possuem alguma marcação no período;
    - inclui correções feitas manualmente no app;
    - horários adicionados manualmente aparecem em verde.
    """

    datas = list(_datas_do_periodo(inicio_periodo, fim_periodo))

    # B:AF = 31 colunas no modelo original. Se o período livre for maior que
    # isso, o arquivo cresce apenas o necessário para não perder datas.
    quantidade_colunas_dias = max(
        QUANTIDADE_COLUNAS_DIAS_ORIGINAL,
        len(datas),
    )

    primeira_coluna = COLUNA_INICIAL_DIAS
    ultima_coluna = primeira_coluna + quantidade_colunas_dias - 1

    funcionarios_ativos = []

    for funcionario in pagamentos:
        chave_funcionario = (
            f"{periodo_origem['inicio']}_"
            f"{periodo_origem['fim']}_"
            f"{funcionario['id']}"
        )

        manuais = sorted(
            marcacoes_manuais.get(chave_funcionario, [])
        )
        conjunto_manuais = set(manuais)

        todas_marcacoes = sorted(
            funcionario["marcacoes"] + manuais
        )

        marcacoes_periodo = [
            marcacao
            for marcacao in todas_marcacoes
            if inicio_periodo <= marcacao.date() <= fim_periodo
        ]

        if not marcacoes_periodo:
            continue

        por_dia = defaultdict(list)

        for marcacao in marcacoes_periodo:
            por_dia[marcacao.date()].append({
                "data_hora": marcacao,
                "manual": marcacao in conjunto_manuais,
            })

        funcionarios_ativos.append({
            "id": funcionario["id"],
            "nome": funcionario["nome_exibicao"],
            "por_dia": por_dia,
        })

    funcionarios_ativos.sort(key=lambda item: item["id"])

    saida = BytesIO()
    workbook = xlsxwriter.Workbook(saida, {"in_memory": True})
    worksheet = workbook.add_worksheet("Tabela de registro de presença")

    azul = "#0000FF"
    verde = "#008A35"

    # ------------------------------------------------------------------
    # FORMATOS — reproduzem fontes, cores e bordas do arquivo original.
    # ------------------------------------------------------------------
    formato_titulo = workbook.add_format({
        "font_name": "Calibri",
        "font_size": 24,
        "bold": True,
        "font_color": azul,
        "align": "center",
        "valign": "vcenter",
    })

    formato_meta = workbook.add_format({
        "font_name": "Calibri",
        "font_size": 9,
        "font_color": azul,
        "align": "left",
        "valign": "vcenter",
    })

    formato_info_esquerda = workbook.add_format({
        "font_name": "Times New Roman",
        "font_size": 11,
        "bold": True,
        "font_color": azul,
        "top": 1,
        "bottom": 1,
        "border_color": azul,
        "align": "left",
        "valign": "vcenter",
    })

    formato_info_direita = workbook.add_format({
        "font_name": "Times New Roman",
        "font_size": 11,
        "bold": True,
        "font_color": azul,
        "top": 1,
        "bottom": 1,
        "border_color": azul,
        "align": "right",
        "valign": "vcenter",
    })

    formato_info_borda = workbook.add_format({
        "font_name": "Times New Roman",
        "font_size": 11,
        "bold": True,
        "font_color": azul,
        "top": 1,
        "bottom": 1,
        "border_color": azul,
        "valign": "vcenter",
    })

    formato_dia = workbook.add_format({
        "font_name": "Calibri",
        "font_size": 9,
        "bold": True,
        "font_color": azul,
        "border": 1,
        "border_color": azul,
        "align": "center",
        "valign": "vcenter",
    })

    formato_horario = workbook.add_format({
        "font_name": "Calibri",
        "font_size": 8,
        "font_color": "#000000",
        "top": 1,
        "bottom": 1,
        "left": 1,
        "right": 1,
        "border_color": azul,
        "align": "center",
        "valign": "vcenter",
        "text_wrap": True,
    })

    formato_horario_manual = workbook.add_format({
        "font_name": "Calibri",
        "font_size": 8,
        "bold": True,
        "font_color": verde,
        "top": 1,
        "bottom": 1,
        "left": 1,
        "right": 1,
        "border_color": azul,
        "align": "center",
        "valign": "vcenter",
        "text_wrap": True,
    })

    formato_manual_fonte = workbook.add_format({
        "font_name": "Calibri",
        "font_size": 8,
        "bold": True,
        "font_color": verde,
    })

    formato_original_fonte = workbook.add_format({
        "font_name": "Calibri",
        "font_size": 8,
        "font_color": "#000000",
    })

    # ------------------------------------------------------------------
    # ESTRUTURA DO ARQUIVO ORIGINAL
    # ------------------------------------------------------------------
    # A é praticamente invisível no original; B:AF têm largura 5,75.
    worksheet.set_column(0, 0, 0.13, None, {"hidden": True})
    worksheet.set_column(primeira_coluna, ultima_coluna, 5.75)

    # Título original ocupa I1:X4.
    worksheet.merge_range(
        0,
        8,
        3,
        23,
        "Tabela de registro de presença de funcionários",
        formato_titulo,
    )

    # Os metadados ficam à direita, começando em Z3/Z4 no original.
    coluna_meta = min(25, ultima_coluna)
    worksheet.write(
        2,
        coluna_meta,
        (
            "Data de presença:"
            f"{inicio_periodo.strftime('%Y-%m-%d')}~"
            f"{fim_periodo.strftime('%Y-%m-%d')}"
        ),
        formato_meta,
    )
    worksheet.write(
        3,
        coluna_meta,
        "Data de apresentação:" + datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        formato_meta,
    )

    # Cada funcionário ocupa exatamente três linhas, como no relatório:
    # informação / dias / horários.
    linha = 4  # linha 5 no Excel

    for funcionario in funcionarios_ativos:
        # Primeiro aplica a borda azul contínua por toda a linha de informação.
        for coluna in range(primeira_coluna, ultima_coluna + 1):
            worksheet.write_blank(
                linha,
                coluna,
                None,
                formato_info_borda,
            )

        # Posições iguais às do arquivo original:
        # B = IDUsuário, D = ID, K = Nome, L = nome, R = Dep., S = departamento.
        worksheet.write(linha, 1, "IDUsuário:", formato_info_esquerda)
        worksheet.write(linha, 3, funcionario["id"], formato_info_esquerda)

        if ultima_coluna >= 10:
            worksheet.write(linha, 10, "Nome:", formato_info_direita)
        if ultima_coluna >= 11:
            worksheet.write(linha, 11, funcionario["nome"], formato_info_esquerda)
        if ultima_coluna >= 17:
            worksheet.write(linha, 17, "Dep.:", formato_info_direita)
        if ultima_coluna >= 18:
            worksheet.write(linha, 18, departamento, formato_info_esquerda)

        linha_dias = linha + 1
        linha_horarios = linha + 2

        # Grade completa até AF (ou além, se o período livre exceder 31 dias).
        for deslocamento in range(quantidade_colunas_dias):
            coluna = primeira_coluna + deslocamento

            if deslocamento < len(datas):
                worksheet.write(
                    linha_dias,
                    coluna,
                    datas[deslocamento].day,
                    formato_dia,
                )
            else:
                worksheet.write_blank(
                    linha_dias,
                    coluna,
                    None,
                    formato_dia,
                )

            if deslocamento < len(datas):
                registros = sorted(
                    funcionario["por_dia"].get(datas[deslocamento], []),
                    key=lambda item: item["data_hora"],
                )
            else:
                registros = []

            _escrever_horarios(
                worksheet=worksheet,
                linha=linha_horarios,
                coluna=coluna,
                registros=registros,
                formato_horario=formato_horario,
                formato_horario_manual=formato_horario_manual,
                formato_manual_fonte=formato_manual_fonte,
                formato_original_fonte=formato_original_fonte,
            )

        # O Excel do relatório original deixa a linha de horários ajustar-se
        # ao texto quebrado. Aqui definimos alturas próximas para a impressão
        # ficar estável também em LibreOffice.
        maior_quantidade = max(
            [
                len(funcionario["por_dia"].get(data, []))
                for data in datas
            ]
            or [1]
        )
        worksheet.set_row(linha, 15)
        worksheet.set_row(linha_dias, 15)
        worksheet.set_row(
            linha_horarios,
            15 if maior_quantidade <= 1 else max(30, maior_quantidade * 15),
        )

        linha += 3

    # ------------------------------------------------------------------
    # IMPRESSÃO — mesmas características principais do original.
    # ------------------------------------------------------------------
    worksheet.hide_gridlines(2)
    worksheet.freeze_panes(4, 0)
    worksheet.set_landscape()
    worksheet.set_paper(9)  # A4
    worksheet.fit_to_pages(1, 0)
    worksheet.center_horizontally()
    worksheet.set_margins(left=0, right=0, top=0.1965, bottom=0.1965)
    worksheet.set_header("")
    worksheet.set_footer("")

    if funcionarios_ativos:
        worksheet.print_area(0, 0, linha - 1, ultima_coluna)

    workbook.close()
    saida.seek(0)

    return saida.getvalue(), len(funcionarios_ativos)
