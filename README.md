# CIAOGbs

> Ferramenta própria para produção automatizada de conteúdo vertical
> para **Instagram Reels** e **TikTok**.

---

## 1. Nome do projeto

**CIAOGbs**

O nome proposital não carrega significado técnico dentro do código. Nos
arquivos e módulos, use nomes genéricos e descritivos (`src/` com módulos
curtos e úteis), e não prefixos do nome do projeto.

---

## 2. Objetivo do projeto

Construir, de forma incremental, uma ferramenta que:

1. receba vídeos;
2. processe-os com **FFmpeg**;
3. gere vídeos verticais (9:16) para Reels e TikTok;
4. transcreva o áudio;
5. use IA para identificar os melhores trechos;
6. gere cortes automáticos;
7. adicione legendas;
8. mais adiante, analise métricas e auxilie na produção de conteúdo.

### Princípio de desenvolvimento

O projeto cresce **por fases**. Cada fase entrega algo funcionando e
verificável antes de a próxima começar. Nada é construído "por antecipação".

Estado atual: **Fases 0 e 1 concluídas** (fundação do repositório e primeiro
corte vertical).

---

## 3. Visão geral da arquitetura

O pipeline completo, em termos de responsabilidade de cada etapa:

```
   input/
     |
     |  1. leitura do vídeo de origem
     v
   [ Leitura ]  -- valida formato, codec e duração
     |
     |  2. corte no intervalo de timestamps
     v
   [ Corte ]  -- FFmpeg extrai o trecho
     |
     |  3. transcrição do áudio do trecho
     v
   [ Transcrição ]  -- texto com marcação de tempo
     |
     |  4. avaliação com IA
     v
   [ IA ]  -- ranqueia os melhores momentos
     |
     |  5. conversão para 9:16
     v
   [ Verticalização ]  -- recorte/escala para 1080x1920
     |
     |  6. geração de legendas
     v
   [ Legendas ]  -- estilo configurável por plataforma
     |
     v
   output/   (temp/ guarda os arquivos intermediários)
```

As etapas **[ Corte ]** e **[ Verticalização ]** já existem, unidas em um só
comando na Fase 1. As demais são a **direção** do projeto, não a implementação
atual.

### Decisões de arquitetura já tomadas

| Decisão | Motivo |
|---|---|
| Código em `src/`, dados em `input/`/`output/`/`temp/` | Separar código de artefato. O que é versionado é só o que se escreve à mão. |
| Sem `pyproject.toml` | Não há nada a instalar: o projeto é um script, não um pacote distribuível. `src/` é uma pasta simples, sem `__init__.py`, resolvida como *namespace package*. |
| Sem dependências de terceiros até a Fase 1 | Nenhum código importa nada de fora. `requirements.txt` segue vazio de propósito. |
| `.env` fora do versionamento | Segredos nunca entram no repositório. `.env.example` documenta apenas nomes de variáveis. |
| Pipeline em etapas sequenciais | Cada etapa tem uma única responsabilidade e pode ser testada isolada. Divida-se em código assíncrono ou em múltiplos serviços apenas quando a complexidade for real, e não presumida. |
| Filtro `crop + scale + setsar` | Uma única cadeia de filtros resolve o 9:16 de forma determinística, sem passar por IA. `setsar=1` é o passo que garante proporção real em vez de imagem esticada. |
| `subprocess` com lista de argumentos | Nome de arquivo com espaço ou caractere especial não vira comando interpretado pelo shell. |

---

## 4. Estrutura de pastas

