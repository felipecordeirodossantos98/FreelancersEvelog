from collections import defaultdict
from datetime import datetime, time, timedelta

VALOR_DIARIA = 110.00
HORAS_DIARIA = 8
VALOR_HORA_EXTRA = 13.75
TOLERANCIA_HORA_EXTRA_MINUTOS = 5
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
NOME_DIA_PAGAMENTO = DIA_PAGAMENTO.capitalize()
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




def listar_dias_pagamento_no_periodo(data_inicio, data_fim):
    """
    Lista todos os dias configurados de pagamento que existem dentro
    do período real da planilha.

    O dia da semana usado é definido exclusivamente por DIA_PAGAMENTO.

    Os dias anteriores ao primeiro dia de pagamento são ignorados
    pelo filtro do app, porque não existe na base o ciclo anterior
    necessário para fechá-los.
    """

    if isinstance(data_inicio, datetime):
        data_inicio = data_inicio.date()

    if isinstance(data_fim, datetime):
        data_fim = data_fim.date()

    if isinstance(data_inicio, str):
        data_inicio = datetime.strptime(
            data_inicio,
            "%Y-%m-%d"
        ).date()

    if isinstance(data_fim, str):
        data_fim = datetime.strptime(
            data_fim,
            "%Y-%m-%d"
        ).date()

    if data_fim < data_inicio:
        return []

    deslocamento = (
        DIA_PAGAMENTO_NUMERO - data_inicio.weekday()
    ) % 7

    primeira_data_pagamento = data_inicio + timedelta(
        days=deslocamento
    )

    datas_pagamento = []
    data_atual = primeira_data_pagamento

    while data_atual <= data_fim:
        datas_pagamento.append(data_atual)
        data_atual += timedelta(days=7)

    return datas_pagamento


def listar_ciclos_pagamento_no_periodo(data_inicio, data_fim):
    """
    Monta os ciclos válidos do filtro a partir do DIA_PAGAMENTO.

    Regras:
    - dias anteriores ao primeiro dia de pagamento existente na base
      são ignorados;
    - entre dias de pagamento, o ciclo é sempre um par fixo
      (ex.: quinta -> quinta);
    - se a base terminar depois do último dia de pagamento, o último
      ciclo vai desse dia de pagamento até o último dia real da base.

    Exemplos para DIA_PAGAMENTO = "quinta":
    - base 11/09 -> 14/10:
      17/09->24/09, 24/09->01/10, 01/10->08/10, 08/10->14/10
    - base 27/08 -> 31/08:
      27/08->31/08
    """

    if isinstance(data_inicio, datetime):
        data_inicio = data_inicio.date()

    if isinstance(data_fim, datetime):
        data_fim = data_fim.date()

    if isinstance(data_inicio, str):
        data_inicio = datetime.strptime(
            data_inicio,
            "%Y-%m-%d"
        ).date()

    if isinstance(data_fim, str):
        data_fim = datetime.strptime(
            data_fim,
            "%Y-%m-%d"
        ).date()

    if data_fim < data_inicio:
        return []

    dias_pagamento = listar_dias_pagamento_no_periodo(
        data_inicio,
        data_fim,
    )

    if not dias_pagamento:
        return []

    ciclos = []

    for indice in range(len(dias_pagamento) - 1):
        ciclos.append((
            dias_pagamento[indice],
            dias_pagamento[indice + 1],
        ))

    ultimo_dia_pagamento = dias_pagamento[-1]

    if ultimo_dia_pagamento < data_fim:
        ciclos.append((ultimo_dia_pagamento, data_fim))

    return ciclos


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


def _calcular_horas_extras(horas_trabalhadas):
    """
    Retorna as horas extras inteiras acima de 8h, com tolerância
    de 5 minutos para completar cada hora extra.

    Exemplos:
    - 8h54 -> 0h extra
    - 8h55 -> 1h extra
    - 9h54 -> 1h extra
    - 9h55 -> 2h extras
    """

    minutos_trabalhados = round(horas_trabalhadas * 60)
    minutos_excedentes = minutos_trabalhados - (HORAS_DIARIA * 60)

    if minutos_excedentes <= 0:
        return 0

    return max(
        0,
        (minutos_excedentes + TOLERANCIA_HORA_EXTRA_MINUTOS) // 60
    )

