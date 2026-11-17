# Órtese dinâmica ativa

Projeto do nosso TCC de Engenharia de Computação da UNIVESP, em 2026.

A ideia foi criar uma órtese para auxiliar os movimentos da mão, junto com um programa para usar o computador por movimentos do rosto. O conjunto recebeu o nome de Exocyborg e foi desenvolvido como uma prova de conceito.

## O projeto

A órtese tem um apoio na palma da mão e anéis nos dedos. O movimento vem de cinco servomotores, ligados aos dedos por cabos de aço dentro de conduítes, no sistema Bowden.

Para não colocar o peso dos motores na mão, eles ficam em uma caixa nas costas, chamada módulo Quiver. Essa caixa também reúne a eletrônica e a alimentação.

No projeto completo, o controle é baseado em ESP32, com sensores de corrente INA226, monitoramento de temperatura, comando por voz e pequenos motores de vibração para retorno tátil. A parte mecânica foi modelada em FreeCAD e Cinema 4D, e os circuitos foram trabalhados no Tinkercad e no LTspice.

## Facepoint

O Facepoint é a parte de acessibilidade. Ele usa a webcam, o OpenCV e o MediaPipe para acompanhar o rosto. A posição do nariz movimenta o ponteiro e os gestos acionam as funções do mouse.

No script, os controles são:

- Nariz: move o ponteiro.
- Piscada curta do olho identificado como esquerdo: clique esquerdo.
- Fechar o olho identificado como direito: clique direito.
- Abrir a boca: clique duplo.
- Manter o olho esquerdo fechado por 0,4 segundo: ativa a rolagem. Depois, basta mover o nariz para cima ou para baixo.
- Outra piscada curta do olho esquerdo: desativa a rolagem.

Para sair, pressione Esc com a janela da câmera selecionada. Os valores de sensibilidade e reconhecimento dos gestos ficam no próprio código e podem precisar de ajuste para cada pessoa.

## Controle da órtese

O painel em Python permite ajustar cada servo e tem botões para movimentos em conjunto: todos em 10 graus, todos em 170 graus e posição de pinça, que movimenta os servos 1 e 2.

O painel publicado se comunica com o ESP32 pela serial, a 115200 bps. Ele envia mensagens como `S1:170`, com uma quebra de linha no final, para indicar o servo e o ângulo desejado.

O firmware mantém os alvos entre 10 e 170 graus e movimenta os motores aos poucos, em passos de 1 grau a cada 15 ms. Também tem controle por teclado matricial 4x4. A arquitetura de voz, sensores e comunicação sem fio está descrita no relatório do TCC.

## Arquivos principais

- `python/nosecontrol/nosecontrol.py` - controle do mouse pelo rosto.
- `python/controlepc/painel.py` - painel dos cinco servos.
- `firmware/firmware.cpp` - código de controle do ESP32.
- `webrtc/controller.py` e `webrtc/receiver.py` - envio e recebimento de coordenadas da mão.

## Para rodar

Para usar os programas no computador, é preciso ter o Python instalado. O controle pelo rosto também precisa de uma webcam funcionando.

Baixe o projeto pelo botão verde **Code** aqui no GitHub e escolha **Download ZIP**. Depois, extraia a pasta no computador.

Abra um terminal dentro da pasta do projeto e execute este comando para instalar as bibliotecas usadas pelos programas:

```bash
python -m pip install opencv-python mediapipe pyautogui customtkinter pyserial aiortc
```

Para iniciar o controle pelo rosto, execute:

```bash
python python/nosecontrol/nosecontrol.py
```

A câmera será aberta e o programa começará a acompanhar os movimentos. Para fechar, selecione a janela da câmera e pressione Esc.

Para abrir o painel dos motores, execute em outro terminal:

```bash
python python/controlepc/painel.py
```

O painel pode ser usado sem a placa conectada. Nesse caso, dá para mexer nos controles e acompanhar os comandos no terminal, mas nenhum motor será movimentado.


Para usar os motores reais, é necessário preparar o ESP32 com o código da pasta `firmware` e ajustar a conexão no painel. Essa etapa depende da montagem eletrônica.



## Testes realizados

O trabalho inclui simulações e cálculos sobre o esforço nos cabos, consumo de corrente, temperatura e desgaste. O relatório também descreve testes de bancada com ESP32 e cinco servomotores, ainda sem acoplamento ao Bowden.

Não foram feitos testes com pacientes. A prova de conceito reúne a modelagem, o software e as avaliações de engenharia, sem validação clínica.

[Repositório do projeto](https://github.com/mediapraise/ortese_dinamica_ativa)

[Circuito no Tinkercad](https://www.tinkercad.com/things/lwHO6xz0aZh-simulacao-de-circuito-da-ortese-tcc-univesp-2026)

Mais detalhes estão no TCC: "Órtese dinâmica ativa não invasiva para suporte biomecânico de funções manuais: uma prova de conceito", UNIVESP, 2026.

