# Tetris multiplayer com sockets TCP

Projeto funcional de Tetris competitivo para dois jogadores, feito em Python.
O servidor usa a biblioteca padrão `socket`; a interface dos clientes usa
Pygame.

## Funcionalidades

- servidor TCP que forma partidas de dois jogadores;
- mesma sequência de Tetriminos nos dois clientes, usando seed e 7-bag;
- tabuleiro local e pré-visualização do tabuleiro adversário;
- ataques: Double envia 1 linha, Triple envia 2 e Tetris envia 4;
- buracos das linhas de lixo gerados pelo servidor;
- detecção de vitória, derrota e desconexão;
- protocolo textual delimitado por `\n`, com tratamento correto do fluxo TCP;
- thread separada para a rede, sem bloquear o loop do Pygame;
- testes unitários para as principais regras do motor.

## Requisitos

- Python 3.10 ou superior;
- Pygame 2.5 ou superior.

## Instalação

Na pasta do projeto:

```bash
python -m venv .venv
source .venv/bin/activate       # Linux/macOS
# .venv\\Scripts\\activate      # Windows PowerShell

python -m pip install -r requirements.txt
```

## Execução local

Abra três terminais.

Terminal 1 — servidor:

```bash
python server.py
```

Terminal 2 — jogador 1:

```bash
python client.py --name "Jogador 1"
```

Terminal 3 — jogador 2:

```bash
python client.py --name "Jogador 2"
```

O servidor inicia por padrão em `0.0.0.0:5000`, e os clientes conectam em
`127.0.0.1:5000`.

## Jogar em computadores diferentes

1. Execute o servidor em um computador acessível pela rede:

   ```bash
   python server.py --host 0.0.0.0 --port 5000
   ```

2. Descubra o IP desse computador, por exemplo `192.168.1.20`.
3. Em cada computador dos jogadores, execute:

   ```bash
   python client.py --host 192.168.1.20 --port 5000 --name "Bruno"
   ```

Se necessário, libere a porta TCP 5000 no firewall do computador servidor.

## Controles

| Tecla | Ação |
|---|---|
| `←` / `A` | mover para a esquerda |
| `→` / `D` | mover para a direita |
| `↓` / `S` | queda suave |
| `↑` / `X` | girar no sentido horário |
| `Z` | girar no sentido anti-horário |
| `Espaço` | queda rápida (hard drop) |
| `Esc` | sair |

## Protocolo

Cada mensagem é UTF-8 e termina com quebra de linha. Principais mensagens:

```text
WAITING
START|<seed>|<player_id>
ATTACK|<quantidade>
GARBAGE|<buraco_1>,<buraco_2>,...
BOARD|<200 células>
GAME_OVER
WIN|<motivo>
LOSE|<motivo>
DISCONNECT
```

O TCP é um fluxo de bytes, por isso uma chamada a `recv()` pode entregar uma
mensagem incompleta ou várias mensagens juntas. A classe `LineSocket` mantém um
buffer e só entrega mensagens completas.

## Estrutura

```text
tetris_multiplayer/
├── client.py
├── server.py
├── requirements.txt
├── tetris/
│   ├── board.py
│   ├── constants.py
│   ├── game.py
│   ├── network.py
│   ├── pieces.py
│   └── protocol.py
└── tests/
    ├── test_board.py
    ├── test_pieces.py
    └── test_protocol.py
```

## Testes

```bash
python -m unittest discover -s tests -v
```