def _adicionar_jornada_completa(
    jornadas,
    entrada,
    saida,
    data_inicio_pagamento=None,
    aplicar_ajuste_inicio=False,
):
    horas = (saida - entrada).total_seconds() / 3600

    horas_extras = _calcular_horas_extras(horas)
    valor_horas_extras = round(
        horas_extras * VALOR_HORA_EXTRA,
        2
    )

    valor_original = round(
        VALOR_DIARIA + valor_horas_extras,
        2
    )

    valor = valor_original
    tipo = (
        "diaria_com_horas_extras"
        if horas_extras > 0
        else "diaria"
    )

    # Somente a PRIMEIRA data do ciclo de pagamento representa o
    # dia de pagamento anterior, cuja diária de R$ 110 já foi paga
    # no próprio dia. No fechamento atual entram apenas as horas
    # extras completas que foram confirmadas depois.
    if (
        aplicar_ajuste_inicio
        and data_inicio_pagamento is not None
        and entrada.date() == data_inicio_pagamento
    ):
        valor = valor_horas_extras

        if horas_extras > 0:
            tipo = "horas_extras_complemento_pagamento"
        else:
            tipo = "diaria_ja_paga_pagamento"

    jornadas.append({
        "entrada": entrada,
        "saida": saida,
        "horas_decimal": horas,
        "horas": formatar_horas(horas),
        "horas_extras": horas_extras,
        "valor_hora_extra": VALOR_HORA_EXTRA,
        "valor_horas_extras": valor_horas_extras,
        "valor_diaria": VALOR_DIARIA,
        "valor": valor,
        "tipo": tipo
    })

def calcular_jornadas(
    marcacoes,
    data_inicio_pagamento=None,
    data_fim_pagamento=None,
):
    """
    Monta uma única jornada por dia usando a PRIMEIRA e a ÚLTIMA
    marcação do dia. Marcações intermediárias continuam visíveis, mas
    não quebram a jornada em vários pares.

    Regras:
    - diária de R$ 110;
    - após 8h, cada hora extra vale R$ 13,75;
    - existe tolerância de 5 minutos para completar a hora extra
      (8h55 já conta 1h extra, 9h55 conta 2h, etc.);
    - no primeiro dia do ciclo, a diária já foi paga e entram somente
      as horas extras confirmadas;
    - no dia final do ciclo, somente a primeira marcação gera o
      adiantamento de R$ 110, mesmo que existam outras marcações;
    - nos demais dias, exatamente uma marcação dentro do ciclo gera
      adiantamento de R$ 110;
    - fora do dia final, duas ou mais marcações no mesmo dia formam
      uma jornada da primeira até a última marcação daquele dia.
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

        dentro_ciclo_pagamento = (
            data_inicio_pagamento is not None
            and data_fim_pagamento is not None
            and data_inicio_pagamento <= data <= data_fim_pagamento
        )

        eh_dia_pagamento = data.weekday() == DIA_PAGAMENTO_NUMERO
        eh_fim_do_ciclo = (
            data_fim_pagamento is not None
            and data == data_fim_pagamento
        )

        # No dia ATUAL de pagamento, a diária é adiantada no momento
        # da primeira marcação. Mesmo que a saída (ou outras marcações) já
        # esteja presente no relatório, ela NÃO entra no pagamento atual.
        # A jornada completa desse dia será apurada no próximo ciclo,
        # quando esta data passar a ser o início do próximo ciclo; nesse momento,
        # entram apenas as horas extras pendentes, pois a diária já foi paga.
        if dentro_ciclo_pagamento and eh_dia_pagamento and eh_fim_do_ciclo:
            jornadas.append({
                "entrada": marcacoes_dia[0],
                "saida": None,
                "horas_decimal": None,
                "horas": "",
                "horas_extras": 0,
                "valor_hora_extra": VALOR_HORA_EXTRA,
                "valor_horas_extras": 0.0,
                "valor_diaria": VALOR_DIARIA,
                "valor": VALOR_DIARIA,
                "tipo": "adiantamento_dia_pagamento"
            })
            continue

        if len(marcacoes_dia) == 1:
            if not dentro_ciclo_pagamento:
                continue

            jornadas.append({
                "entrada": marcacoes_dia[0],
                "saida": None,
                "horas_decimal": None,
                "horas": "",
                "horas_extras": 0,
                "valor_hora_extra": VALOR_HORA_EXTRA,
                "valor_horas_extras": 0.0,
                "valor_diaria": VALOR_DIARIA,
                "valor": VALOR_DIARIA,
                "tipo": "adiantamento_marcacao_unica"
            })
            continue

        # A jornada do dia vai da primeira à última marcação.
        entrada = marcacoes_dia[0]
        saida = marcacoes_dia[-1]

        aplicar_ajuste_inicio = (
            data_inicio_pagamento is not None
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

    jornadas.sort(key=lambda jornada: jornada["entrada"])
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
