# Escolha de Comandante em uma Frota de Drones

Trabalho desenvolvido para a disciplina de **Sistemas Distribuídos**, com o objetivo de emular uma frota de drones que precisa escolher um comandante mesmo diante de falhas na comunicação ou no comportamento dos nós.

A proposta utiliza algoritmos de consenso para coordenar a decisão entre os drones. A execução principal do trabalho foi realizada em ambiente emulado com **Mininet**, no qual cada drone é representado como um host da rede, comunicando-se por meio de sockets TCP e mensagens em formato JSON.

## Objetivo do Projeto

O objetivo do projeto é demonstrar como uma frota de drones pode chegar a uma decisão comum sobre qual drone deve assumir o papel de comandante.

Para isso, foram implementados dois algoritmos de consenso:

- **Paxos**, utilizado em cenários com falhas não bizantinas;
- **Lamport-Shostak-Pease OM(m)**, utilizado em cenários com falhas bizantinas.

A decisão final representa o drone escolhido como comandante da frota.

## Ambiente de Emulação

A emulação foi realizada com **Mininet**, permitindo representar os drones como nós independentes de uma rede.

Na emulação:

- cada drone é executado como um processo associado a um host;
- a comunicação ocorre por sockets TCP;
- as mensagens são enviadas em formato JSON;
- um controlador organiza a execução dos cenários;
- os resultados são coletados ao final da eleição.

Essa abordagem permite observar o comportamento dos algoritmos em um ambiente de rede emulado, aproximando o experimento de um cenário distribuído.

## Algoritmos Implementados

### Paxos

O **Paxos** foi utilizado nos cenários com falhas não bizantinas, como:

- crash;
- omissão;
- temporização.

A implementação trabalha com consenso de valor único. Nesse caso, o valor escolhido representa o identificador do drone comandante.

As principais fases do Paxos são:

- `PREPARE`;
- `PROMISE`;
- `ACCEPT_REQUEST`;
- `ACCEPTED`;
- `DECIDE`.

A decisão ocorre quando o proponente obtém apoio de uma maioria dos drones:

```text
maioria = (quantidade de drones // 2) + 1
```

A implementação utiliza propostas numeradas e preserva o valor previamente aceito de maior número quando essa informação é retornada nas mensagens `PROMISE`.

### Lamport-Shostak-Pease OM(m)

O algoritmo **Lamport-Shostak-Pease OM(m)** foi utilizado nos cenários com falhas bizantinas.

Esse tipo de falha representa situações em que um drone pode agir de forma contraditória, enviando valores diferentes para drones diferentes.

Na implementação:

- o comandante inicial envia uma proposta;
- os drones repassam os valores recebidos;
- drones bizantinos podem enviar informações contraditórias;
- os drones corretos decidem por maioria;
- mensagens ausentes ou empates utilizam um valor padrão.

O projeto considera a condição teórica clássica para tolerância a falhas bizantinas:

```text
n >= 3f + 1
```

Onde:

- `n` é o número total de drones;
- `f` é o número de drones bizantinos.

Cenários fora desse limite podem ser executados para observação experimental, mas não possuem garantia teórica formal de consenso.

## Tipos de Falha

O projeto considera diferentes modelos de falha:

- `crash`: o drone falha e deixa de participar da comunicação;
- `omissao`: algumas mensagens podem ser descartadas;
- `temporizacao`: mensagens podem sofrer atraso;
- `bizantina`: o drone pode enviar informações contraditórias.

O uso do argumento `--seed` permite tornar os sorteios e comportamentos aleatórios mais previsíveis durante os testes e demonstrações.

## Métricas Avaliadas

Ao final da execução, o sistema apresenta métricas relacionadas ao consenso obtido.

As principais métricas são:

- comandante escolhido;
- acordo entre drones corretos;
- validade da decisão;
- terminação;
- quantidade de mensagens trocadas;
- mensagens omitidas;
- mensagens atrasadas;
- mensagens contraditórias;
- tempo de execução;
- verificação do limite bizantino.

Essas métricas ajudam a avaliar se os drones corretos chegaram à mesma decisão e se o algoritmo se comportou de acordo com o modelo de falha analisado.

## Estrutura do Projeto

```text
trabalho-final-SD/
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
│   └── arquivos de configuração dos cenários
├── emulacao/
│   ├── mininet_topologia.py
│   ├── drone_socket.py
│   ├── controlador_emulacao.py
│   ├── verificar_ambiente.py
│   └── README.md
├── resultados/
│   └── arquivos gerados pelas execuções
├── tests/
├── requirements.txt
└── README.md
```

## Dependências

É necessário ter:

- Python 3;
- Mininet;
- Open vSwitch;
- matplotlib, para geração de gráficos.

No Ubuntu/WSL, as principais dependências podem ser instaladas com:

