#include <ESP32Servo.h>

// ==============================================================================
// CONFIGURAÇÃO DOS SERVOMOTORES
// ==============================================================================
const int NUM_SERVOS = 5;
Servo meusServos[NUM_SERVOS];

// Pinos do ESP32 - PWMs
const int pinosServos[NUM_SERVOS] = {13, 12, 14, 27, 26}; 

// Controle de ângulo (Por enquanto todos iniciam na posição central de 90°)
int angulosAtuais[NUM_SERVOS] = {90, 90, 90, 90, 90};
int angulosAlvos[NUM_SERVOS]  = {90, 90, 90, 90, 90};

const int MIN_ANGULO = 10;
const int MAX_ANGULO = 170;
const int PASSO = 10;

// Configuração de tempo para suavização do movimento
unsigned long ultimoTempoSuave = 0;
const int INTERVALO_SUAVE_MS = 15; // Velocidade da rampa de movimento

// ==============================================================================
// CONFIGURAÇÃO DO TECLADO MATRICIAL 4X4
// ==============================================================================
// Mapeamento dos pinos no ESP32 para as Linhas e Colunas do teclado
const int L_PINOS[4] = {23, 22, 21, 19}; // Pinos das Linhas (L1, L2, L3, L4)
const int C_PINOS[4] = {18, 5,  17, 16}; // Pinos das Colunas (C1, C2, C3, C4)

// Layout dos caracteres do teclado matricial 4x4
const char MAPA_TECLAS[4][4] = {
  {'1', '2', '3', 'A'},
  {'4', '5', '6', 'B'},
  {'7', '8', '9', 'C'},
  {'*', '0', '#', 'D'}
};

// TROCAR POR INCREMENTAÇÃO CONTÍNUA - Variáveis para evitar múltiplos cliques fantasmas (Debounce básico)
char ultimaTeclaPressionada = '\0';
unsigned long tempoUltimaTecla = 0;

// ==============================================================================
// MAPEAMENTO DE FUNÇÕES DO TECLADO FÍSICO
// ==============================================================================
/* ORGANIZAR MELHOR A POSIÇÃO DE USO DOS BOTÕES - Como os botões físicos vão controlar os servos:
   Teclas '1' a '5' -> Incrementa (+10°) o respectivo Servo (1 a 5)
   Teclas '6' a '0' -> Decrementa (-10°) o respectivo Servo (1 a 5)
   Tecla 'A'        -> Macro: Zerar Todos (10°)
   Tecla 'B'        -> Macro: Subir Todos (170°)
   Tecla 'C'        -> Macro: Posição de Pinça (Servo 1 e 2 em 170°)
*/

void setup() {
  // Inicializa a comunicação UART (USB) na velocidade de 115200 bps
  Serial.begin(115200);
  Serial.println("[ESP32] Sistema Iniciado. Aguardando comandos...");

  // Inicializa e anexa os servos aos seus respectivos pinos
  for (int i = 0; i < NUM_SERVOS; i++) {
    meusServos[i].attach(pinosServos[i]);
    meusServos[i].write(angulosAtuais[i]); // Move para a posição inicial de 90°
  }

  // Configura os pinos do Teclado Matricial
  for (int i = 0; i < 4; i++) {
    pinMode(L_PINOS[i], OUTPUT);
    digitalWrite(L_PINOS[i], HIGH); // Inicializa linhas em nível alto
    pinMode(C_PINOS[i], INPUT_PULLUP); // Colunas com resistor interno para evitar ruído
  }
}

void loop() {
  // 1. Verifica se chegaram ordens vindas do Python (Via UART)
  verificarComandosUART();

  // 2. Verifica se algum botão físico do Teclado 4x4 foi apertado
  verificarTecladoFisico();

  // 3. Atualiza o movimento suave dos motores em direção ao ângulo alvo atual
  atualizarMovimentoSuave();
}

// ==============================================================================
// PROCESSAMENTO DOS COMANDOS VINDOS DO PYTHON (UART)
// ==============================================================================
void verificarComandosUART() {
  if (Serial.available() > 0) {
    // Lê a linha de texto enviada pelo Python (Ex: "S1:170\n")
    String mensagem = Serial.readStringUntil('\n');
    mensagem.trim();

    // Valida se a string segue o protocolo padrão do nosso projeto
    if (mensagem.startsWith("S") && mensagem.indexOf(':') > 0) {
      int indiceDoisPontos = mensagem.indexOf(':');
      
      // Extrai o número do servo e o ângulo desejado
      int numServo = mensagem.substring(1, indiceDoisPontos).toInt();
      int anguloAlvo = mensagem.substring(indiceDoisPontos + 1).toInt();

      // Ajusta o índice para o padrão de vetor do C++ (Servo 1 vira índice 0)
      int idx = numServo - 1;

      if (idx >= 0 && idx < NUM_SERVOS) {
        // Aplica a trava de segurança de ângulos
        angulosAlvos[idx] = constrain(anguloAlvo, MIN_ANGULO, MAX_ANGULO);
        Serial.print("[UART RECONHECIDO] Servo ");
        Serial.print(numServo);
        Serial.print(" atualizado para alvo: ");
        Serial.println(angulosAlvos[idx]);
      }
    }
  }
}

