# Escolha de Comandante em uma Frota de Drones

Trabalho da disciplina de Sistemas Distribuídos. O projeto simula uma frota de
drones que troca mensagens e precisa escolher um comandante, mesmo quando
alguns drones ou mensagens apresentam falhas.

O sistema foi desenvolvido como uma simulação local e didática. Cada drone é
representado por um objeto Python e a rede entrega as mensagens dentro do
próprio programa.

## Algoritmos implementados

### Paxos

O Paxos é usado nos cenários com falhas não bizantinas. A implementação trabalha
com consenso de valor único: o valor escolhido representa o drone comandante.
As fases simuladas são `PREPARE`, `PROMISE`, `ACCEPT_REQUEST`, `ACCEPTED` e
`DECIDE`.

A decisão ocorre quando o proponente recebe votos de uma maioria:

```text
maioria = (quantidade de drones // 2) + 1
```

Esta é uma implementação de Paxos de valor único. Propostas sucessivas usam
números crescentes, e o proponente preserva o valor previamente aceito de maior
número informado nos `PROMISE`. Não há replicação de log.

### Lamport-Shostak-Pease

O Lamport-Shostak-Pease é usado nos cenários com falhas bizantinas. O
comandante inicial envia uma proposta com `ORDER`. Os drones corretos repassam
o valor recebido usando `FORWARD`, enquanto drones bizantinos podem enviar
valores contraditórios. Cada drone correto decide por maioria.

O projeto implementa a recursão `OM(m)`. Em cada nível, os tenentes repassam o
valor recebido como novos comandantes de uma chamada `OM(m - 1)`. Empates e
mensagens ausentes usam um valor padrão configurável.

O projeto verifica a condição clássica:

```text
n >= 3f + 1
```

`n` é a quantidade total de drones e `f` é a quantidade de drones bizantinos.
Cenários fora desse limite continuam sendo executados para análise, mas não
possuem garantia teórica clássica de consenso.

## Falhas simuladas

- `nenhuma`: funcionamento normal;
- `crash`: o drone para de enviar e receber mensagens;
- `omissao`: mensagens podem ser descartadas conforme uma taxa;
- `temporizacao`: mensagens são entregues após um atraso;
- `bizantina`: o drone pode enviar candidatos diferentes para cada destino.

O argumento `--seed` torna os sorteios de omissão, atraso e comportamento
bizantino repetíveis.

## Métricas

Ao final de cada execução, o sistema apresenta:

- acordo: verifica se drones corretos que decidiram escolheram o mesmo valor;
- validade: no Paxos, verifica o valor efetivamente proposto após preservar
  aceites anteriores; no OM(m), verifica a proposta do comandante correto;
- terminação: verifica se todos os drones corretos chegaram a uma decisão;
- mensagens enviadas, recebidas, omitidas, atrasadas e contraditórias;
- tempo de execução;
- status do limite bizantino nos cenários LSP.

## Estrutura do projeto

```text
drones-consenso/
├── main.py
├── drone.py
├── mensagem.py
├── rede.py
├── falhas.py
├── paxos.py
├── lsp.py
├── simulador.py
├── metricas.py
├── exportador.py
├── graficos.py
├── relatorio.py
├── cenarios/
│   └── arquivos de configuração JSON
├── emulacao/
│   ├── mininet_topologia.py
│   ├── drone_socket.py
│   ├── controlador_emulacao.py
│   └── README.md
├── resultados/
│   └── CSVs, gráficos e relatórios gerados
├── tests/
├── requirements.txt
└── README.md
```

## Dependências

É necessário ter Python 3 instalado. O `matplotlib` é usado apenas para gerar
os gráficos.

```bash
pip install -r requirements.txt
```

Sem o `matplotlib`, as simulações, os testes, o CSV e o relatório continuam
funcionando. Apenas a geração dos gráficos mostra um aviso.

## Comandos principais

Paxos com um drone em crash:

```bash
python main.py --algoritmo paxos --drones 5 --falha crash --falhos 1 --seed 42
```

LSP com um drone bizantino:

```bash
python main.py --algoritmo lsp --drones 5 --falha bizantina --falhos 1 --seed 42
```

Executar um cenário JSON:

```bash
python main.py --cenario cenarios/paxos_5_crash.json
```

Executar todos os cenários:

```bash
python main.py --todos --seed 42
```

Gerar o CSV geral:

```bash
python main.py --todos --seed 42 --csv
```

Gerar CSV e gráficos:

```bash
python main.py --todos --seed 42 --csv --graficos
```

Gerar CSV, gráficos e relatório:

```bash
python main.py --todos --seed 42 --csv --graficos --relatorio
```

## Comando recomendado para demonstração

```bash
python main.py --todos --seed 42 --csv --graficos --relatorio
```

Esse comando executa os 11 cenários JSON em ordem, mostra a tabela geral no
terminal e gera CSV, gráficos PNG e relatório textual.

## Cenários JSON

A pasta `cenarios/` possui configurações prontas para Paxos e LSP com 5 e 10
drones. Exemplo:

```json
{
  "nome": "paxos_5_crash",
  "algoritmo": "paxos",
  "drones": 5,
  "falha": "crash",
  "falhos": 1,
  "seed": 42,
  "taxa_omissao": 0.0,
  "atraso_max": 0
}
```

