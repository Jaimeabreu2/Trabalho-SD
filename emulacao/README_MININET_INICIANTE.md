# Guia de Mininet para iniciantes

Este guia mostra como executar a parte emulada do projeto em uma máquina
Linux. A versão normal do projeto continua funcionando no Windows pelo
`main.py`.

## O que é Mininet?

Mininet é uma ferramenta que cria uma rede virtual dentro do Linux. Com ele,
conseguimos criar hosts, switches e links em uma única máquina. Neste trabalho,
cada drone é representado como um host emulado. Assim, conseguimos demonstrar
que os drones trocam mensagens por uma rede, e não apenas por chamadas internas
do Python.

## Por que usamos Mininet?

O enunciado pede um ambiente de emulação. Na versão Mininet:

- `d0`, `d1`, ... representam os drones;
- `coord` representa o controlador da demonstração;
- `s1` conecta os hosts;
- os processos trocam mensagens JSON por sockets TCP.

```text
d0 \
d1  \
d2 --- s1 --- coord
d3  /
d4 /
```

A versão local executa todos os cenários, métricas, CSV, gráficos e relatório.
A versão Mininet é menor e serve para demonstrar os drones como processos em
hosts separados.

## Ambiente recomendado

A opção mais simples é usar uma máquina virtual Ubuntu. Mininet não funciona
diretamente no Windows comum.

Na VM:

1. Abra o aplicativo **Terminal**.
2. Entre na pasta do projeto:

```bash
cd caminho/do/projeto
```

3. Confirme que os arquivos aparecem:

```bash
ls
ls emulacao
```

## Instalar o Mininet

Em Ubuntu:

```bash
sudo apt update
sudo apt install mininet openvswitch-switch
```

Se necessário, inicie o Open vSwitch:

```bash
sudo systemctl enable --now openvswitch-switch
```

O `matplotlib` não é necessário para a emulação Mininet.

## Verificar o ambiente

Ainda na raiz do projeto:

```bash
python3 emulacao/verificar_ambiente.py
```

Também é possível conferir cada comando:

```bash
python3 --version
sudo mn --version
sudo ovs-vsctl --version
```

O verificador deve informar que Python, Linux, Mininet e Open vSwitch estão
disponíveis.

## Limpar execuções antigas

Antes de testar, execute:

```bash
sudo mn -c
```

O comando `sudo mn -c` limpa redes antigas do Mininet. Ele é útil quando uma
execução anterior terminou com erro ou quando algum processo ficou preso.

## Executar Paxos

```bash
sudo python3 emulacao/mininet_topologia.py --algoritmo paxos --drones 5 --falha crash --falhos 1 --seed 42
```

A saída deve mostrar:

- os hosts `d0` a `d4`;
- o switch `s1`;
- o controlador `coord`;
- as fases `PREPARE`, `ACCEPT` e `DECIDE`;
- votos `PROMISE` e `ACCEPTED`;
- o comandante escolhido.

O resultado fica em:

```text
resultados/emulacao_paxos_5_crash.txt
```

## Executar Lamport-Shostak-Pease

```bash
sudo python3 emulacao/mininet_topologia.py --algoritmo lsp --drones 5 --falha bizantina --falhos 1 --seed 42
```

A saída deve mostrar as chamadas `OM(m)`, valores recebidos, mensagens
contraditórias, acordo e status do limite `n >= 3f + 1`.

O resultado fica em:

```text
resultados/emulacao_lsp_5_bizantina.txt
```

## Executar usando cenário JSON

Paxos:

```bash
sudo python3 emulacao/mininet_topologia.py --cenario cenarios/paxos_5_crash.json
```

LSP:

```bash
sudo python3 emulacao/mininet_topologia.py --cenario cenarios/lsp_5_bizantina_1.json
```

Com cenário JSON, o nome do resultado acompanha o nome do cenário:

```text
resultados/emulacao_lsp_5_bizantina_1.txt
```

## Depois da demonstração

Limpe novamente a rede:

```bash
sudo mn -c
```

Confira os resultados:

```bash
ls resultados
cat resultados/emulacao_paxos_5_crash.txt
cat resultados/emulacao_lsp_5_bizantina_1.txt
```

Para guardar evidências da apresentação, salve:

- uma captura da topologia e dos hosts criados;
- a saída das fases Paxos ou das chamadas `OM(m)`;
- o arquivo `resultados/emulacao_*.txt`;
- a saída de `python3 emulacao/verificar_ambiente.py`.

Não marque a validação como concluída se a mensagem de ausência do Mininet
aparecer.

## Problemas comuns

### Erro: `mn: command not found`

O Mininet não está instalado ou o comando não está sendo executado em uma
máquina Linux adequada.

```bash
sudo apt install mininet
```

### Erro: `ovs-vsctl: command not found`

O Open vSwitch não está instalado.

```bash
sudo apt install openvswitch-switch
```

### Erro de permissão

Execute a topologia com `sudo`.

### Erro de porta ocupada ou processo preso

```bash
sudo mn -c
```

Depois, tente novamente.

### Open vSwitch parado

```bash
sudo systemctl restart openvswitch-switch
sudo mn -c
```

### Drone não ficou pronto

Limpe o Mininet, confirme que está na raiz do projeto e repita o comando.

## Limitação importante

A versão Mininet é uma camada de emulação didática. Ela demonstra drones como
hosts separados trocando mensagens via sockets TCP. A lógica principal e a
análise completa dos cenários continuam na versão local do projeto. A emulação
foi adicionada para atender ao requisito de ambiente emulado do trabalho.
