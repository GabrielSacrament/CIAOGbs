"""Testes da leitura e validacao de timestamps (src/timestamps.py)."""

import unittest

from src.timestamps import format_timestamp, parse_timestamp, validate_interval


class ParseTimestampTest(unittest.TestCase):
    def test_aceita_hora_minuto_segundo(self):
        self.assertEqual(parse_timestamp("00:01:20"), 80)

    def test_aceita_valor_maximo(self):
        self.assertEqual(parse_timestamp("01:59:59"), 7199)

    def test_aceita_todo_zerado(self):
        self.assertEqual(parse_timestamp("00:00:00"), 0)

    def test_recusa_hora_com_tres_digitos(self):
        with self.assertRaises(ValueError):
            parse_timestamp("100:00:00")

    def test_recusa_segundos_crus(self):
        with self.assertRaises(ValueError):
            parse_timestamp("80")

    def test_recusa_minutos_acima_de_59(self):
        with self.assertRaises(ValueError):
            parse_timestamp("01:70:00")

    def test_recusa_segundos_acima_de_59(self):
        with self.assertRaises(ValueError):
            parse_timestamp("00:01:99")

    def test_recusa_texto_qualquer(self):
        with self.assertRaises(ValueError):
            parse_timestamp("abc")

    def test_recusa_formato_invertido(self):
        with self.assertRaises(ValueError):
            parse_timestamp("01:20")

    def test_mensagem_de_erro_informa_o_formato_esperado(self):
        with self.assertRaises(ValueError) as contexto:
            parse_timestamp("80")
        self.assertIn("HH:MM:SS", str(contexto.exception))


class FormatTimestampTest(unittest.TestCase):
    def test_formata_segundos_em_horas_minutos_segundos(self):
        self.assertEqual(format_timestamp(80), "00:01:20")

    def test_formata_valor_zerado(self):
        self.assertEqual(format_timestamp(0), "00:00:00")

    def test_ida_e_volta_preserva_o_valor(self):
        self.assertEqual(format_timestamp(parse_timestamp("01:30:45")), "01:30:45")


class ValidateIntervalTest(unittest.TestCase):
    def test_aceita_fim_depois_do_inicio(self):
        self.assertIsNone(validate_interval(80, 125))

    def test_recusa_fim_igual_ao_inicio(self):
        with self.assertRaises(ValueError):
            validate_interval(80, 80)

    def test_recusa_fim_antes_do_inicio(self):
        with self.assertRaises(ValueError):
            validate_interval(125, 80)

    def test_mensagem_de_erro_mostra_os_dois_lados(self):
        with self.assertRaises(ValueError) as contexto:
            validate_interval(125, 80)
        mensagem = str(contexto.exception)
        self.assertIn("00:02:05", mensagem)
        self.assertIn("00:01:20", mensagem)