```
CIAOGbs/
|
|-- input/              # Vídeos de origem. Ignorado pelo Git (só o .gitkeep é versionado).
|-- output/             # Vídeos finais gerados. Ignorado pelo Git.
|-- temp/               # Arquivos intermediários. Ignorado pelo Git. Sem uso na Fase 1.
|-- src/                # Código da aplicação.
|   |-- cut_video.py    # CLI: monta e executa o comando do FFmpeg.
|   `-- timestamps.py   # Leitura e validação dos timestamps HH:MM:SS.
|-- tests/              # Testes automatizados (unittest, sem dependências).
|   |-- test_cut_video.py
|   `-- test_timestamps.py
|
|-- .env.example        # Modelo de variáveis de ambiente. Sem segredos reais.
|-- .gitignore          # Python, mídia, secrets, caches, pastas de trabalho.
|-- AGENTS.md           # Regras de trabalho para agentes de IA neste repositório.
|-- README.md           # Este arquivo.
`-- requirements.txt    # Dependências pip. Vazio de propósito.
```

### Responsabilidade de cada pasta

| Pasta | Quem escreve | Quem lê | Observação |
|---|---|---|---|
| `input/` | você | `src/` | Coloque o vídeo aqui. Nada vai para o repositório. |
| `temp/` | — | — | Reservada para fases futuras. A Fase 1 não usa: o FFmpeg escreve direto em `output/`. |
| `output/` | `src/` | você | Resultado final. Quase nunca deve ser sobrescrito. |
| `src/` | você | você | Único lugar com código Python. |
| `tests/` | você | você | Um arquivo de teste por módulo de `src/`. |

### Observação sobre `src/`

`src/` é uma pasta comum, **sem `__init__.py`**. O Python 3 a resolve como
*namespace package*, então `py -m src.cut_video` e `from src.cut_video import ...`
funcionam normalmente. Os comandos precisam ser executados **a partir da raiz do
projeto**, porque é de lá que `src` entra no caminho de importação.

---

## 5. Pré-requisitos

| Ferramenta | Versão verificada | Status |
|---|---|---|
| Python | 3.14.6 | instalado |
| Git | 2.53.0.windows.2 | instalado |
| FFmpeg | 9.0.2 (essentials build) | instalado |
| FFprobe | 9.0.2 (essentials build) | instalado |

### Usar `py` e não `python`

Nesta máquina o comando `python` aponta para o alias da Microsoft Store e
falha. O launcher `py` funciona normalmente. Por isso **todos** os comandos
deste README usam `py`:

```powershell
py --version
py -m pip --version
```

### FFmpeg

FFmpeg e FFprobe são **binários externos**, não dependências pip: não entram
no `requirements.txt` e não são instalados por ele. Ambos são obrigatórios a
partir da Fase 1.

Instalados em `C:\ffmpeg-9.0.2-essentials_build\bin`, que está no PATH do
usuário. Se o `ffmpeg -version` falhar, o terminal foi aberto antes da
instalação: abra um terminal novo.

---

## 6. Configuração do ambiente

### 6.1 Criar o ambiente virtual

```powershell
py -m venv .venv
```

O `.venv` já está no `.gitignore`.

### 6.2 Ativar o ambiente virtual

**PowerShell:**

```powershell
.\.venv\Scripts\Activate.ps1
```

> Se o PowerShell bloquear a execução do script, rode uma vez só:
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

**CMD:**

```cmd
.venv\Scripts\activate.bat
```

Desativar ao terminar:

```powershell
deactivate
```

### 6.3 Instalar dependências

Hoje **não há nada a instalar** (Fase 0). O comando fica registrado aqui para
as próximas fases:

```powershell
py -m pip install -r requirements.txt
```

### 6.4 Configurar o `.env` (necessário a partir da Fase 1)

```powershell
Copy-Item .env.example .env
```

Depois edite o `.env` com os valores reais. O `.env` já está ignorado pelo Git.
**Nunca** coloque chaves reais no `.env.example` nem no código.

---

## 7. Como verificar que a estrutura está funcionando

Nenhum comando abaixo instala nem altera nada. Rode na raiz do projeto:

```powershell
# 1. Ferramentas
py --version
ffmpeg -version
ffprobe -version

# 2. Estrutura de pastas
Get-ChildItem -Force -Recurse

# 3. Git inicializado e regras de ignore corretas
git status
git status --ignored=matching --porcelain -uall
```

Interpretação do resultado esperado em `git status --ignored`:

- `??` = arquivo **será versionado** (`.gitignore`, `README.md`, `AGENTS.md`,
  `.env.example`, `requirements.txt` e os `.gitkeep`).
- `!!` = arquivo **ignorado** (`.env`, arquivos de mídia).

Se algum `.gitkeep` aparecer como `!!`, o `.gitignore` precisa de ajuste.

---

## 8. Fase 1 — Primeiro corte vertical

### Objetivo

Receber um vídeo, um horário inicial e um horário final, e gerar um **corte
vertical 9:16 em 1080x1920**, com o áudio preservado e o arquivo de origem
intocado. É o primeiro componente funcional do CIAOGbs.

### Como usar

**1. Coloque um vídeo em `input/`.** O nome pode ser qualquer um; ele será a
base do nome do arquivo gerado.

```
input/
`-- video.mp4
```

**2. Rode o comando a partir da raiz do projeto:**

```powershell
py -m src.cut_video --input input\video.mp4 --start 00:01:20 --end 00:02:05
```

| Argumento | Obrigatório | Exemplo | Significado |
|---|---|---|---|
| `--input` | sim | `input\video.mp4` | Vídeo de origem |
| `--start` | sim | `00:01:20` | Início do corte, em `HH:MM:SS` |
| `--end` | sim | `00:02:05` | Fim do corte, em `HH:MM:SS` |
| `--output` | não | `output\meu_corte.mp4` | Nome do arquivo gerado |

Sobre o formato do horário: é obrigatório `HH:MM:SS`, com duas dígitos em cada
parte. `00:01:20` e `01:59:59` são válidos; `80` e `01:70:00` são recusados com
mensagem explicativa.

**3. Pegue o resultado em `output/`.**