// ==============================================================================
// VARREDURA E PROCESSAMENTO DO TECLADO MATRICIAL 4X4 (FÍSICO)
// ==============================================================================
void verificarTecladoFisico() {
  char teclaDetectada = '\0';

  // Varredura por colunas e linhas para identificar o clique
  for (int l = 0; l < 4; l++) {
    digitalWrite(L_PINOS[l], LOW); // Ativa a linha atual
    
    for (int c = 0; c < 4; c++) {
      if (digitalRead(C_PINOS[c]) == LOW) { // Se a coluna foi para nível baixo, o botão foi pressionado
        teclaDetectada = MAPA_TECLAS[l][c];
        break;
      }
    }
    
    digitalWrite(L_PINOS[l], HIGH); // Desativa a linha atual
    if (teclaDetectada != '\0') break;
  }

  // Sistema de controle de clique (Debounce)
  if (teclaDetectada != '\0' && (millis() - tempoUltimaTecla > 300)) {
    tempoUltimaTecla = millis();
    Serial.print("[TECLADO FISICO] Botão Pressionado: ");
    Serial.println(teclaDetectada);

    // Processa a ação baseada no botão pressionado
    switch (teclaDetectada) {
      // INCREMENTOS (+10°)
      case '1': alterarAlvoFisico(0, PASSO);  break; // Servo 1
      case '2': alterarAlvoFisico(1, PASSO);  break; // Servo 2
      case '3': alterarAlvoFisico(2, PASSO);  break; // Servo 3
      case '4': alterarAlvoFisico(3, PASSO);  break; // Servo 4
      case '5': alterarAlvoFisico(4, PASSO);  break; // Servo 5

      // DECREMENTOS (-10°)
      case '6': alterarAlvoFisico(0, -PASSO); break; // Servo 1
      case '7': alterarAlvoFisico(1, -PASSO); break; // Servo 2
      case '8': alterarAlvoFisico(2, -PASSO); break; // Servo 3
      case '9': alterarAlvoFisico(3, -PASSO); break; // Servo 4
      case '0': alterarAlvoFisico(4, -PASSO); break; // Servo 5

      // MACROS
      case 'A': // Zerar todos
        for (int i = 0; i < NUM_SERVOS; i++) angulosAlvos[i] = MIN_ANGULO;
        break;
      case 'B': // Subir todos
        for (int i = 0; i < NUM_SERVOS; i++) angulosAlvos[i] = MAX_ANGULO;
        break;
      case 'C': // Posição de Pinça (Servos 1 e 2)
        angulosAlvos[0] = MAX_ANGULO;
        angulosAlvos[1] = MAX_ANGULO;
        break;
    }
  }
}

void alterarAlvoFisico(int indexServo, int alteracao) {
  int novoAlvo = angulosAlvos[indexServo] + alteracao;
  angulosAlvos[indexServo] = constrain(novoAlvo, MIN_ANGULO, MAX_ANGULO);
}

// ==============================================================================
// SUAVIZAÇÃO DE MOVIMENTO (RAMPA DE ACELERAÇÃO)
// ==============================================================================
void atualizarMovimentoSuave() {
  if (millis() - ultimoTempoSuave >= INTERVALO_SUAVE_MS) {
    ultimoTempoSuave = millis();

    for (int i = 0; i < NUM_SERVOS; i++) {
      if (angulosAtuais[i] != angulosAlvos[i]) {
        // Se o ângulo atual for menor que o alvo, incrementa de 1 em 1 grau
        if (angulosAtuais[i] < angulosAlvos[i]) {
          angulosAtuais[i]++;
        } 
        // REVISAR AQUI - Se for maior, decrementa de 1 em 1 grau
        else {
          angulosAtuais[i]--;
        }
        // Envia o novo comando de pulso físico para mover o servo
        meusServos[i].write(angulosAtuais[i]);
      }
    }
  }
}

