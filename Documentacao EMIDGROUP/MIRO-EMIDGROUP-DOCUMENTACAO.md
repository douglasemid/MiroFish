# Miro.EMIDGROUP — Documentação Completa

> **Versão:** 1.0
> **Data:** Abril de 2026
> **Domínio em produção:** https://miro.emidgroup.com.br
> **Repositório (fork):** https://github.com/douglasemid/MiroFish
> **Repositório upstream:** https://github.com/666ghj/MiroFish

---

## Sumário

1. [Visão geral do projeto](#1-visão-geral-do-projeto)
2. [Tradução completa para Português Brasileiro](#2-tradução-completa-para-português-brasileiro)
3. [Variáveis de ambiente — explicação técnica](#3-variáveis-de-ambiente--explicação-técnica)
4. [Modus operandi de uma simulação MiroFish](#4-modus-operandi-de-uma-simulação-mirofish)
5. [Fórmula de custo e dimensionamento](#5-fórmula-de-custo-e-dimensionamento)
6. [Provedores de LLM compatíveis](#6-provedores-de-llm-compatíveis)
7. [LLMs locais (Llama, Mistral) — viabilidade](#7-llms-locais-llama-mistral--viabilidade)
8. [Configuração via UI vs configuração via .env](#8-configuração-via-ui-vs-configuração-via-env)
9. [Como construir um prompt eficaz](#9-como-construir-um-prompt-eficaz)
10. [Exemplo de prompt avançado: proposta comercial para 200 ISPs](#10-exemplo-de-prompt-avançado-proposta-comercial-para-200-isps)
11. [Operação no servidor (comandos úteis)](#11-operação-no-servidor-comandos-úteis)
12. [Observações Avançadas](#12-observações-avançadas)

---

## 1. Visão geral do projeto

### O que é o MiroFish

**MiroFish** é um motor de simulação de inteligência coletiva baseado em multi-agentes LLM. A partir de um material-semente (PDF, MD, TXT — relatório, notícia, roteiro, proposta comercial), ele:

1. Extrai entidades, gera personas com personalidade, memória de longo prazo e lógica própria
2. Constrói automaticamente um "mundo digital paralelo" usando o framework **OASIS** (CAMEL-AI) que simula plataformas estilo Twitter e Reddit
3. Coloca centenas/milhares de agentes para interagir nesse mundo durante N rodadas de tempo simulado
4. Um **Report Agent** analisa toda a simulação e devolve um relatório de previsão estruturado, mais a possibilidade de chat interativo com qualquer agente do mundo simulado

**Casos de uso típicos:**
- Previsão de reação pública a uma decisão, anúncio ou produto
- Teste de pitch de vendas antes de uma rodada real de prospecção
- Análise de risco reputacional de uma campanha
- Exploração de finais alternativos para narrativas (literatura, roteiro)
- Análise de mercado e ICP refinement
- Antecipação de objeções comerciais

### Stack técnica

| Camada | Tecnologia |
|---|---|
| Backend | **Python 3.11+** + Flask 3 + Flask-CORS, porta interna **5001** |
| Frontend | **Vue 3** + Vite 7 + vue-router + vue-i18n + d3 + axios, porta interna **3000** |
| Engine de simulação | **camel-oasis 0.2.5** + camel-ai 0.2.78 |
| LLM | API externa OpenAI-compatible (suporta qualquer provedor que fale o formato OpenAI SDK) |
| Memória de agentes | **Zep Cloud** (SaaS, free tier inicial) |
| Processamento de texto | PyMuPDF, pydantic, python-dotenv, charset-normalizer |
| Empacotamento | Docker (`mirofish-pt:local` na nossa instalação) |
| Persistência | Sem banco próprio — apenas `./backend/uploads` em volume Docker |

### Infraestrutura na VPS EMIDGROUP

- **Host:** `187.77.234.102`
- **Domínio:** `miro.emidgroup.com.br` (registro DNS A apontando para a VPS)
- **Rede Docker:** bridge dedicada para o ecossistema EMIDGROUP
- **SSL:** Let's Encrypt válido até 2026-07-06, renovação automática
- **Reverse proxy:** Nginx (containerizado) com server block dedicado para `miro.emidgroup.com.br`
- **Pasta isolada na VPS:** `/home/deploy/mirofish/`
- **Imagem Docker:** `mirofish-pt:local` (buildada localmente a partir do fork `douglasemid/MiroFish` com tradução PT-BR embutida)
- **Consumo idle do container:** ~500 MB RAM, 1% CPU

---

## 2. Tradução completa para Português Brasileiro

### Estratégia adotada

O MiroFish nativo só tem dois idiomas de UI traduzidos: **Chinês (zh)** e **Inglês (en)**. Para o português, há entrada em `locales/languages.json` mas **só serve para instruir o LLM** — não tem arquivo de tradução de UI. Em outras palavras, antes do nosso trabalho:
- ✅ Os agentes podiam responder em pt-BR
- ❌ Mas a interface (botões, labels, mensagens) ficava em chinês ou inglês

### O que foi feito

1. **Criação de `locales/pt.json`** com **646 strings** traduzidas a partir de `locales/en.json`, mantendo:
   - Todas as chaves originais preservadas (`common.confirm`, `step2.simulationDuration`, etc)
   - Todos os placeholders de variáveis intactos (`{count}`, `{error}`, `{title}`)
   - Vocabulário e gramática **brasileiros** (não europeu)
   - Termos técnicos preservados quando padrão (Agent, GraphRAG, ReACT, MBTI, LLM, Reddit, Twitter)

2. **Definição de PT-BR como idioma padrão** em `frontend/src/i18n/index.js`:
   ```js
   const savedLocale = localStorage.getItem('locale') || 'pt'   // antes era 'zh'
   const i18n = createI18n({
     legacy: false,
     locale: savedLocale,
     fallbackLocale: 'en',                                       // antes era 'zh'
     messages
   })
   ```

3. **Refinamento da instrução LLM** em `locales/languages.json`:
   ```json
   "pt": {
     "label": "Português (BR)",
     "llmInstruction": "Por favor, responda sempre em português brasileiro (pt-BR), usando vocabulário, gramática e expressões naturais do Brasil. Não use português europeu."
   }
   ```
   Essa instrução é enviada pelo backend Flask para cada chamada do LLM, garantindo que **personas e relatórios sempre saiam em pt-BR**.

4. **Replicação de regras CSS** de `html[lang="en"]` para `html[lang="pt"]` usando o seletor moderno `:is()`, em três arquivos:
   - `frontend/src/views/Home.vue`
   - `frontend/src/components/Step4Report.vue`
   - `frontend/src/components/Step5Interaction.vue`

   Por quê? Palavras em português são significativamente mais longas que em chinês. Sem isso, títulos, descrições de etapas e labels ficariam quebrados ou cortados em telas estreitas. As regras originais já existiam para o inglês (que tem o mesmo problema) — apenas estendemos para PT.

5. **Edição do `frontend/index.html`** (HTML estático que carrega antes do Vue bootar):
   ```html
   <html lang="pt">
   <script>document.documentElement.lang = localStorage.getItem('locale') || 'pt'</script>
   <meta name="description" content="MiroFish - Sistema de Simulação de Opinião em Mídias Sociais" />
   <title>MiroFish - Preveja Tudo</title>
   ```
   Antes esses elementos ficavam em chinês durante o split-second que o Vue leva para inicializar.

### Como o sistema de i18n funciona internamente

**Frontend (Vue + vue-i18n):** o i18n auto-carrega qualquer arquivo `locales/*.json` registrado em `languages.json`. Salva a escolha do usuário em `localStorage` sob a chave `locale`. O componente `LanguageSwitcher.vue` permite trocar dinamicamente.

**Backend (Flask):** o backend lê o header HTTP `Accept-Language` enviado automaticamente pelo frontend (via interceptor axios). Carrega o arquivo `pt.json` correspondente em memória e usa a função utilitária `t(key)` em `backend/app/utils/locale.py`. A função `get_language_instruction()` retorna o `llmInstruction` do `languages.json` para injetar nos prompts do LLM.

**Resumo:** o sistema é elegante e plug-and-play. Adicionar um novo idioma exige apenas (a) criar o arquivo `<codigo>.json` e (b) registrar o `llmInstruction` no `languages.json`. Nenhuma mudança de código backend é necessária.

### Como atualizar a tradução no futuro

Se você quiser ajustar uma string específica (ex: trocar "Construir Grafo" por "Montagem do Grafo"):

```bash
# Localmente (Mac), no clone do fork
cd /Users/marketing/Documents/PROJETOS-CLAUDE/MiroFish

# Editar locales/pt.json — buscar a chave, ajustar o valor

git add locales/pt.json
git commit -m "i18n(pt): ajusta tradução X"
git push origin main

# Na VPS (via SSH), pull e restart
ssh -i ~/.ssh/id_ed25519 root@187.77.234.102
cd /home/deploy/mirofish/src && git pull
cd /home/deploy/mirofish && docker compose restart
```

> **Atenção:** o `pt.json` foi embutido na imagem Docker durante o build. Para mudanças no JSON valerem sem rebuild, é necessário adicionar um bind-mount do `pt.json` no `docker-compose.yml`. Pode ser feito sob demanda.

### Validação da tradução

Após a tradução, foi rodada uma comparação estrutural automática entre `en.json` e `pt.json`:

```
en keys: 646
pt keys: 646
missing in pt: 0
extra in pt: 0
JSON válido: OK
```

100% de paridade — toda string do inglês tem equivalente português.

---

## 3. Variáveis de ambiente — explicação técnica

Todas as variáveis abaixo estão definidas em `backend/app/config.py` e podem ser configuradas via arquivo `.env` em `/home/deploy/mirofish/.env` na VPS.

### 🔑 Obrigatórias (sem isso o backend não inicia)

| Variável | Default | O que faz |
|---|---|---|
| `LLM_API_KEY` | — | Chave da API do LLM (qualquer provedor compatível com OpenAI SDK) |
| `ZEP_API_KEY` | — | Chave do Zep Cloud (sistema de memória de longo prazo dos agentes) |

Sem qualquer uma das duas, a função `Config.validate()` aborta a inicialização do Flask com `sys.exit(1)`.

### 🤖 LLM principal

| Variável | Default | O que faz |
|---|---|---|
| `LLM_BASE_URL` | `https://api.openai.com/v1` | Endpoint OpenAI-compatible — onde o backend envia as requisições |
| `LLM_MODEL_NAME` | `gpt-4o-mini` | Nome do modelo a ser usado em cada chamada |

### ⚡ LLM acelerador (opcional, mas estrategicamente valioso)

Permite usar **dois LLMs em paralelo** dentro da mesma simulação: um modelo "pesado" para tarefas que exigem qualidade (geração de personas, planejamento do relatório, ferramentas analíticas) e um modelo "barato e rápido" para as ações repetitivas dos agentes (que são milhares de chamadas).

| Variável | Default | O que faz |
|---|---|---|
| `LLM_BOOST_API_KEY` | (vazio) | Chave do LLM acelerador (pode ser a mesma do principal) |
| `LLM_BOOST_BASE_URL` | (vazio) | Endpoint do acelerador |
| `LLM_BOOST_MODEL_NAME` | (vazio) | Modelo do acelerador (ex: `qwen-turbo`) |

> **Importante:** se você não vai usar o acelerador, **não inclua essas variáveis no `.env`** — nem mesmo vazias. A presença com valores em branco pode causar erros.

> 💡 **Estratégia de economia:** configure `LLM_MODEL_NAME=qwen-plus` (qualidade alta para personas e relatórios) e `LLM_BOOST_MODEL_NAME=qwen-turbo` (custo baixo para os ticks de agente). Pode reduzir o custo total de uma simulação em **60-80%**.

### 🌐 Simulação OASIS

| Variável | Default | O que faz |
|---|---|---|
| `OASIS_DEFAULT_MAX_ROUNDS` | `10` | Número padrão de rodadas (ticks de tempo simulado) por simulação. **Sobrescritível por simulação na UI** via toggle "Personalizado" no Step 2. |

### 📝 Report Agent (gerador do relatório final)

| Variável | Default | O que faz |
|---|---|---|
| `REPORT_AGENT_MAX_TOOL_CALLS` | `5` | Máximo de chamadas de ferramentas (InsightForge, PanoramaSearch, QuickSearch, InterviewSubAgent) que o Report Agent pode fazer por seção do relatório |
| `REPORT_AGENT_MAX_REFLECTION_ROUNDS` | `2` | Quantas rodadas de auto-reflexão o agente faz antes de finalizar uma seção |
| `REPORT_AGENT_TEMPERATURE` | `0.5` | Criatividade do relatório (0 = preciso/literal, 1 = criativo/imprevisível) |

### ⚙️ Flask / infraestrutura

| Variável | Default | O que faz |
|---|---|---|
| `SECRET_KEY` | `mirofish-secret-key` | Chave de sessão do Flask. **Trocar em produção.** |
| `FLASK_DEBUG` | `True` | Modo debug com hot-reload e stack traces. **Recomendado `False` em produção.** |
| `FLASK_HOST` | `0.0.0.0` | Bind address do Flask |
| `FLASK_PORT` | `5001` | Porta interna do Flask |

### 📦 Constantes não-configuráveis (hardcoded no `config.py`)

Estas estão em código e exigem alterar o fonte para mudar:

- `MAX_CONTENT_LENGTH = 50 * 1024 * 1024` → upload máx **50 MB**
- `ALLOWED_EXTENSIONS = {pdf, md, txt, markdown}` → tipos de arquivo aceitos
- `DEFAULT_CHUNK_SIZE = 500` → tamanho dos chunks de texto enviados ao Zep
- `DEFAULT_CHUNK_OVERLAP = 50` → overlap entre chunks consecutivos

### Configuração atual em produção (estado da arte)

```env
# LLM principal — Alibaba Model Studio (Singapore / Internacional)
LLM_API_KEY=sk-a36c85c88d9f4d5b8bc4d075e4076649
LLM_BASE_URL=https://dashscope-intl.aliyuncs.com/compatible-mode/v1
LLM_MODEL_NAME=qwen-plus

# Zep Cloud — memória de agentes
ZEP_API_KEY=z_1dWlk...

# (Acelerador comentado — pode ser ativado quando necessário)
# LLM_BOOST_API_KEY=sk-...
# LLM_BOOST_BASE_URL=https://dashscope-intl.aliyuncs.com/compatible-mode/v1
# LLM_BOOST_MODEL_NAME=qwen-turbo
```

---

## 4. Modus operandi de uma simulação MiroFish

Esta seção descreve, passo a passo, **o que acontece tecnicamente** quando o usuário cria uma simulação na UI até receber o relatório final.

### Os dois eixos independentes

Antes de tudo, é fundamental entender que uma simulação tem **dois eixos completamente separados** que muitos confundem:

| Eixo | O que controla | Onde se ajusta |
|---|---|---|
| **Quantidade de agentes** (= "pessoas" simuladas) | Quantos personas o LLM gera. Pode ser 50, 100, 500, 1000+ | **Implícito**: o LLM decide com base no prompt + documento. Visualizado no Step 2 da UI antes de iniciar. |
| **Quantidade de rodadas** (= ticks de tempo simulado) | Por quantos "ticks" o motor avança o relógio do mundo simulado | **Explícito**: variável `OASIS_DEFAULT_MAX_ROUNDS` ou toggle "Personalizado" no Step 2 |

**Analogia útil:** pense em um jogo tipo *The Sims*.
- **Agentes** = quantas pessoas existem na cidade
- **Rodadas** = quantos "dias" o jogo roda antes de você apertar pause

Você pode ter 100 pessoas × 10 rodadas (cidade média, simulação curta) ou 5.000 pessoas × 100 rodadas (cidade gigante, simulação longa). São independentes.

### O que acontece em cada rodada

Cada rodada é um **tick de tempo no mundo simulado**. Por exemplo, se a simulação representa 24 horas reais distribuídas em 10 rodadas, cada rodada equivale a ~2,4 horas do mundo simulado.

Em cada rodada:
1. **Cada agente** (cada uma das pessoas simuladas) é "acordado" pelo motor OASIS
2. O LLM é chamado **uma vez por agente** para decidir o que essa persona faz: postar, curtir, comentar, seguir, repostar, ficar quieto
3. As ações acontecem no "Twitter/Reddit simulado" (memória mantida no Zep)
4. O sistema atualiza memórias individuais, conexões sociais, posts virais e tópicos em alta
5. Avança para a próxima rodada

### As 5 etapas (Steps) da UI

**Step 1 — Construir Grafo (Graph Build)**

- Você sobe um ou mais documentos (PDF/MD/TXT, máx 50 MB cada)
- Você escreve o **prompt da simulação** em linguagem natural
- O LLM analisa o conteúdo, extrai entidades, gera uma ontologia (estrutura de conceitos)
- Os documentos são chunked (divididos em pedaços de ~500 chars) e enviados ao Zep para construir um **GraphRAG** (grafo de conhecimento com memória temporal)
- Resultado: nós de entidade, arestas de relação, tipos de schema

**Step 2 — Configuração de Ambiente (Env Setup)**

- O LLM combina o GraphRAG com o prompt para extrair entidades e relações relevantes
- **Personas dos agentes são geradas** — cada uma com idade, gênero, profissão, MBTI aparente, biografia, memórias formadas, posição na rede social
- Configuração das duas plataformas simuladas (Twitter-like e Reddit-like): time flow, algoritmos de recomendação, horários ativos de cada persona, frequência de postagens, viral threshold, echo chamber strength
- Você vê o **número total de agentes esperados** e pode ajustar as **rodadas** (toggle "Personalizado" → escolhe N rodadas em vez do default)
- Eventos iniciais e tópicos em alta são gerados para "dar vida" ao mundo no momento zero

**Step 3 — Executar Simulação (Run Simulation)**

- A simulação roda em paralelo nas duas plataformas (Twitter-like e Reddit-like)
- Cada rodada é executada conforme descrito acima
- Memória do grafo é atualizada dinamicamente
- O usuário acompanha em tempo real o progresso (rodada atual, ações executadas, métricas)
- Pode parar a qualquer momento

**Step 4 — Geração de Relatório (Report Generation)**

- O **Report Agent** entra em ação após o final da simulação
- Ele planeja a estrutura do relatório (outline) baseada no prompt original
- Para cada seção, faz **busca profunda** combinando até 4 ferramentas:
  - **InsightForge** — atribuição profunda alinhando dados-semente com estado da simulação
  - **PanoramaSearch** — algoritmo BFS que reconstrói caminhos de propagação de eventos
  - **QuickSearch** — recuperação rápida via GraphRAG
  - **InterviewSubAgent** — entrevistas autônomas com indivíduos simulados
- Usa raciocínio **ReACT** (Reasoning + Acting) para iterar até produzir conteúdo de qualidade
- Cada seção é salva como `section_<N>.md` e depois montada num relatório completo

**Step 5 — Interação Profunda (Deep Interaction)**

- Após o relatório pronto, você pode:
  - **Conversar diretamente com o Report Agent** (ele tem memória completa da simulação)
  - **Conversar 1:1 com qualquer indivíduo simulado** (perguntar sua opinião, motivações, planos)
  - **Enviar pesquisas (surveys)** para múltiplos agentes simultaneamente (escolhe os alvos, faz a pergunta, recebe respostas em paralelo)

### Fluxo simplificado em diagrama

```
Usuário sobe PDF + Prompt
        ↓
[Step 1] Extração de ontologia + GraphRAG (Zep)
        ↓
[Step 2] Geração de ~N personas + config de mundo
        ↓ (usuário ajusta rodadas se quiser)
[Step 3] Loop de M rodadas × N agentes × LLM call
        ↓ (memórias evoluem em tempo real)
[Step 4] Report Agent gera relatório multi-seção via ReACT
        ↓
[Step 5] Chat com agentes / Surveys / Drill-down
```

---

## 5. Fórmula de custo e dimensionamento

### A fórmula básica

```
chamadas LLM totais ≈ rodadas × agentes
custo total ≈ chamadas × custo_médio_por_chamada + overhead
```

O **overhead** inclui: geração de personas (uma chamada por agente no início), construção da ontologia, configuração de plataforma, planejamento e geração do relatório (várias chamadas por seção). Pode somar de 10% a 50% além do cálculo básico.

### Tabela de referência (com Qwen-Plus)

Estimativas grosseiras assumindo `qwen-plus` como modelo principal e tamanhos de prompt típicos (~1.500 tokens entrada + ~300 tokens saída por chamada):

| Cenário | Agentes | Rodadas | Chamadas LLM | Custo aproximado |
|---|---|---|---|---|
| Teste mínimo | 20 | 5 | ~100 | ~US$ 0,05 |
| Teste pequeno | 50 | 10 | ~500 | ~US$ 0,15 |
| Padrão | 100 | 10 | ~1.000 | ~US$ 0,30 |
| Médio | 100 | 40 | ~4.000 | ~US$ 1,20 |
| Médio-longo | 200 | 30 | ~6.000 | ~US$ 1,80 |
| Grande | 500 | 100 | ~50.000 | ~US$ 15,00 |
| Massivo | 5.000 | 100 | ~500.000 | ~US$ 150,00 |

> **Atenção:** o custo real pode ser **2x a 5x maior** que essa estimativa devido ao overhead descrito acima e ao tamanho variável do contexto acumulado conforme a simulação progride.

### Tabela comparativa de custo entre modelos

Mesma simulação de **200 agentes × 10 rodadas** (~2.000 chamadas):

| Modelo | Provedor | Custo estimado |
|---|---|---|
| `qwen-turbo` | Alibaba Model Studio | ~US$ 0,20 |
| `qwen-plus` | Alibaba Model Studio | ~US$ 0,80 |
| `gpt-4o-mini` | OpenAI | ~US$ 1,00 |
| `claude-haiku-4-5` | Anthropic (via OpenRouter) | ~US$ 1,50 |
| `deepseek-chat` | DeepSeek | ~US$ 0,30 |
| `llama-3.3-70b` | Groq (free tier) | **grátis** (com rate limit) |
| `claude-sonnet-4-6` | Anthropic (via OpenRouter) | ~US$ 5,00 |
| `claude-opus-4-6` | Anthropic (via OpenRouter) | ~US$ 25,00 |

### Recomendação para começar

**Mantenha `OASIS_DEFAULT_MAX_ROUNDS=10`** e use **`qwen-plus`** (já configurado em produção). É o equilíbrio mais saudável entre custo e qualidade para validar se o produto serve para o seu caso.

Quando estiver confortável e quiser:
- **Reduzir custo:** ative o acelerador `qwen-turbo`
- **Elevar qualidade do relatório:** troque o principal para `claude-sonnet-4-6` via OpenRouter
- **Testar grátis:** crie conta no Groq, use `llama-3.3-70b-versatile`

---

## 6. Provedores de LLM compatíveis

O MiroFish aceita **qualquer API que fale o formato OpenAI SDK**. Isso abre um leque enorme.

### 🥇 Alibaba Model Studio (atualmente em uso)

- **Endpoint internacional:** `https://dashscope-intl.aliyuncs.com/compatible-mode/v1`
- **Endpoint chinês:** `https://dashscope.aliyuncs.com/compatible-mode/v1`
- **Modelos recomendados:** `qwen-plus`, `qwen-turbo`, `qwen-max`, `qwen3.5-plus`, `qwen3-max`
- **Cadastro:** https://modelstudio.console.alibabacloud.com/
- **Notas:** ótimo custo-benefício, bom em PT-BR, free quota inicial generoso

### 🟣 Anthropic Claude (via OpenRouter — recomendado)

A Anthropic tem **formato próprio incompatível** com OpenAI SDK. Para usar Claude no MiroFish, o caminho mais simples é via **OpenRouter**, um gateway unificado.

**Configuração:**
```env
LLM_API_KEY=sk-or-v1-sua-chave-openrouter
LLM_BASE_URL=https://openrouter.ai/api/v1
LLM_MODEL_NAME=anthropic/claude-haiku-4-5
```

**Modelos Claude disponíveis (use o ID exato):**
- `anthropic/claude-haiku-4-5` — mais barato e rápido (~US$ 1/M tokens input)
- `anthropic/claude-sonnet-4-6` — equilíbrio (~US$ 3/M tokens input)
- `anthropic/claude-opus-4-6` — top de linha (~US$ 15/M tokens input)

**Vantagens do OpenRouter:**
- Não precisa criar conta na Anthropic
- Acesso unificado a 200+ modelos: GPT, Claude, Gemini, Llama, Qwen, DeepSeek, Mistral
- Failover automático entre provedores
- Trocar de modelo = trocar 1 string no `.env`

**Custo:** OpenRouter cobra ~5% de markup sobre o preço direto do provedor. Trade-off geralmente favorável.

**Cadastro:** https://openrouter.ai → login com Google → adiciona crédito → Settings → Keys → Create Key

### 🟢 Outras opções OpenAI-compatible

| Provedor | Endpoint | Notas |
|---|---|---|
| **OpenAI** | `https://api.openai.com/v1` | Modelos `gpt-4o-mini`, `gpt-4o`, `o1-mini`. Cadastro padrão. |
| **DeepSeek** | `https://api.deepseek.com/v1` | Chinês, MUITO barato, qualidade comparável a GPT-4o-mini. |
| **Groq** | `https://api.groq.com/openai/v1` | Roda Llama/Qwen em hardware proprietário, ULTRA rápido (~500 tokens/seg). **Tem free tier generoso.** |
| **Cerebras** | `https://api.cerebras.ai/v1` | Similar ao Groq, free tier disponível. |
| **Together.ai** | `https://api.together.xyz/v1` | Llama, Qwen, Mistral, etc. Free credits no signup. |
| **Mistral** | `https://api.mistral.ai/v1` | Modelos europeus (Mistral Large, Codestral). |

---

## 7. LLMs locais (Llama, Mistral) — viabilidade

### A pergunta

> "É possível usar LLMs gratuitas que são instaláveis na VPS? Como Llama ou similar?"

### A resposta honesta

**Tecnicamente sim. Na prática, na sua VPS atual, NÃO.**

### Por quê?

Sua VPS tem:
- **2 vCPUs** (não potentes)
- **7,8 GB RAM** (com o MiroFish e demais serviços consumindo ~2 GB)
- **Sem GPU**

LLMs locais minimamente úteis exigem:
- **GPU com VRAM:** 8 GB+ para um modelo 7B em fp16, 4 GB+ para quantizado Q4
- **Ou CPU + muita RAM:** 16 GB+ para um modelo 7B quantizado, e mesmo assim **muito lento**

### Tabela de tempo por chamada LLM

| Modelo | Hardware | Tempo por resposta |
|---|---|---|
| Llama 3.2 1B (mini) | CPU 2-core | ~10-30s |
| Llama 3 8B Q4 | CPU 2-core | ~60-180s |
| Qwen-Plus (cloud) | API | ~1-2s |
| Claude Haiku (cloud) | API | ~1-3s |

### O efeito disso no MiroFish

Lembre-se: cada simulação faz **2.000 a 50.000 chamadas LLM**. Faça a conta:

```
2.000 chamadas × 60s = 120.000 segundos = 33 HORAS por simulação
```

E ainda com **qualidade muito pior** que os modelos cloud. **Inviável.**

### Quando faria sentido rodar local?

Você só consideraria local LLM se:
1. ✅ Tivesse uma máquina com **GPU NVIDIA potente** (RTX 3090/4090, A100, H100...)
2. ✅ Quisesse **privacidade absoluta** dos dados (sem API externa)
3. ✅ Tivesse volume tão alto que API ficasse cara demais

### Alternativa pragmática: Groq

Se a motivação para querer "local" é "Llama de graça", crie conta no **Groq**:

- URL: https://console.groq.com
- Free tier com bom limite
- Modelos: `llama-3.3-70b-versatile`, `llama-3.1-8b-instant`, `mixtral-8x7b-32768`, `gemma2-9b-it`
- Velocidade absurda (~500 tokens/seg via hardware proprietário LPU)

**Configuração no MiroFish:**
```env
LLM_BASE_URL=https://api.groq.com/openai/v1
LLM_MODEL_NAME=llama-3.3-70b-versatile
LLM_API_KEY=gsk_...
```

---

## 8. Configuração via UI vs configuração via .env

### ✅ Configurável pela UI (por simulação)

- **Prompt da simulação** (descrição em linguagem natural)
- **Upload do material-semente** (PDF/MD/TXT)
- **Número de rodadas** (toggle "Personalizado" no Step 2 — sobrescreve o default do `.env`)
- **Visualização das personas geradas** (revisão antes de iniciar a simulação)
- **Visualização da configuração de algoritmo de recomendação, viral threshold, echo chamber strength** — gerados automaticamente, mostrados na tela mas **não editáveis** via UI
- **Visualização dos tópicos iniciais (initial hot topics)** — gerados, visualizáveis, não editáveis

### ❌ Só configurável via `.env` (variáveis globais)

- Chaves de API (LLM e Zep)
- Modelo do LLM (`qwen-plus`, `qwen-turbo`, `gpt-4o-mini`...)
- Endpoint base do LLM (`LLM_BASE_URL`)
- LLM acelerador
- Temperatura do Report Agent
- Limites do Report Agent (tool calls, reflection rounds)
- Default de rodadas (sobrescritível na UI por simulação)
- Modo debug do Flask

### 🚫 Não tem painel admin

**Não existe** uma tela tipo `/admin/settings` ou `/configuracoes` onde você loga e ajusta esses parâmetros pelo navegador. Mudanças no `.env` exigem **editar o arquivo no servidor e dar restart no container**.

### Como aplicar mudanças no `.env`

```bash
ssh -i ~/.ssh/id_ed25519 root@187.77.234.102
nano /home/deploy/mirofish/.env
# editar variáveis, Ctrl+O para salvar, Ctrl+X para sair
cd /home/deploy/mirofish && docker compose restart
docker logs -f mirofish    # acompanhar para ver se subiu OK
```

---

## 9. Como construir um prompt eficaz

### Por que isso importa

A qualidade da simulação depende **80% da qualidade do prompt + do material-semente**. Um prompt vago tipo *"simule donos de provedores"* gera personas genéricas e resultados rasos. Um prompt cirúrgico produz insights acionáveis.

### Anatomia de um bom prompt MiroFish

Um prompt eficaz tem **5 elementos** estruturados:

1. **CONTEXTO** → quem é o "público" simulado (perfil sócio-demográfico, características, dores)
2. **ESTÍMULO** → o evento, oferta ou material que vai disparar a simulação
3. **VARIÁVEIS** → o que pode mudar entre os agentes (heterogeneidade)
4. **OBJETIVO** → o que você quer prever ou medir
5. **RESTRIÇÕES** → limites de tamanho, escopo, tempo simulado

### Material-semente: o segundo pilar

O prompt sozinho não basta. O LLM precisa de **contexto rico** para construir personas realistas. O material-semente (PDF/MD/TXT que você sobe) é onde mora esse contexto.

**Tipos de material úteis:**
- Roteiros de pitch / scripts comerciais
- Propostas comerciais completas
- Pesquisas de mercado / relatórios setoriais
- Personas de clientes anteriores (mesmo fictícias mas realistas)
- Listas de objeções comuns já ouvidas
- Tabelas de preços + comparativos com concorrentes
- Briefings de campanha
- Releases / posts de imprensa
- Capítulos de livros
- Artigos científicos

> **Mínimo viável:** se for subir só 1 documento, consolide os mais importantes em um único PDF de até 30 páginas. Sem material rico, a simulação inventa coisas.

---

## 10. Exemplo de prompt avançado: proposta comercial para 200 ISPs

Este é um exemplo real de como estruturar um prompt complexo. **Caso de uso:** simular a recepção de uma proposta comercial de serviços de marketing por aproximadamente 200 donos de provedores regionais de internet (ISPs) brasileiros, para prever taxa de fechamento e capturar objeções qualitativas.

### O prompt completo

```
Simule a recepção de uma proposta comercial de serviços de marketing
por aproximadamente 200 donos de provedores regionais de internet (ISPs)
brasileiros, considerando o perfil descrito a seguir.

PERFIL DOS AGENTES (~200 personas):
Donos ou sócios-administradores de provedores de internet de pequeno e
médio porte no Brasil, com 500 a 15.000 assinantes ativos. Distribuídos
por diferentes regiões (Norte, Nordeste, Centro-Oeste, Sul, Sudeste).
Maioria com formação técnica (engenharia, redes, telecom), entre 30 e
55 anos, autodidatas em gestão, fundadores que cresceram organicamente.
Compartilham as seguintes dores:

- Marketing rudimentar (boca a boca, panfletos, Facebook ads sem estratégia)
- Concorrência crescente de grandes operadoras (Vivo, Claro, Oi) e ISPs maiores
- Churn alto sem mensuração precisa
- Equipe interna sem skill de marketing digital
- Desconfiança histórica de agências (já foram queimados antes por promessas vazias)
- Foco operacional (rede, NOC, suporte) em detrimento do crescimento de receita
- Decisão de compra rápida quando enxergam ROI claro, mas céticos por padrão

Distribua entre eles personas heterogêneas: alguns mais analíticos,
outros mais relacionais, alguns early adopters, outros conservadores,
alguns financeiramente apertados, outros com fluxo de caixa folgado.
Inclua variações de humor inicial (cético, neutro, entusiasmado).

ESTÍMULO (evento da simulação):
Cada agente recebeu o pitch comercial em anexo (PDF) e participou de
uma call remota one-to-one de 45 minutos com o vendedor da
[SEU NOME / EMPRESA]. Após a call, eles têm acesso a um "feed simulado"
estilo grupo de WhatsApp de donos de provedores, onde podem comentar a
proposta entre si, tirar dúvidas, compartilhar receios, e influenciar
uns aos outros ao longo de ~7 dias simulados antes de tomar a decisão
de fechar ou não.

VARIÁVEIS QUE QUERO OBSERVAR:
- Quem fecha imediatamente após a call (24h)
- Quem fecha depois de discutir com os pares (72h+)
- Quem rejeita imediatamente e por quê
- Quem fica em "vou pensar" indefinido
- Quais objeções aparecem com mais frequência
- Como o sentimento coletivo evolui ao longo dos dias
- Se algum "líder de opinião" emerge no grupo influenciando os outros

OBJETIVOS DE PREVISÃO:
1. Estimativa quantitativa de fechamento: % em 7 dias, segmentado por
   porte do provedor (pequeno vs médio) e por região
2. Top 5 objeções qualitativas: quais argumentos contrários surgem mais
   e como reagi-los
3. Top 5 ganchos positivos: o que mais ressoou no pitch e deve ser amplificado
4. Perfil do comprador ideal (ICP refinado): subgrupos com maior taxa de conversão
5. Sugestões de ajuste no pitch: o que reescrever, remover ou enfatizar
6. Risco reputacional: chance de feedback negativo público

HORIZONTE TEMPORAL:
Simule 7 dias de tempo decorrido após a call. As decisões de compra
podem acontecer em qualquer momento dessa janela.
```

### Material-semente recomendado para esta simulação

Suba (consolidados em um único PDF/MD se possível):

1. **Sua proposta comercial completa** (5-15 páginas) — escopo, entregas, preço, prazo, cases anteriores, time
2. **Roteiro/script do pitch de vendas** (transcrição do que você fala na call de 45 min) — **fundamental**
3. **Pesquisa de mercado de ISPs brasileiros** (relatório público da ANATEL, Telebrasil, ABRINT) — dá densidade ao perfil
4. **3-5 personas de clientes anteriores** (mesmo fictícias mas realistas) — calibra o LLM
5. **Lista de objeções comuns** já ouvidas em outros pitches — ouro puro para o LLM antecipar
6. **Tabela de preços + comparativo com concorrentes**

### Configuração técnica recomendada para esta simulação

| Parâmetro | Valor sugerido | Por quê |
|---|---|---|
| `OASIS_DEFAULT_MAX_ROUNDS` | **30 a 50** | 7 dias simulados / 30-50 rodadas → cada rodada representa algumas horas de tempo simulado |
| `LLM_MODEL_NAME` | `qwen-plus` ou `claude-haiku-4-5` (via OpenRouter) | Personas críticas precisam de qualidade |
| `LLM_BOOST_MODEL_NAME` | `qwen-turbo` | Para os 6.000-10.000 ticks de agente, modelo barato |
| `REPORT_AGENT_TEMPERATURE` | `0.3` | Quer relatório analítico, não criativo |
| `REPORT_AGENT_MAX_TOOL_CALLS` | `8` | Mais investigação por seção do relatório |

### Custo estimado desta simulação

- **Com Qwen-Plus + Qwen-Turbo:** US$ 2 a US$ 5
- **Com Claude Haiku via OpenRouter:** US$ 8 a US$ 15

### Estratégia de execução em duas fases

1. **Fase de validação:** rode primeiro com **20 agentes** (ajusta o prompt para "aproximadamente 20") só para validar que sai sem erro e que o relatório te serve. Custo: ~US$ 0,20.
2. **Fase de produção:** só depois rode com 200 agentes para valer.

---

## 11. Operação no servidor (comandos úteis)

Todos os comandos abaixo assumem que você já está conectado via SSH:

```bash
ssh -i ~/.ssh/id_ed25519 root@187.77.234.102
```

### Container do MiroFish

```bash
# Ver logs em tempo real
docker logs -f mirofish

# Reiniciar
cd /home/deploy/mirofish && docker compose restart

# Parar
cd /home/deploy/mirofish && docker compose down

# Subir de novo
cd /home/deploy/mirofish && docker compose up -d

# Recriar (aplica mudanças no compose)
cd /home/deploy/mirofish && docker compose up -d --force-recreate

# Status
docker ps --filter name=mirofish

# Consumo de recursos
docker stats --no-stream mirofish
```

### Atualizar variáveis de ambiente

```bash
nano /home/deploy/mirofish/.env

# Trocar modelo LLM rapidamente sem editor (ex: para qwen-turbo)
sed -i 's/LLM_MODEL_NAME=.*/LLM_MODEL_NAME=qwen-turbo/' /home/deploy/mirofish/.env

# Aplicar mudanças
cd /home/deploy/mirofish && docker compose restart
```

### Atualizar tradução / código do fork

```bash
cd /home/deploy/mirofish/src
git pull origin main
cd /home/deploy/mirofish
docker compose restart
```

### Atualizar imagem (rebuild)

```bash
cd /home/deploy/mirofish/src
git pull origin main
docker build -t mirofish-pt:local .
cd /home/deploy/mirofish
docker compose up -d --force-recreate
```

> **Atenção:** o build consome ~5 GB de disco temporariamente. Verifique espaço com `df -h /` antes.

### Limpeza de imagens Docker antigas

```bash
docker image prune -a   # remove imagens não usadas
df -h /                  # confere espaço liberado
```

### Diagnóstico do Nginx

```bash
# Testar config
docker exec edm_nginx nginx -t

# Recarregar config sem downtime
docker exec edm_nginx nginx -s reload

# Ver vhost atual
cat /etc/nginx/nginx.conf

# Backup antes de editar
cp /etc/nginx/nginx.conf /etc/nginx/nginx.conf.bak
```

### Renovação manual do certificado SSL

```bash
# Renovação automática já está agendada via systemd timer
certbot renew --dry-run    # simula sem aplicar
certbot renew              # aplica de verdade
```

### Diagnóstico geral

```bash
# Espaço em disco
df -h /

# Memória
free -h

# CPUs
nproc

# Processos pesados
htop   # se instalado, senão: top

# Portas em uso
ss -tlnp
```

---

## 12. Observações Avançadas

### Modo dev vs produção

A imagem oficial do MiroFish (e a nossa custom `mirofish-pt:local`) roda **Vite + Flask em modo dev** (com debug, hot reload, SSE). Para o caso de uso atual (interno, baixo tráfego, dev experience importa) está adequado. Para uso em produção pesada (muitos usuários simultâneos, performance crítica), o ideal seria:

- Build estático do Vue (`npm run build` produz arquivos `.js`/`.css` minificados)
- Servir os estáticos pelo Nginx ou Caddy
- Backend Flask rodando atrás de **Gunicorn** ou **Uvicorn** com workers
- Desligar `FLASK_DEBUG=False` (já contemplado nas variáveis)

Isso exigiria customizar o `Dockerfile` da imagem.

### Licença AGPL-3.0 e suas implicações

O MiroFish é licenciado sob **AGPL-3.0** (GNU Affero General Public License v3). Isso tem implicações práticas:

- **Você pode usar comercialmente** (não precisa pagar)
- **Pode modificar o código** (e nós já modificamos para PT-BR)
- **Mas:** se você expor o serviço publicamente para terceiros, é tecnicamente obrigado a **disponibilizar o código modificado** (incluindo nossas customizações) — basta manter o link do fork público no GitHub
- Como nosso fork `douglasemid/MiroFish` já está público, essa obrigação está cumprida automaticamente

### Sistema de WebSocket / SSE

O frontend Vue se conecta ao backend Flask via:
- **HTTP REST** (`axios`) para criar/listar simulações, upload de arquivos, comandos
- **Server-Sent Events (SSE)** para receber updates em tempo real durante a simulação (rodadas, ações dos agentes, progresso do relatório)

Não há Socket.IO ou WebSocket bidirecional — só o canal SSE unidirecional do servidor → cliente.

### Sistema de filas e tarefas assíncronas

O backend Flask **não usa Celery, RQ ou Redis Queue**. Em vez disso:
- Tarefas longas (build do grafo, geração de personas, simulação, geração de relatório) rodam em **threads internas do Flask** com `threaded=True`
- O frontend faz **polling** em endpoints `/api/.../status` para acompanhar progresso
- Estado das tarefas é mantido em memória do processo Python (`_thread_local`)

**Implicação:** se o container `mirofish` reiniciar no meio de uma simulação, **a simulação é perdida** (não há persistência da fila). Você precisa recriar.

### Persistência de dados

| Dado | Onde fica | Persistente? |
|---|---|---|
| Uploads de PDF/MD/TXT | `./backend/uploads/` (volume bind) | ✅ Sim, sobrevive a restart |
| Estado das simulações em andamento | Memória do processo Python | ❌ Não, perdido em restart |
| Memória dos agentes | **Zep Cloud** (externo) | ✅ Sim, na infraestrutura do Zep |
| Logs do container | `docker logs mirofish` | Limitado pelo Docker (rotação automática) |
| Relatórios gerados | `./backend/uploads/reports/<id>/` | ✅ Sim, sobrevive a restart |

### Estrutura interna do backend Flask

```
backend/
├── app/
│   ├── __init__.py            # create_app() — bootstrap do Flask
│   ├── config.py              # Config class — variáveis de ambiente
│   ├── api/                   # Blueprints REST: graph, simulation, report, agent, etc
│   ├── models/                # Modelos pydantic
│   ├── services/              # Lógica de negócio: ZepToolsService, ReportAgent, etc
│   └── utils/
│       └── locale.py          # Sistema i18n (load de pt.json e função t())
├── pyproject.toml
├── requirements.txt
├── run.py                     # Entry point — Config.validate() + app.run()
└── uv.lock
```

### Estrutura interna do frontend Vue

```
frontend/
├── index.html                 # HTML estático com lang=pt
├── public/                    # Assets servidos no root URL
│   ├── icon.png
│   └── documentacao-emidgroup.html   # Esta documentação (após o deploy)
├── src/
│   ├── main.js                # Bootstrap do Vue + i18n + router
│   ├── App.vue
│   ├── i18n/
│   │   └── index.js           # createI18n com locale='pt' por padrão
│   ├── router/
│   ├── store/
│   ├── api/
│   │   └── index.js           # axios com interceptor Accept-Language
│   ├── views/
│   │   └── Home.vue           # Página inicial com navbar
│   ├── components/
│   │   ├── LanguageSwitcher.vue
│   │   ├── Step1Graph.vue
│   │   ├── Step2EnvSetup.vue
│   │   ├── Step3Simulation.vue
│   │   ├── Step4Report.vue
│   │   └── Step5Interaction.vue
│   └── assets/
├── package.json
└── vite.config.js
```

### Como o Nginx encaminha o tráfego

A pilha funciona assim:

```
Browser → https://miro.emidgroup.com.br
         ↓ (TLS handshake com cert Let's Encrypt)
Nginx (container) — porta 443
         ↓ (server block para miro.emidgroup.com.br)
proxy_pass http://mirofish:3000/        ← frontend Vite
proxy_pass http://mirofish:5001/api/    ← backend Flask
         ↓
Container `mirofish` na rede Docker interna
```

O Nginx usa **resolver Docker interno** (`127.0.0.11`) para resolver lazy DNS dos containers, então funciona mesmo se o `mirofish` for recriado.

O Host header é enviado como `localhost` para o frontend (para o Vite aceitar via `allowedHosts`), e o host real chega no backend via `X-Forwarded-Host`.

### Tradução incompleta — pontos não traduzidos

- **Logs internos do backend Python** (ex: `MiroFish Backend 启动中...`) ainda aparecem em chinês porque são `print()` hardcoded no código fonte. Não afetam a UI do usuário.
- **Conteúdo dos PDFs/MDs** que você upload é processado no idioma original — se você subir um PDF em inglês, as personas vão pensar em inglês mesmo (mas vão **responder em PT-BR** por causa do `llmInstruction`).
- **Comentários de código** dentro dos arquivos JS/Vue/Python permanecem em chinês/inglês — irrelevante para o usuário final.

### Troubleshooting comum

#### "Container mirofish não inicia / crashloop"

Causa mais comum: chave do LLM ou Zep inválida/ausente.

```bash
docker logs mirofish 2>&1 | head -30
# Procure por: "LLM_API_KEY 未配置" ou "ZEP_API_KEY 未配置"
```

#### "502 Bad Gateway" no navegador

O container `mirofish` parou. Verificar:
```bash
docker ps --filter name=mirofish
docker logs mirofish 2>&1 | tail -50
```

Se o container está parado, subir:
```bash
cd /home/deploy/mirofish && docker compose up -d
```

#### "Vite Blocked request: This host is not allowed"

Significa que o Host header não está sendo enviado como `localhost` pelo Nginx. Verifique no `nginx.conf` se o location `/` do server block do MiroFish tem:
```nginx
proxy_set_header Host "localhost";
proxy_set_header X-Forwarded-Host $host;
```

#### "Disco cheio (100%)"

Causa comum: imagens Docker antigas acumuladas.

```bash
df -h /
docker images
docker image prune -a
```

#### "Simulação travou no Step 3"

Sem solução automática. Provavelmente o LLM API caiu ou retornou rate limit. Restart do container e refaça.

```bash
cd /home/deploy/mirofish && docker compose restart
```

### Roadmap sugerido de evolução

1. **Curto prazo:**
   - Adicionar bind-mount do `pt.json` para facilitar updates de tradução sem rebuild
   - Configurar `OASIS_DEFAULT_MAX_ROUNDS=30` se for trabalhar com simulações mais longas
   - Desligar `FLASK_DEBUG=False`

2. **Médio prazo:**
   - Criar conta no OpenRouter e ter Claude como segunda opção
   - Configurar LLM acelerador com `qwen-turbo`
   - Implementar backup periódico da pasta `backend/uploads/`

3. **Longo prazo:**
   - Customizar o `Dockerfile` para modo produção (Vite build + Gunicorn)
   - Adicionar persistência de filas com Redis Queue ou Celery
   - Implementar autenticação na UI (hoje qualquer um com a URL acessa)
   - Painel admin web para configurar variáveis sem SSH

### Histórico de mudanças aplicadas

| Data | Mudança |
|---|---|
| 2026-04-07 | Setup inicial: pasta isolada, docker-compose, SSL, vhost Nginx, primeiro deploy com imagem oficial |
| 2026-04-07 | Tradução completa para PT-BR: 646 strings, default locale, instruction LLM, CSS para `lang="pt"`, index.html |
| 2026-04-07 | Build de imagem custom `mirofish-pt:local` (após detectar que imagem oficial estava desatualizada e não tinha `vue-i18n`) |
| 2026-04-07 | Criação desta documentação consolidada |

---

## Créditos e referências

- **MiroFish (upstream):** https://github.com/666ghj/MiroFish — projeto incubado pela Shanda Group
- **Fork EMIDGROUP:** https://github.com/douglasemid/MiroFish — com tradução PT-BR
- **OASIS (CAMEL-AI):** https://github.com/camel-ai/oasis — motor de simulação social
- **Zep Cloud:** https://www.getzep.com/ — sistema de memória de longo prazo
- **Alibaba Model Studio (Bailian):** https://modelstudio.console.alibabacloud.com/

---

**Documentação consolidada por:** Claude (Anthropic) em colaboração com Douglas EMID
**Última atualização:** Abril de 2026