```
output/
`-- video_corte_001.mp4
```

A numeração é automática e nunca sobrescreve: `video.mp4` gera
`video_corte_001.mp4`, depois `video_corte_002.mp4`, e assim por diante.

O caminho absoluto e o tamanho do arquivo são impressos ao final, e o código
de saída é `0` quando deu certo, `1` quando deu errado.

### Como o enquadramento funciona

O vídeo horizontal é transformado em 9:16 por esta cadeia de filtros:

```
-vf "crop=ih*9/16:ih,scale=1080:1920,setsar=1"
```

| Parte | O que faz |
|---|---|
| `crop=ih*9/16:ih` | A largura do recorte é calculada a partir da **altura** de entrada (`ih`), o que já garante proporção 9:16. O corte é **centralizado** por padrão no FFmpeg. |
| `scale=1080:1920` | Amplia a faixa cortada até a resolução de entrega. |
| `setsar=1` | Zera o *sample aspect ratio*. Sem isso, o arquivo teria proporção exibida errada, aparecendo esticado. |

Como a largura vem da altura, a mesma fórmula serve para fonte horizontal
(1920x1080 → recorta 608x1080) e para fonte já vertical (1080x1920 → não
perde nada).

### O que o resultado garante

| Propriedade | Valor | Como é definida |
|---|---|---|
| Resolução | 1080x1920 | `scale=1080:1920` |
| Proporção | 9:16 | `crop=ih*9/16:ih` + `setsar=1` |
| Vídeo | H.264 (`libx264`) | `-c:v libx264`, CRF 20 |
| Áudio | AAC 128 kbps | `-c:a aac -b:a 128k` |
| Formato de pixel | `yuv420p` | `-pix_fmt yuv420p` |
| Reprodução web | índice no início do arquivo | `-movflags +faststart` |
| Duração | exatamente `end - start` | `-t` |

### Limitações atuais

- **O enquadramento é central e fixo.** Num vídeo 16:9, o crop descarta cerca
  de 68% da largura, e só o miolo do quadro sobrevive. Se o assunto estiver
  nas laterais, sai cortado. Não há detecção de rosto nem escolha de
  enquadramento — isso é Fase futura.
- **A seleção de bons momentos não existe.** Você informa o início e o fim na
  mão. O CIAOGbs ainda não analisa o vídeo para sugerir trechos, nem
  transcrição, nem IA de qualquer tipo.
- **Não há legendas**, nem IA, nem publicação em redes sociais.
- **Um corte por execução.** Não há modo em lote.
- **Reels e TikTok usam o mesmo preset.** Não há ajuste por plataforma.
- **`temp/` não é usada.** O FFmpeg escreve direto em `output/`.
- **O FPS final é o da origem.** O comando não força `-r`.
- **A validação de duração é única por arquivo.** Rodar várias vezes lê a
  duração de novo a cada vez.

### Testes

Os testes usam apenas `unittest`, da biblioteca padrão, e **não** executam o
FFmpeg de verdade — verificam a parsing dos horários, as validações e a lista
exata de argumentos enviada ao FFmpeg.

```powershell
py -m unittest discover -s tests -v
```

Para conferir o resultado de um corte real com um vídeo verdadeiro:

```powershell
ffprobe -v error -show_entries stream=codec_type,width,height,display_aspect_ratio `
  -of default=noprint_wrappers=0 output\video_corte_001.mp4
```

Esperado: `h264`, `width=1080`, `height=1920`, `display_aspect_ratio=9:16`,
e uma segunda entrada `codec_type=audio`.

---

## 9. Roadmap

| Fase | Escopo | Estado |
|---|---|---|
| Fase 0 | Fundação: pastas, `.gitignore`, `.env.example`, `requirements.txt`, documentação | **concluída** |
| Fase 1 | Primeiro processamento de vídeo com FFmpeg: receber vídeo + timestamps e gerar vídeo vertical 9:16 | **concluída** |
| Fase 2 | Transcrição do áudio | planejada |
| Fase 3 | IA para identificar bons trechos | planejada |
| Fase 4 | Geração automática de cortes | planejada |
| Fase 5 | Legendas automáticas | planejada |
| Fase 6 | Ajuste de formato para Reels e TikTok | planejada |
| Fase 7 | Análise de métricas | planejada |

**Nenhuma fase acima da Fase 1 deve ser implementada sem solicitação explícita
do usuário.** Ver `AGENTS.md`.

---

## 10. Problemas conhecidos nesta fase

1. **`python` não funciona, use `py`.** Resolvido por convenção de documentação.
2. **O FFmpeg encerra com código 0 mesmo quando não gera vídeo nenhum.** Ele
   acontece quando o trecho pedido começa depois do fim do arquivo. Por isso o
   CIAOGbs não confia só no código de saída: ele lê a duração do vídeo antes
   de cortar, e confere se o arquivo gerado tem stream de vídeo depois. Nos
   dois casos o arquivo parcial é apagado e o comando sai com código 1.
3. **`FFMPEG_PATH` e `TARGET_*` no `.env.example` não são lidas.** São
   placeholders para quando existir configuração externa. A Fase 1 usa valores
   fixos em `src/cut_video.py`.
4. **Python 3.14 é muito recente.** Bibliotecas de transcrição/áudio
   (Whisper, PyTorch, MoviePy) podem não ter wheels para 3.14. Se isso
   acontecer na fase correspondente, pode ser necessário fixar uma versão do
   Python. **Não é ação da Fase 1.**

---

## 11. Como contribuir

Leia o `AGENTS.md` antes de alterar qualquer coisa. Em resumo:

- uma fase por vez, com aprovação;
- sem dependências sem justificativa;
- sem segredos no código;
- `git push` somente com autorização explícita.
