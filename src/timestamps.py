"""Leitura e validacao dos timestamps no formato HH:MM:SS.

Funcao pura: nao toca em disco, rede ou FFmpeg. Manter a regra de tempo
isolada deixa os testes baratos e separa o "quando" do "como cortar".
"""

import re

TIMESTAMP_PATTERN = re.compile(r"^(\d{2}):(\d{2}):(\d{2})$")

SECONDS_PER_MINUTE = 60
SECONDS_PER_HOUR = 3600
MAX_PART_VALUE = 59
TIMESTAMP_FORMAT_HINT = "HH:MM:SS (ex.: 00:01:20)"


def parse_timestamp(value: str) -> int:
    """Converte 'HH:MM:SS' em segundos.

    Levanta ValueError com mensagem pronta para o usuario quando o texto
    nao segue o formato, ou quando minutos/segundos passam de 59.
    """
    match = TIMESTAMP_PATTERN.match(value)
    if match is None:
        raise ValueError(
            f"timestamp invalido: {value!r}. "
            f"Use o formato {TIMESTAMP_FORMAT_HINT}"
        )

    hours, minutes, seconds = (int(part) for part in match.groups())
    if minutes > MAX_PART_VALUE or seconds > MAX_PART_VALUE:
        raise ValueError(
            f"timestamp invalido: {value!r}. Minutos e segundos devem ser "
            f"menores que {MAX_PART_VALUE + 1}"
        )

    return hours * SECONDS_PER_HOUR + minutes * SECONDS_PER_MINUTE + seconds


def format_timestamp(total_seconds: int) -> str:
    """Converte segundos de volta em 'HH:MM:SS' para entregar ao FFmpeg."""
    hours, rest = divmod(total_seconds, SECONDS_PER_HOUR)
    minutes, seconds = divmod(rest, SECONDS_PER_MINUTE)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def validate_interval(start_seconds: int, end_seconds: int) -> None:
    """Garante que o fim do corte esteja depois do inicio.

    Intervalo vazio (end == start) tambem e recusado: nao produziria video
    algum, apenas um arquivo de saida de 0 byte que parece sucesso.
    """
    if end_seconds <= start_seconds:
        raise ValueError(
            f"--end ({format_timestamp(end_seconds)}) deve ser maior que "
            f"--start ({format_timestamp(start_seconds)})"
        )
