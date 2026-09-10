from collections import defaultdict
from datetime import datetime, time, timedelta

VALOR_ATE_9H = 110
VALOR_ACIMA_9H = 220
LIMITE_HORAS = 9
LIMITE_DUPLICIDADE_MINUTOS = 10

# ==============================================================
# DIA DO PAGAMENTO
# ==============================================================
# Se a empresa mudar o dia do pagamento no futuro, altere apenas
# esta variável. Valores aceitos: segunda, terca, quarta, quinta,
# sexta, sabado e domingo.
DIA_PAGAMENTO = "quinta"

DIAS_SEMANA = {
    "segunda": 0,
    "terca": 1,
    "quarta": 2,
    "quinta": 3,
    "sexta": 4,
    "sabado": 5,
    "domingo": 6,
}

if DIA_PAGAMENTO not in DIAS_SEMANA:
    raise ValueError(
        "DIA_PAGAMENTO inválido. Use: "
        + ", ".join(DIAS_SEMANA)
    )

DIA_PAGAMENTO_NUMERO = DIAS_SEMANA[DIA_PAGAMENTO]
ARTIGO_DIA_PAGAMENTO = (
    "do"
    if DIA_PAGAMENTO in {"sabado", "domingo"}
    else "da"
)
ROTULO_DIA_PAGAMENTO = f"{ARTIGO_DIA_PAGAMENTO} {DIA_PAGAMENTO}"


def remover_duplicidades(marcacoes):

    if not marcacoes:
        return []

    marcacoes = sorted(marcacoes)
    resultado = [marcacoes[0]]

    for marcacao in marcacoes[1:]:

        diferenca = (
            marcacao - resultado[-1]
        ).total_seconds() / 60

        if diferenca >= LIMITE_DUPLICIDADE_MINUTOS:
            resultado.append(marcacao)

    return resultado


def formatar_horas(horas_decimais):

    horas = int(horas_decimais)
    minutos = round((horas_decimais - horas) * 60)

    if minutos == 60:
        horas += 1
        minutos = 0

    return f"{horas:02d}:{minutos:02d}"


def converter_data_hora(data, hora):

    if isinstance(hora, time):

        return datetime.combine(
            datetime.strptime(data, "%Y-%m-%d").date(),
            hora
        )

    hora = str(hora).strip()

    if len(hora) >= 8:
        hora = hora[:5]

    return datetime.strptime(
        f"{data} {hora}",
        "%Y-%m-%d %H:%M"
    )


def calcular_periodo_pagamento(data_referencia):
    """
    Retorna o período padrão do pagamento.

    A referência normalmente é a data final informada no relatório.

    - antes do dia de pagamento: começa no pagamento anterior e vai
      até a própria data de referência;
    - no dia do pagamento: começa no mesmo dia da semana anterior e
      termina na data de referência;
    - depois do dia de pagamento: mantém fechado o período que acabou
      no dia de pagamento daquela semana.

    Exemplo com DIA_PAGAMENTO = quinta:
    - quarta 12/08 -> 06/08 até 12/08
    - quinta 13/08 -> 06/08 até 13/08
    - sábado 15/08 -> 06/08 até 13/08
    """

    if isinstance(data_referencia, datetime):
        data_referencia = data_referencia.date()

    if isinstance(data_referencia, str):
        data_referencia = datetime.strptime(
            data_referencia,
            "%Y-%m-%d"
        ).date()

    dia_semana = data_referencia.weekday()

    if dia_semana < DIA_PAGAMENTO_NUMERO:
        # O dia de pagamento desta semana ainda vai acontecer.
        dia_pagamento_semana = data_referencia + timedelta(
            days=DIA_PAGAMENTO_NUMERO - dia_semana
        )
        inicio = dia_pagamento_semana - timedelta(days=7)
        fim = data_referencia

    elif dia_semana == DIA_PAGAMENTO_NUMERO:
        # Hoje é o dia de pagamento.
        fim = data_referencia
        inicio = fim - timedelta(days=7)

    else:
        # O dia de pagamento desta semana já passou. Mantém o ciclo
        # fechado nele, sem avançar automaticamente para sexta/sábado.
        fim = data_referencia - timedelta(
            days=dia_semana - DIA_PAGAMENTO_NUMERO
        )
        inicio = fim - timedelta(days=7)

    return inicio, fim


def _adicionar_jornada_completa(
    jornadas,
    entrada,
    saida,
    data_inicio_pagamento=None,
    aplicar_ajuste_inicio=False,
):
    horas = (saida - entrada).total_seconds() / 3600

    valor_original = (
        VALOR_ATE_9H
        if horas <= LIMITE_HORAS
        else VALOR_ACIMA_9H
    )

    valor = valor_original
    tipo = (
        "normal"
        if horas <= LIMITE_HORAS
        else "dobrada"
    )

    # Somente a PRIMEIRA data do ciclo de pagamento representa a
    # quinta anterior, cujo R$ 110 já foi pago no próprio dia.
    if (
        aplicar_ajuste_inicio
        and data_inicio_pagamento is not None
        and entrada.date() == data_inicio_pagamento
    ):
        valor = max(
            valor_original - VALOR_ATE_9H,
            0
        )

        if valor_original > VALOR_ATE_9H:
            tipo = "dobrada_complemento_pagamento"
        else:
            tipo = "normal_ja_pago_pagamento"

    jornadas.append({
        "entrada": entrada,
        "saida": saida,
        "horas_decimal": horas,
        "horas": formatar_horas(horas),
        "valor": valor,
        "tipo": tipo
    })


