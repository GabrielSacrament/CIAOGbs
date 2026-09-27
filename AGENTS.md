# AGENTS.md — Regras de trabalho no CIAOGbs

Este arquivo define como agentes de IA (e pessoas) devem trabalhar neste
repositório. Ele tem precedência sobre instruções genéricas: **as regras
abaixo sempre valem**, mesmo que uma tarefa pareça pedir o contrário.

---

## 1. O projeto é incremental

O CIAOGbs cresce por fases. Cada fase entrega algo funcionando e verificável
antes de a próxima começar. Não existe "sprint", "refatoração trimestral" nem
"deixar pronto para depois".

Fases de referência: `README.md`, seção 9.

---

## 2. Nada de funcionalidades futuras sem solicitação

**Não implemente etapas futuras sem pedido explícito do usuário.**

Concretamente, não implemente, mesmo que pareça "óbvio" ou "um detalhe":

- processamento de vídeo;
- integração com FFmpeg;
- cortes automáticos;
- Whisper ou qualquer transcrição;
- IA de seleção de trechos;
- geração automática de Reels/TikTok;
- legendas automáticas;
- geração de roteiros;
- geração de voz (TTS);
- pesquisa automática de conteúdo;
- publicação em Instagram ou TikTok;
- chamadas a APIs externas;
- banco de dados;
- interface gráfica;
- dashboard;
- sistema de métricas.

`src/` e `tests/` começaram vazias de propósito. Isso não é um lembrete
esquecido: é a decisão aprovada para a Fase 0.

**Alerta explícito ao usuário:** se uma tarefa pedida exigir tocar em
escopo de fase futura, pare e avise antes de escrever código.

---

## 3. Mudanças grandes são analisadas antes

Antes de qualquer alteração estrutural — criar ou remover pastas, trocar o
modelo de execução, introduzir `pyproject.toml`, refatorar módulos, mudar
padrões de nomenclatura — o agente deve:

1. explicar o que pretende fazer;
2. dizer por que é necessário agora;
3. apontar o impacto no restante do projeto;
4. aguardar aprovação.

Se houver mais de uma abordagem razoável, **apresente as opções** e deixe a
escolha com o usuário. Escolha a solução mais simples por conta própria apenas
quando não houver alternativa defensável.

---

## 4. Sem alterações visuais ou arquiteturais desnecessárias

Não mude:

- estrutura de pastas já aprovada;
- formato de arquivos de configuração;
- estilo ou tom da documentação;
- ferramentas de lint/test/format sem pedido;
- organização de imports ou nomes públicos.

Resista a "melhorar" coisas que funcionam. Se algo te incomoda, **pergunte**,
não altere.

---

## 5. Código simples e legível

Preferências do projeto:

- Python com tipagem, nomes explícitos e funções curtas.
- Uma função, uma responsabilidade.
- `pathlib.Path` em vez de concatenação de string para caminhos.
- Sem classe sem necessidade: use função até precisar de estado.
- Sem metaprogramação, sem `*args`/`**kwargs` genéricos, sem decorator próprio.
- Sem constante mágica sem nome: extraia com nome descritivo.

Ordem de escolha: stdlib -> dependência já presente no projeto -> nova
dependência (só com justificativa, ver regra 6).

---

## 6. Dependências: nem uma a mais

**Não instale bibliotecas desnecessárias.** Não adicione dependência para uma
fase futura, "porque talvez precise" ou "porque é comum".

Ao adicionar qualquer dependência:

1. explicar por que ela é necessária **na fase atual**;
2. atualizar `requirements.txt` com a versão fixada;
3. implementar leitura de `.env` no mesmo momento, se for o caso.

FFmpeg é binário externo do sistema, não dependência pip. Trate separado.

---

## 7. Comentários explicam decisões, não o óbvio

Comente **por quê**, nunca **o quê**.

```python
# Ruim: soma a e b
total = a + b

# Bom: -1 em vez de 0 porque o índice do primeiro frame é 1 no container MP4,
#       e a API do FFmpeg usa base 0 (ver issue #12).
first_frame = index - 1
```

Não comente o que o código já diz com clareza. Prefira nomes bons a comentários.

---

## 8. Segredos nunca no código

Proibido, sem exceção:

- chave de API, token, senha ou cookie em arquivo versionado;
- string de conexão com credencial;
- segredo em comentário, docstring, log ou mensagem de erro.

Use `.env`, lido em tempo de execução. O `.env` é ignorado pelo Git.
O `.env.example` contém **apenas nomes de variáveis e valores vazios**.

Ao precisar de uma variável nova: acrescente o nome no `.env.example` com
comentário indicando a fase, e o valor real só no `.env` local.

---

## 9. Comandos destrutivos exigem autorização

Nunca execute sem pedir antes:

- `git push`, `git reset --hard`, `git clean`, `git rebase`, `git checkout .`;
- `git add .`, `git add -A` ou `git commit` (o usuário controla o histórico);
- remoção em massa de arquivos ou pastas;
- sobrescrita de arquivos existentes sem reler antes;
- rodar comando em pasta fora do projeto.

Sempre com autorização explícita: **nunca** `git push`. Mesmo que exista
remote configurado. O usuário decide o momento do push.

---

## 10. Reutilizar sem abstrair demais

Antes de escrever código novo, verifique se já existe no `src/`.

Ao reutilizar, extraia para um módulo só quando a **terceira** ocorrência
pedir isso. Até lá, duplicar três linhas é melhor do que um módulo abstrato
difícil de ler. Não criar `utils.py`, `helpers.py` ou `base.py` genérico.

---

## 11. Seção não negociável: explicar antes

Antes de alteração grande, o agente deve explicar em texto o que pretende
fazer, o por quê, e o que **não** vai fazer. Depois de alterar, mostrar:

- arquivos criados;
- arquivos alterados;
- o papel de cada um;
- a árvore final;
- comandos de verificação;
- problemas encontrados.

O usuário é desenvolvedor júnior e quer **entender**, não apenas receber
o resultado. Explique decisões em linguagem simples.

---

## 12. Ambiente deste projeto

- **SO:** Windows, PowerShell 5.1
- **Git:** 2.53.0.windows.2
- **Python:** 3.14.6, acessado pelo launcher `py`

Regra prática: **use `py`, nunca `python`.** O comando `python` aponta para o
alias da Microsoft Store e falha nesta máquina.

Comandos devem seguir a sintaxe do PowerShell 5.1 — não há `&&`, use
`; if ($?) { ... }`. Não usar sintaxe de CMD nem de bash.

---

## 13. Convenção de idioma

Documentação de prose (`README.md`, `AGENTS.md`) é escrita em **português com
acentuação correta**, em UTF-8.

Arquivos lidos por ferramentas — `.gitignore`, `.env.example`,
`requirements.txt`, e todo código-fonte — permanecem em **ASCII puro**, para
não depender da codificação do console do Windows.

Comentários dentro de código seguem a mesma regra: ASCII.

---

## 14. Resumo em uma frase

Faça o que foi pedido, na fase atual, do jeito mais simples possível,
explique o que você fez, e pare.
