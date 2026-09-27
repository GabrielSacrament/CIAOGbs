"""Testes do comando FFmpeg e da validacao de entrada (src/cut_video.py).

Nenhum teste aqui executa o FFmpeg de verdade. A validacao com um video
real fica por conta do teste manual descrito no README.
"""

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from src.cut_video import (
    build_ffmpeg_command,
    has_video_stream,
    read_duration_seconds,
    resolve_output_path,
    validate_input_file,
    validate_interval_within_duration,
    vertical_filter,
)


def build_command_de_exemplo() -> list[str]:
    return build_ffmpeg_command(
        ffmpeg_path="ffmpeg",
        input_path=Path("input/video.mp4"),
        start=80,
        end=125,
        output_path=Path("output/video_corte_001.mp4"),
    )


class VerticalFilterTest(unittest.TestCase):
    def test_filtro_tem_crop_scale_e_setsar(self):
        filtro = vertical_filter()
        self.assertIn("crop=ih*9/16:ih", filtro)
        self.assertIn("scale=1080:1920", filtro)
        self.assertIn("setsar=1", filtro)

    def test_filtro_usa_a_ordem_crop_depois_scale(self):
        filtro = vertical_filter()
        self.assertLess(filtro.index("crop="), filtro.index("scale="))


class BuildFfmpegCommandTest(unittest.TestCase):
    def setUp(self):
        self.command = build_command_de_exemplo()

    def valor_de(self, flag: str) -> str:
        return self.command[self.command.index(flag) + 1]

    def test_entrada_usa_o_inicio_formatado(self):
        self.assertEqual(self.valor_de("-ss"), "00:01:20")

    def test_busca_ocorre_antes_do_arquivo_de_entrada(self):
        indice_entrada = self.command.index("-i")
        self.assertEqual(self.command[indice_entrada - 1], "00:01:20")

    def test_usa_duracao_calculada_e_nao_horario_absoluto(self):
        self.assertEqual(self.valor_de("-t"), "00:00:45")

    def test_filtro_vertical_e_o_filtro_de_video(self):
        self.assertEqual(self.valor_de("-vf"), vertical_filter())

    def test_codigos_de_video_e_audio(self):
        self.assertEqual(self.valor_de("-c:v"), "libx264")
        self.assertEqual(self.valor_de("-c:a"), "aac")

    def test_formato_de_pixel_compativel_com_celular(self):
        self.assertEqual(self.valor_de("-pix_fmt"), "yuv420p")

    def test_indice_do_arquivo_no_comeco_do_video(self):
        self.assertEqual(self.valor_de("-movflags"), "+faststart")

    def test_ultimo_argumento_e_o_arquivo_de_saida(self):
        esperado = str(Path("output/video_corte_001.mp4"))
        self.assertEqual(self.command[-1], esperado)

    def test_argumentos_vem_em_lista_sem_shell(self):
        self.assertIsInstance(self.command, list)
        self.assertTrue(all(isinstance(arg, str) for arg in self.command))

    def test_proibe_sobrescrever(self):
        self.assertIn("-n", self.command)
        self.assertNotIn("-y", self.command)

    def test_arquivo_de_entrada_aparece_como_argumento_do_i(self):
        # No Windows o Path usa barra invertida, e o FFmpeg aceita as duas.
        esperado = str(Path("input/video.mp4"))
        self.assertEqual(self.valor_de("-i"), esperado)


class ValidateInputFileTest(unittest.TestCase):
    def test_recusa_arquivo_inexistente(self):
        with self.assertRaises(ValueError):
            validate_input_file(Path("input/nao_existe.mp4"))

    def test_mensagem_de_erro_mostra_o_caminho(self):
        with self.assertRaises(ValueError) as contexto:
            validate_input_file(Path("input/nao_existe.mp4"))
        self.assertIn("nao_existe.mp4", str(contexto.exception))

    def test_aceita_arquivo_existente(self):
        with tempfile.TemporaryDirectory() as pasta:
            video = Path(pasta) / "video.mp4"
            video.write_bytes(b"conteudo ficticio")
            self.assertIsNone(validate_input_file(video))

    def test_recusa_diretorio_no_lugar_do_video(self):
        with tempfile.TemporaryDirectory() as pasta:
            with self.assertRaises(ValueError):
                validate_input_file(Path(pasta))