def calcular_jornadas(
    marcacoes,
    data_inicio_pagamento=None,
    data_fim_pagamento=None,
    adiantamento_em_qualquer_dia=False,
):
    """
    Calcula as jornadas e, quando o ciclo de pagamento é informado,
    aplica as regras especiais somente nas bordas desse ciclo.

    Regras do ciclo:
    - no primeiro dia do ciclo (dia de pagamento anterior):
      jornada normal = R$ 0; jornada dobrada = + R$ 110;
    - no modo automático, qualquer dia DENTRO do ciclo com exatamente
      UMA marcação gera um adiantamento de R$ 110;
    - se essa marcação única estiver no último DIA_PAGAMENTO do ciclo,
      ela recebe a identificação específica de adiantamento do pagamento;
    - no Período livre, quando adiantamento_em_qualquer_dia=True,
      qualquer dia com exatamente UMA marcação também gera um
      adiantamento de R$ 110, independentemente do dia da semana;
    - o filtro visual não altera as classificações das jornadas completas.
    """

    marcacoes = remover_duplicidades(marcacoes)

    if not marcacoes:
        return []

    if isinstance(data_inicio_pagamento, datetime):
        data_inicio_pagamento = data_inicio_pagamento.date()

    if isinstance(data_fim_pagamento, datetime):
        data_fim_pagamento = data_fim_pagamento.date()

    jornadas = []
    marcacoes_por_dia = defaultdict(list)

    for marcacao in marcacoes:
        marcacoes_por_dia[marcacao.date()].append(marcacao)

    for data in sorted(marcacoes_por_dia):

        marcacoes_dia = sorted(marcacoes_por_dia[data])

        # Uma única marcação vale R$ 110 como adiantamento nos dois
        # modos. No automático ela precisa estar dentro do ciclo de
        # pagamento; no Período livre pode ser qualquer dia selecionado.
        eh_dia_pagamento = (
            data.weekday() == DIA_PAGAMENTO_NUMERO
        )

        eh_fim_do_ciclo = (
            data_fim_pagamento is not None
            and data == data_fim_pagamento
        )

        dentro_ciclo_pagamento = (
            data_inicio_pagamento is not None
            and data_fim_pagamento is not None
            and data_inicio_pagamento <= data <= data_fim_pagamento
        )

        deve_adiantar_livre = (
            len(marcacoes_dia) == 1
            and adiantamento_em_qualquer_dia
        )

        deve_adiantar_automatico = (
            len(marcacoes_dia) == 1
            and not adiantamento_em_qualquer_dia
            and dentro_ciclo_pagamento
        )

        if deve_adiantar_livre or deve_adiantar_automatico:
            if deve_adiantar_livre:
                tipo_adiantamento = "adiantamento_periodo_livre"
            elif eh_dia_pagamento and eh_fim_do_ciclo:
                tipo_adiantamento = "adiantamento_dia_pagamento"
            else:
                tipo_adiantamento = "adiantamento_marcacao_unica"

            jornadas.append({
                "entrada": marcacoes_dia[0],
                "saida": None,
                "horas_decimal": None,
                "horas": "",
                "valor": VALOR_ATE_9H,
                "tipo": tipo_adiantamento
            })
            continue

        # Jornada é formada dentro do próprio dia. Isso garante que
        # uma sexta-feira com apenas uma marcação não seja pareada com
        # a primeira marcação do sábado seguinte.
        i = 0
        primeira_jornada_do_dia = True

        while i + 1 < len(marcacoes_dia):

            entrada = marcacoes_dia[i]
            saida = marcacoes_dia[i + 1]

            aplicar_ajuste_inicio = (
                primeira_jornada_do_dia
                and data_inicio_pagamento is not None
                and data == data_inicio_pagamento
                and data.weekday() == DIA_PAGAMENTO_NUMERO
            )

            _adicionar_jornada_completa(
                jornadas=jornadas,
                entrada=entrada,
                saida=saida,
                data_inicio_pagamento=data_inicio_pagamento,
                aplicar_ajuste_inicio=aplicar_ajuste_inicio,
            )

            primeira_jornada_do_dia = False
            i += 2

        # Se o dia tiver mais de uma marcação e ainda sobrar uma ao
        # final do pareamento, essa sobra continua sendo ignorada.

    jornadas.sort(
        key=lambda jornada: jornada["entrada"]
    )

    return jornadas


def calcular_pagamentos(
    dados,
    data_inicio_pagamento=None,
    data_fim_pagamento=None,
):

    funcionarios = {}

    # Junta todas as marcações por funcionário
    for dia in dados["dias"].values():

        data = dia["data"]

        for funcionario in dia["funcionarios"]:

            fid = funcionario["id"]

            if fid not in funcionarios:

                funcionarios[fid] = {
                    "id": fid,
                    "nome": funcionario["nome"],
                    "marcacoes": []
                }

            for horario in funcionario["horarios"]:

                funcionarios[fid]["marcacoes"].append(
                    converter_data_hora(data, horario)
                )

    resultado = []

    for funcionario in funcionarios.values():

        funcionario["marcacoes"].sort()

        marcacoes = remover_duplicidades(
            funcionario["marcacoes"]
        )

        jornadas = calcular_jornadas(
            marcacoes,
            data_inicio_pagamento=data_inicio_pagamento,
            data_fim_pagamento=data_fim_pagamento,
        )

        resultado.append({
            "id": funcionario["id"],
            "nome": funcionario["nome"],
            "nome_exibicao": funcionario["nome"].title(),
            "marcacoes": marcacoes,
            "jornadas": jornadas,
            "total": sum(
                j["valor"]
                for j in jornadas
            )
        })

    resultado.sort(
        key=lambda x: x["nome_exibicao"]
    )

    return resultado
