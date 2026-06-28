# Emulação com Mininet

A versão principal do projeto executa os algoritmos em uma simulação local. A
pasta `emulacao/` adiciona uma demonstração com Mininet, onde os drones são
representados como hosts separados e trocam mensagens por sockets. Essa etapa
atende ao requisito de uso de ambiente de emulação do trabalho.

## Estrutura

- `mininet_topologia.py`: cria os hosts, o switch e inicia os processos;
- `drone_socket.py`: servidor TCP JSON executado por cada drone;
- `controlador_emulacao.py`: conduz as fases didáticas e reúne as respostas.

A topologia possui um switch, hosts `d0`, `d1`, ... e o host `coord`, que atua
como controlador da demonstração.

```text
d0 \
d1  \
d2 --- s1 --- coord
d3  /
d4 /
```

Para uma explicação passo a passo, consulte
[README_MININET_INICIANTE.md](README_MININET_INICIANTE.md).

## Ambiente necessário

O Mininet normalmente deve ser executado em Linux, WSL com suporte adequado ou
uma máquina virtual. Uma instalação comum em Ubuntu é:

```bash
sudo apt update
sudo apt install mininet openvswitch-switch
```

Antes da primeira execução, verifique o ambiente:

```bash
python3 emulacao/verificar_ambiente.py
python3 --version
sudo mn --version
sudo ovs-vsctl --version
```

## Comandos

Paxos com um drone em crash:

```bash
sudo python3 emulacao/mininet_topologia.py --algoritmo paxos --drones 5 --falha crash --falhos 1 --seed 42
```

LSP com um drone bizantino:

```bash
sudo python3 emulacao/mininet_topologia.py --algoritmo lsp --drones 5 --falha bizantina --falhos 1 --seed 42
```

Também é possível usar os cenários JSON:

```bash
sudo python3 emulacao/mininet_topologia.py --cenario cenarios/paxos_5_crash.json
sudo python3 emulacao/mininet_topologia.py --cenario cenarios/lsp_5_bizantina_1.json
```

## Como funciona

Cada drone abre um servidor TCP e recebe mensagens JSON. O controlador envia
`PREPARE`, `ACCEPT_REQUEST` e `DECIDE` no Paxos. No LSP, envia `ORDER` e pede
aos drones que produzam os repasses `FORWARD`.

As falhas são demonstradas de forma simples:

- crash: o drone não responde;
- omissão: algumas respostas são descartadas;
- temporização: a resposta sofre atraso;
- bizantina: o candidato pode ser alterado conforme o destinatário.

Ao final, um arquivo `emulacao_<cenario>.txt` é salvo em `resultados/`.

### Fluxo Paxos

1. `coord` envia `PREPARE` numerado por TCP;
2. drones disponíveis respondem `PROMISE` com eventual aceite anterior;
3. com maioria, `coord` preserva o aceite de maior número e envia
   `ACCEPT_REQUEST`;
4. os drones respondem `ACCEPTED`;
5. com nova maioria, `coord` envia `DECIDE`.

### Fluxo LSP

1. `coord` inicia `OM(m)` com `ORDER`;
2. cada tenente se torna comandante em uma chamada `OM(m - 1)`;
3. os repasses `FORWARD` carregam o caminho para evitar ciclos;
4. o drone bizantino pode alterar o candidato por destinatário;
5. empate ou ausência usa o valor padrão;
6. o controlador reúne os valores e calcula a maioria dos drones corretos.

## Resultados esperados

O terminal mostra topologia, ambiente, mensagens, maiorias e decisão. O arquivo
TXT registra data, algoritmo, falha, comandante, acordo, validade, terminação e
quantidade de mensagens.

## Diferença para a versão local

A versão local concentra a simulação e todas as métricas em um processo. A
versão Mininet usa processos e hosts separados, com comunicação TCP real, mas
mantém um fluxo menor e voltado à demonstração.

## Limitações

- o controlador coordena as fases e não implementa descoberta de nós;
- cada conexão transporta uma mensagem JSON;
- as falhas e os algoritmos foram simplificados para apresentação;
- o LSP emulado executa a recursão `OM(m)`, mas o host `coord` orquestra as
  chamadas e os drones não abrem conexões diretas entre si;
- a emulação não substitui a implementação local completa;
- Kathará não foi incluído.

A versão Mininet é uma camada de emulação didática. Ela demonstra drones como
hosts separados trocando mensagens via sockets TCP. A lógica principal e a
análise completa dos cenários continuam na versão local do projeto. A emulação
foi adicionada para atender ao requisito de ambiente emulado do trabalho.

## Validação prática

O ambiente de desenvolvimento usado nesta revisão foi Windows com Python
3.13, sem WSL, Mininet ou Open vSwitch. Por isso, os sockets e o controlador
foram validados em localhost, mas a topologia completa ainda deve ser executada
em Linux, WSL compatível ou máquina virtual.

No ambiente Linux, use esta sequência:

```bash
python3 emulacao/verificar_ambiente.py
sudo mn -c
sudo python3 emulacao/mininet_topologia.py --algoritmo paxos --drones 5 --falha crash --falhos 1 --seed 42
sudo python3 emulacao/mininet_topologia.py --algoritmo lsp --drones 5 --falha bizantina --falhos 1 --seed 42
sudo python3 emulacao/mininet_topologia.py --cenario cenarios/paxos_5_crash.json
sudo python3 emulacao/mininet_topologia.py --cenario cenarios/lsp_5_bizantina_1.json
```

Resultado esperado:

- hosts `d0` a `d4`, switch `s1` e controlador `coord` são criados;
- Paxos mostra quantidades de `PROMISE` e `ACCEPTED`;
- LSP mostra acordo e mensagens contraditórias;
- os arquivos `resultados/emulacao_*.txt` são criados;
- a mensagem `Emulação finalizada.` aparece antes de a rede ser parada.

Problemas comuns:

- porta ou processo preso: execute `sudo mn -c`;
- Open vSwitch parado: execute `sudo systemctl restart openvswitch-switch`;
- permissão negada: execute a topologia com `sudo`;
- drone não ficou pronto: confira os processos e tente novamente após
  `sudo mn -c`;
- importação não encontrada: execute o comando a partir da raiz do projeto.

Ao terminar ou após uma interrupção, limpe o Mininet:

```bash
sudo mn -c
```