class ResolveOutputPathTest(unittest.TestCase):
    def test_primeira_saida_comeca_em_001(self):
        with tempfile.TemporaryDirectory() as pasta:
            saida = resolve_output_path(Path("input/video.mp4"), Path(pasta), None)
            self.assertEqual(saida.name, "video_corte_001.mp4")

    def test_incrementa_quando_o_numero_ja_esta_ocupado(self):
        with tempfile.TemporaryDirectory() as pasta:
            (Path(pasta) / "video_corte_001.mp4").write_bytes(b"x")
            saida = resolve_output_path(Path("input/video.mp4"), Path(pasta), None)
            self.assertEqual(saida.name, "video_corte_002.mp4")

    def test_pula_numeracao_com_varios_ocupados(self):
        with tempfile.TemporaryDirectory() as pasta:
            for indice in (1, 2, 3):
                (Path(pasta) / f"video_corte_{indice:03d}.mp4").write_bytes(b"x")
            saida = resolve_output_path(Path("input/video.mp4"), Path(pasta), None)
            self.assertEqual(saida.name, "video_corte_004.mp4")

    def test_respeita_saida_informada_pelo_usuario(self):
        with tempfile.TemporaryDirectory() as pasta:
            alvo = Path(pasta) / "meu_corte.mp4"
            saida = resolve_output_path(Path("input/video.mp4"), Path(pasta), alvo)
            self.assertEqual(saida, alvo)

    def test_recusa_saida_informada_que_ja_existe(self):
        with tempfile.TemporaryDirectory() as pasta:
            alvo = Path(pasta) / "meu_corte.mp4"
            alvo.write_bytes(b"x")
            with self.assertRaises(ValueError):
                resolve_output_path(Path("input/video.mp4"), Path(pasta), alvo)


class ValidateIntervalWithinDurationTest(unittest.TestCase):
    def test_aceita_trecho_dentro_da_duracao(self):
        self.assertIsNone(validate_interval_within_duration(150.0, 80, 125))

    def test_aceita_trecho_ate_o_final_exato(self):
        self.assertIsNone(validate_interval_within_duration(125.0, 80, 125))

    def test_recusa_fim_alem_da_duracao(self):
        with self.assertRaises(ValueError):
            validate_interval_within_duration(150.0, 80, 300)

    def test_mensagem_diz_quanto_o_video_dura(self):
        with self.assertRaises(ValueError) as contexto:
            validate_interval_within_duration(150.0, 80, 300)
        mensagem = str(contexto.exception)
        self.assertIn("00:02:30", mensagem)
        self.assertIn("00:05:00", mensagem)


class FakeFfprobe:
    """Cria um executavel que imita o FFprobe, para testar sem midia real.

    No Windows o subprocess passa um .bat direto para o CreateProcess, que
    delega ao cmd. Nao ha mock nem dependencia extra envolvidos.
    """

    def __init__(self, stdout: str = "", returncode: int = 0):
        self.caminho = self._criar(stdout, returncode)

    @staticmethod
    def _criar(stdout: str, returncode: int) -> Path:
        pasta = tempfile.mkdtemp()
        caminho = Path(pasta) / "ffprobe_falso.bat"
        # Precisa escrever no stdout do processo, que e o que as funcoes
        # leem. "type nul" imprime nada, para o caso de saida vazia.
        if stdout:
            producao = f"echo {stdout}"
        else:
            producao = "type nul"
        conteudo = f"@echo off\r\n{producao}\r\nexit /b {returncode}\r\n"
        caminho.write_text(conteudo, encoding="ascii")
        return caminho

    def __enter__(self) -> str:
        return str(self.caminho)

    def __exit__(self, *_excecao) -> None:
        os.remove(self.caminho)
        os.rmdir(self.caminho.parent)


@unittest.skipUnless(os.name == "nt", "usa um .bat para imitar o FFprobe")
class ReadDurationSecondsTest(unittest.TestCase):
    def test_le_a_duracao_em_segundos(self):
        with FakeFfprobe(stdout="150.000000") as ffprobe:
            self.assertEqual(
                read_duration_seconds(ffprobe, Path("input/video.mp4")), 150.0
            )

    def test_recusa_saida_vazia(self):
        with FakeFfprobe(stdout="") as ffprobe:
            with self.assertRaises(ValueError):
                read_duration_seconds(ffprobe, Path("input/video.mp4"))

    def test_recusa_quando_o_ffprobe_falha(self):
        with FakeFfprobe(returncode=1) as ffprobe:
            with self.assertRaises(ValueError):
                read_duration_seconds(ffprobe, Path("input/video.mp4"))


@unittest.skipUnless(os.name == "nt", "usa um .bat para imitar o FFprobe")
class HasVideoStreamTest(unittest.TestCase):
    def test_detecta_stream_presente(self):
        with FakeFfprobe(stdout="0") as ffprobe:
            self.assertTrue(has_video_stream(ffprobe, Path("saida.mp4")))

    def test_detecta_container_sem_stream(self):
        with FakeFfprobe(stdout="") as ffprobe:
            self.assertFalse(has_video_stream(ffprobe, Path("saida.mp4")))

    def test_detecta_quando_o_ffprobe_falha(self):
        with FakeFfprobe(returncode=1) as ffprobe:
            self.assertFalse(has_video_stream(ffprobe, Path("saida.mp4")))