Os valores do JSON substituem os argumentos manuais quando `--cenario` é
utilizado.

## Arquivos gerados

O modo completo pode criar em `resultados/`:

- `resultados_todos.csv`;
- `grafico_mensagens_enviadas.png`;
- `grafico_tempo_execucao.png`;
- `grafico_mensagens_contraditorias.png`;
- `grafico_decisoes.png`;
- `grafico_comparacao_algoritmos.png`;
- `relatorio_todos.txt`.

Execuções individuais usam nomes como `resultado_paxos_5_crash.csv` e
`relatorio_paxos_5_crash.txt`.

## Testes

Para executar a suíte completa:

```bash
python -m unittest discover -s tests -v
```

Os testes cobrem rede local, falhas, Paxos, LSP, limite bizantino, métricas,
cenários JSON, modo `--todos`, CSV, gráficos e relatório.

## Modo verbose

O argumento `--verbose` mostra as mensagens trocadas, mudanças de fase,
falhas observadas e decisões locais. Ele ajuda a acompanhar a execução passo a
passo durante a apresentação. Sem o argumento, a saída permanece resumida.

Execução manual:

```bash
python main.py --algoritmo paxos --drones 5 --falha crash --falhos 1 --seed 42 --verbose
```

Execução por cenário:

```bash
python main.py --cenario cenarios/lsp_5_bizantina_1.json --verbose
```

Todos os cenários, separados por cabeçalhos:

```bash
python main.py --todos --seed 42 --verbose
```

O verbose também pode ser combinado com CSV, gráficos e relatório:

```bash
python main.py --todos --seed 42 --csv --graficos --relatorio --verbose
```

Como `OM(m)` cresce recursivamente, cenários como 10 drones e `OM(4)` geram
muitos logs. Para apresentação passo a passo, prefira:

```bash
python main.py --cenario cenarios/lsp_5_bizantina_1.json --verbose
```

## Pontos importantes para apresentação

- Paxos foi usado para crash, omissão e temporização.
- Lamport-Shostak-Pease foi usado para falhas bizantinas.
- Acordo, validade e terminação são verificados ao final.
- Cenários fora de `n >= 3f + 1` são executados sem garantia teórica.
- A seed permite repetir os sorteios da simulação.
- CSV, gráficos e relatório ajudam a comparar os resultados.
- A implementação é uma simulação acadêmica local, não um sistema distribuído
  implantado em drones reais.

## Justificativa dos algoritmos escolhidos

- Paxos foi escolhido para falhas não bizantinas, como crash, omissão e
  temporização, porque usa quórum para escolher um único valor.
- Lamport-Shostak-Pease foi escolhido para falhas bizantinas, pois considera
  participantes que podem enviar informações incorretas ou contraditórias.
- No problema da frota, o valor decidido representa o comandante.
- Os dois algoritmos permitem comparar consenso sob modelos de falha
  diferentes, conforme solicitado no trabalho.

## Como explicar na apresentação

- Drone correto: segue o algoritmo e repassa o valor sem alterar.
- Crash: o drone para de enviar e receber.
- Omissão: uma mensagem pode ser perdida.
- Temporização: uma mensagem chega com atraso.
- Falha bizantina: o drone pode enviar valores diferentes para destinatários
  diferentes.
- Paxos não trata bizantinos porque pressupõe participantes não maliciosos.
- OM(m) repassa valores recursivamente para tolerar contradições.
- Acordo: drones corretos não decidem valores diferentes.
- Validade: a decisão respeita um valor proposto de forma válida.
- Terminação: todos os drones corretos chegam a uma decisão.
- `n >= 3f + 1`: condição clássica para tolerar `f` falhas bizantinas.
- Execução local: reúne a simulação e análise completa.
- Mininet: usa hosts separados e sockets TCP, com `coord` orquestrando as
  mensagens.

## Limitações atuais

O projeto não inclui replicação de log, Kathará ou execução em drones reais.
O LSP, o Paxos e a camada Mininet foram mantidos simples para facilitar a
explicação e a apresentação acadêmica. A emulação exige um ambiente externo
com Mininet e Open vSwitch instalados.

## Emulação com Mininet

O enunciado solicita o uso de um ambiente de emulação. A pasta `emulacao/`
atende esse requisito com uma demonstração em que cada drone é um host Mininet
separado e troca mensagens JSON por sockets TCP. O host `coord` conduz a
eleição e os resultados são gravados em `resultados/`.

A versão local continua sendo executada normalmente sem Mininet.

Paxos emulado:

```bash
sudo python3 emulacao/mininet_topologia.py --algoritmo paxos --drones 5 --falha crash --falhos 1 --seed 42
```

LSP emulado:

```bash
sudo python3 emulacao/mininet_topologia.py --algoritmo lsp --drones 5 --falha bizantina --falhos 1 --seed 42
```

O Mininet normalmente exige Linux, WSL com suporte adequado ou máquina
virtual. Consulte [emulacao/README.md](emulacao/README.md) para instalação,
execução, validação prática e limitações. O ambiente pode ser conferido com:

```bash
python3 emulacao/verificar_ambiente.py
```

Quem nunca utilizou Mininet pode seguir o guia
[emulacao/README_MININET_INICIANTE.md](emulacao/README_MININET_INICIANTE.md).