```bash
sudo apt update
sudo apt install -y mininet openvswitch-switch python3-pip python3-matplotlib
```

Para instalar dependências Python adicionais, utilize:

```bash
pip install -r requirements.txt
```

## Verificação do Ambiente

Antes de executar a emulação, é possível verificar se o ambiente está configurado corretamente:

```bash
python3 emulacao/verificar_ambiente.py
```

Esse comando verifica itens como:

- versão do Python;
- sistema operacional;
- presença do Mininet;
- presença do Open vSwitch;
- permissão de execução.

## Execução no Mininet

Antes de executar uma nova emulação, recomenda-se limpar qualquer estado anterior do Mininet:

```bash
sudo mn -c
```

### Executar Paxos no Mininet

Exemplo com 5 drones e 1 falha por crash:

```bash
sudo python3 emulacao/mininet_topologia.py --algoritmo paxos --drones 5 --falha crash --falhos 1 --seed 42
```

Esse comando cria a topologia no Mininet, inicia os drones e executa o processo de escolha do comandante usando Paxos.

### Executar Lamport-Shostak-Pease no Mininet

Exemplo com 5 drones e 1 falha bizantina:

```bash
sudo python3 emulacao/mininet_topologia.py --algoritmo lsp --drones 5 --falha bizantina --falhos 1 --seed 42
```

Esse comando executa o algoritmo OM(m) em um cenário com comportamento bizantino.

## Comandos Recomendados para Demonstração

A sequência abaixo foi utilizada como base para validação e apresentação do projeto:

```bash
python3 emulacao/verificar_ambiente.py

sudo mn -c

sudo python3 emulacao/mininet_topologia.py --algoritmo paxos --drones 5 --falha crash --falhos 1 --seed 42

sudo mn -c

sudo python3 emulacao/mininet_topologia.py --algoritmo lsp --drones 5 --falha bizantina --falhos 1 --seed 42
```

Essa sequência demonstra:

- ambiente configurado;
- execução do Paxos com falha não bizantina;
- execução do OM(m) com falha bizantina;
- escolha de comandante;
- verificação de acordo, validade e terminação.

## Arquivos Gerados

Os resultados das execuções são salvos na pasta:

```text
resultados/
```

Exemplos de arquivos gerados:

```text
emulacao_paxos_5_crash.txt
emulacao_lsp_5_bizantina_1.txt
resultados_todos.csv
relatorio_todos.txt
```

Esses arquivos registram informações como:

- algoritmo executado;
- número de drones;
- tipo de falha;
- drone escolhido como comandante;
- mensagens trocadas;
- propriedades de consenso verificadas;
- status da execução.

## Testes

A suíte de testes pode ser executada com:

```bash
python3 -m unittest discover -s tests -v
```

Os testes verificam componentes como:

- mensagens;
- falhas;
- algoritmos de consenso;
- métricas;
- cenários;
- geração de resultados.

## Uso da Seed

O argumento `--seed` é utilizado para tornar os experimentos mais reproduzíveis.

Exemplo:

```bash
--seed 42
```

Com isso, sorteios relacionados a falhas, atrasos e comportamentos bizantinos tendem a seguir o mesmo padrão em execuções repetidas, facilitando a comparação dos resultados.

## Limitações do Escopo

O projeto possui caráter acadêmico e tem como foco demonstrar o funcionamento de algoritmos de consenso em um ambiente emulado.

A implementação concentra-se na escolha de um comandante por execução, sem abordar aspectos físicos de uma frota real, como bateria, mobilidade, sensores ou comunicação sem fio instável.

Além disso, nos cenários bizantinos, a garantia formal de consenso depende do limite:

```text
n >= 3f + 1
```

Por isso, os casos dentro desse limite são os mais adequados para demonstrar a corretude esperada do algoritmo.

## Justificativa dos Algoritmos

O **Paxos** foi escolhido por ser um algoritmo clássico de consenso tolerante a falhas não bizantinas, sendo adequado para situações em que drones podem parar, atrasar mensagens ou deixar de responder.

O **Lamport-Shostak-Pease OM(m)** foi escolhido por tratar cenários com falhas bizantinas, nos quais participantes podem enviar informações contraditórias.

Dessa forma, os dois algoritmos permitem comparar o consenso em diferentes modelos de falha, mantendo o foco no problema central do trabalho: a escolha de um comandante para a frota de drones.

## Conclusão

O projeto demonstra a escolha de comandante em uma frota de drones utilizando algoritmos de consenso em ambiente emulado com Mininet. A solução permite observar a troca de mensagens entre drones, a ocorrência de diferentes tipos de falha e a verificação de propriedades fundamentais como acordo, validade e terminação.

Com isso, o trabalho atende ao objetivo de explorar conceitos de Sistemas Distribuídos por meio de uma aplicação prática envolvendo coordenação, falhas e consenso.
