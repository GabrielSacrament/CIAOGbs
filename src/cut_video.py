"""Gera um corte vertical 9:16 (1080x1920) a partir de um trecho de video.

Fase 1 do CIAOGbs. O unico caminho do codigo e a linha de comando:

    py -m src.cut_video --input input/video.mp4 --start 00:01:20 --end 00:02:05

O video de entrada nunca e alterado: o FFmpeg so le dele.
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

from .timestamps import format_timestamp, parse_timestamp, validate_interval

# As pastas sao resolvidas a partir deste arquivo, e nao do diretorio atual,
# para que o comando funcione de onde o usuario estiver.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "output"

FFMPEG_EXECUTABLE = "ffmpeg"
FFPROBE_EXECUTABLE = "ffprobe"
FFMPEG_MISSING_HINT = (
    "Instale com 'winget install Gyan.FFmpeg' ou baixe em ffmpeg.org, "
    "depois reinicie o terminal para atualizar o PATH."
)

OUTPUT_WIDTH = 1080
OUTPUT_HEIGHT = 1920
VIDEO_CODEC = "libx264"
VIDEO_PRESET = "medium"
VIDEO_CRF = "20"
AUDIO_CODEC = "aac"
AUDIO_BITRATE = "128k"
PIXEL_FORMAT = "yuv420p"

OUTPUT_NAME_PATTERN = "{stem}_corte_{index:03d}.mp4"
ERROR_LINES_SHOWN = 15
STREAM_INDEX_CSV = "csv=p=0"


def vertical_filter() -> str:
    """Monta o filtro que torna o video vertical 9:16.

    crop=ih*9/16:ih  -> a largura do recorte vem da altura (ih), o que ja
                       garante proporcao 9:16. O crop e centralizado por
                       padrao no FFmpeg, entao o centro do quadro e mantido.
    scale=1080:1920  -> leva a faixa cortada ate a resolucao de entrega.
    setsar=1         -> zera o aspect ratio do pixel; sem isso o arquivo
                       sairia esticado em vez de 9:16 de verdade.
    """
    return (
        f"crop=ih*9/16:ih,"
        f"scale={OUTPUT_WIDTH}:{OUTPUT_HEIGHT},"
        "setsar=1"
    )


def find_ffmpeg() -> str:
    """Devolve o caminho do executavel do FFmpeg, ou falha com dica util."""
    executable = shutil.which(FFMPEG_EXECUTABLE)
    if executable is None:
        raise RuntimeError(
            f"FFmpeg nao encontrado no PATH. {FFMPEG_MISSING_HINT}"
        )
    return executable


def find_ffprobe() -> str:
    """Devolve o caminho do executavel do FFprobe, ou falha com dica util.

    O FFprobe vem junto com o FFmpeg, entao nao e uma dependencia nova.
    """
    executable = shutil.which(FFPROBE_EXECUTABLE)
    if executable is None:
        raise RuntimeError(
            f"FFprobe nao encontrado no PATH. {FFMPEG_MISSING_HINT}"
        )
    return executable


def read_duration_seconds(ffprobe_path: str, media_path: Path) -> float:
    """Le a duracao de um arquivo de midia, em segundos."""
    command = [
        ffprobe_path,
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(media_path),
    ]
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        raise ValueError(
            f"nao foi possivel ler a duracao de {media_path}. "
            f"O arquivo e um video valido?"
        )
    try:
        return float(result.stdout.strip())
    except ValueError:
        raise ValueError(
            f"nao foi possivel ler a duracao de {media_path}. "
            f"O arquivo e um video valido?"
        ) from None


def has_video_stream(ffprobe_path: str, media_path: Path) -> bool:
    """Diz se o arquivo possui pelo menos um stream de video.

    O FFmpeg encerra com codigo 0 mesmo quando o trecho pedido esta fora
    da duracao do arquivo: nesse caso ele escreve um container sem nenhum
    stream. Conferir aqui evita anunciar um corte que nao existe.
    """
    command = [
        ffprobe_path,
        "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=index",
        "-of", STREAM_INDEX_CSV,
        str(media_path),
    ]
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return result.returncode == 0 and result.stdout.strip() != ""


def validate_input_file(input_path: Path) -> None:
    """Falha com mensagem clara se a entrada nao existir ou nao for arquivo."""
    if not input_path.exists():
        raise ValueError(f"arquivo de entrada nao encontrado: {input_path}")
    if not input_path.is_file():
        raise ValueError(f"o caminho de entrada nao e um arquivo: {input_path}")


def resolve_output_path(
    input_path: Path,
    output_dir: Path,
    requested_output: Path | None,
) -> Path:
    """Escolhe o arquivo de saida, contando ate achar um numero livre.

    Sem --output, video.mp4 vira video_corte_001.mp4, depois
    video_corte_002.mp4, e assim por diante, sem sobrescrever nada.
    """
    if requested_output is not None:
        if requested_output.exists():
            raise ValueError(f"arquivo de saida ja existe: {requested_output}")
        return requested_output

    index = 1
    while True:
        candidate = output_dir / OUTPUT_NAME_PATTERN.format(
            stem=input_path.stem, index=index
        )
        if not candidate.exists():
            return candidate
        index += 1


def build_ffmpeg_command(
    ffmpeg_path: str,
    input_path: Path,
    start: int,
    end: int,
    output_path: Path,
) -> list[str]:
    """Monta a lista de argumentos do FFmpeg.

    Fica separada e sem efeito colateral para que os testes consigam
    conferir a lista exata sem precisar executar o FFmpeg.

    -ss antes de -i  -> busca rapida no arquivo, e precisa no FFmpeg atual.
    -t               -> duracao (end - start). Evita a confusao de -to,
                        que contaria o tempo a partir do inicio do arquivo.
    -n               -> proibe sobrescrita, por seguranca.
    """
    duration_seconds = end - start
    return [
        ffmpeg_path,
        "-hide_banner",
        "-loglevel", "error",
        "-n",
        "-ss", format_timestamp(start),
        "-i", str(input_path),
        "-t", format_timestamp(duration_seconds),
        "-vf", vertical_filter(),
        "-c:v", VIDEO_CODEC,
        "-preset", VIDEO_PRESET,
        "-crf", VIDEO_CRF,
        "-pix_fmt", PIXEL_FORMAT,
        "-c:a", AUDIO_CODEC,
        "-b:a", AUDIO_BITRATE,
        "-movflags", "+faststart",
        str(output_path),
    ]


def run_ffmpeg(command: list[str]) -> None:
    """Executa o FFmpeg e traduz a falha em RuntimeError legivel.

    A lista de argumentos vai direto ao executavel, sem shell: nome de
    arquivo com espaco ou caractere especial nao vira comando injetado.
    """
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode == 0:
        return

    details = "\n".join(
        result.stderr.strip().splitlines()[-ERROR_LINES_SHOWN:]
    )
    raise RuntimeError(
        f"FFmpeg falhou (codigo {result.returncode}):\n{details}"
    )


def validate_interval_within_duration(
    duration_seconds: float,
    start: int,
    end: int,
) -> None:
    """Recusa um --end que passe do fim do video de origem."""
    if end > duration_seconds:
        raise ValueError(
            f"--end ({format_timestamp(end)}) passa do fim do video, que "
            f"dura apenas {format_timestamp(int(duration_seconds))}"
        )


def cut(
    input_path: Path,
    start: int,
    end: int,
    output_dir: Path,
    requested_output: Path | None = None,
) -> Path:
    """Executa o fluxo completo e devolve o caminho do arquivo gerado."""
    validate_interval(start, end)
    validate_input_file(input_path)

    ffmpeg_path = find_ffmpeg()
    ffprobe_path = find_ffprobe()

    duration_seconds = read_duration_seconds(ffprobe_path, input_path)
    validate_interval_within_duration(duration_seconds, start, end)

    output_path = resolve_output_path(input_path, output_dir, requested_output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    command = build_ffmpeg_command(ffmpeg_path, input_path, start, end, output_path)
    try:
        run_ffmpeg(command)
        if not has_video_stream(ffprobe_path, output_path):
            raise RuntimeError(
                f"o FFmpeg terminou sem erro, mas o arquivo gerado nao tem "
                f"nenhum stream de video. Verifique se o trecho "
                f"{format_timestamp(start)}-{format_timestamp(end)} existe "
                f"dentro do video."
            )
    except RuntimeError:
        # O FFmpeg pode ter criado um arquivo parcial antes de abortar.
        # Apagar evita que um corte pela metade pareca um corte valido.
        output_path.unlink(missing_ok=True)
        raise

    return output_path


def build_parser() -> argparse.ArgumentParser:
    """Monta o interpretador dos argumentos de linha de comando."""
    parser = argparse.ArgumentParser(
        prog="py -m src.cut_video",
        description=(
            "Gera um corte vertical 9:16 (1080x1920) de um trecho de video."
        ),
    )
    parser.add_argument(
        "--input", required=True, type=Path,
        help="caminho do video de origem (ex.: input/video.mp4)",
    )
    parser.add_argument(
        "--start", required=True,
        help="inicio do corte em HH:MM:SS (ex.: 00:01:20)",
    )
    parser.add_argument(
        "--end", required=True,
        help="fim do corte em HH:MM:SS (ex.: 00:02:05)",
    )
    parser.add_argument(
        "--output", type=Path, default=None,
        help="caminho do arquivo gerado (opcional; padrao: output/<nome>_corte_NNN.mp4)",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()

    try:
        start = parse_timestamp(args.start)
        end = parse_timestamp(args.end)
        output_path = cut(
            input_path=args.input,
            start=start,
            end=end,
            output_dir=DEFAULT_OUTPUT_DIR,
            requested_output=args.output,
        )
    except (ValueError, RuntimeError) as error:
        print(f"Erro: {error}", file=sys.stderr)
        return 1

    size_kb = output_path.stat().st_size / 1024
    print(f"Corte gerado: {output_path} ({size_kb:.1f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
