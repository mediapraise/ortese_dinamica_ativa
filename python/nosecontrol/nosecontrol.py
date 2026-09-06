# TCC UNIVESP 2026
# Controles: Mover o ponteiro (Posição do nariz), clique (Fechar os olhos meio segundo), Clique-duplo (Abrir a boca), botão direito (Fechar olho direito), Scroll (Fechar olho esquerdo)  
import cv2
import mediapipe as mp
import pyautogui
import math
import time

# --- Configurações do Sistema ---
pyautogui.FAILSAFE = False

# Dimensões da tela do monitor
LARGURA_TELA, ALTURA_TELA = pyautogui.size()

# CONFIGURAÇÕES DE CONTROLE ABSOLUTO E ÁREA DE EXCLUSÃO
FILTRO_ESTABILIZADOR = 0.15  
AREA_EXCLUSAO = 0.005  

# Caixa de alcance do rosto
CAIXA_MOVIMENTO_X = 0.12  
CAIXA_MOVIMENTO_Y = 0.10  

# Variáveis de estado do mouse e filtro
mouse_atual_x, mouse_atual_y = LARGURA_TELA // 2, ALTURA_TELA // 2
ultimo_nariz_x, ultimo_nariz_y = 0.5, 0.5

# --- Limiares de Ativação ---
EAR_ESQ_FECHADO = 0.22    
EAR_DIR_FECHADO = 0.22    
PROPORCAO_BOCA_ABERTA = 0.55 

INTERVALO_ENTRE_CLIQUES = 0.7
TEMPO_PISCADA_LONGA = 0.4  # Tempo segurando o olho fechado para ativar o Scroll

ultimo_clique_esq = 0
ultimo_clique_dir = 0
ultimo_clique_duplo = 0
tempo_inicio_fechamento_esq = 0

# Estado do Modo Scroll
modo_scroll_ativo = False

# --- Inicialização do MediaPipe ---
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(refine_landmarks=True, max_num_faces=1)

cap = cv2.VideoCapture(0)

# ÍNDICES GEOMÉTRICOS OFICIAIS MEDIAPIPE FACE MESH (Ordem de 6 pontos)
PONTO_NARIZ = 4
OLHO_ESQ = [33, 160, 158, 133, 153, 144]
OLHO_DIR = [362, 385, 387, 263, 373, 380]

BOCA_LABIO_SUP = 13
BOCA_LABIO_INF = 14
BOCA_CANTO_ESQ = 61
BOCA_CANTO_DIR = 291

def calcular_ear(olho_pontos, landmarks):
    """Calcula o Eye Aspect Ratio (Abertura do Olho) usando a geometria correta"""
    v1 = math.dist([landmarks[olho_pontos[1]].x, landmarks[olho_pontos[1]].y], 
                   [landmarks[olho_pontos[5]].x, landmarks[olho_pontos[5]].y])
    v2 = math.dist([landmarks[olho_pontos[2]].x, landmarks[olho_pontos[2]].y], 
                   [landmarks[olho_pontos[4]].x, landmarks[olho_pontos[4]].y])
    h = math.dist([landmarks[olho_pontos[0]].x, landmarks[olho_pontos[0]].y], 
                  [landmarks[olho_pontos[3]].x, landmarks[olho_pontos[3]].y])
    return (v1 + v2) / (2.0 * h) if h > 0 else 0

def calcular_abertura_boca(sup, inf, canto_e, canto_d, landmarks):
    altura = math.dist([landmarks[sup].x, landmarks[sup].y], [landmarks[inf].x, landmarks[inf].y])
    largura = math.dist([landmarks[canto_e].x, landmarks[canto_e].y], [landmarks[canto_d].x, landmarks[canto_d].y])
    return altura / largura if largura > 0 else 0

print("NoseControl pronto! Olho Esq (Longo) = Modo Scroll | Abrir a Boca = Clique Duplo.")

olho_esq_estava_aberto = True
olho_dir_estava_aberto = True
boca_estava_fechada = True

while cap.isOpened():
    success, frame = cap.read()
    if not success: break

    frame = cv2.flip(frame, 1)
    h, w, _ = frame.shape
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb_frame)
    tempo_atual = time.time()

    if results.multi_face_landmarks:
        face_landmarks = results.multi_face_landmarks[0].landmark

        # 1. MAPEAMENTO ABSOLUTO COM ANCORA ANTI-TREMORES
        nariz_x = face_landmarks[PONTO_NARIZ].x
        nariz_y = face_landmarks[PONTO_NARIZ].y

        distancia_movimento = math.dist([nariz_x, nariz_y], [ultimo_nariz_x, ultimo_nariz_y])

        if distancia_movimento > AREA_EXCLUSAO:
            ultimo_nariz_x, ultimo_nariz_y = nariz_x, nariz_y

            alvo_pixel_x = int(((nariz_x - (0.5 - CAIXA_MOVIMENTO_X)) / (2 * CAIXA_MOVIMENTO_X)) * LARGURA_TELA)
            alvo_pixel_y = int(((nariz_y - (0.5 - CAIXA_MOVIMENTO_Y)) / (2 * CAIXA_MOVIMENTO_Y)) * ALTURA_TELA)

            alvo_pixel_x = max(0, min(LARGURA_TELA, alvo_pixel_x))
            alvo_pixel_y = max(0, min(ALTURA_TELA, alvo_pixel_y))

            mouse_atual_x = mouse_atual_x + FILTRO_ESTABILIZADOR * (alvo_pixel_x - mouse_atual_x)
            mouse_atual_y = mouse_atual_y + FILTRO_ESTABILIZADOR * (alvo_pixel_y - mouse_atual_y)

            # Se o Modo Scroll estiver ativo, o nariz move o scroll em vez do ponteiro
            if modo_scroll_ativo:
                desvio_y = nariz_y - 0.5
                if abs(desvio_y) > 0.02:
                    forca_scroll = int(-desvio_y * 150)
                    pyautogui.scroll(forca_scroll)
            else:
                pyautogui.moveTo(int(mouse_atual_x), int(mouse_atual_y))

        # 2. CALCULOS INDEPENDENTES DOS OLHOS
        ear_esq = calcular_ear(OLHO_ESQ, face_landmarks)
        ear_dir = calcular_ear(OLHO_DIR, face_landmarks)

        # LÓGICA INTELIGENTE DO OLHO ESQUERDO (Clique Simples vs Modo Scroll)
        if ear_esq < EAR_ESQ_FECHADO:
            if olho_esq_estava_aberto:
                tempo_inicio_fechamento_esq = tempo_atual
                olho_esq_estava_aberto = False
            elif not modo_scroll_ativo and (tempo_atual - tempo_inicio_fechamento_esq >= TEMPO_PISCADA_LONGA):
                # Se segurou fechado por mais de 0.4s, alterna o modo scroll
                modo_scroll_ativo = True
                print("Modo Scroll: ATIVADO")
                ultimo_clique_esq = tempo_atual  # Bloqueia clique simples fantasma
        else:
            if not olho_esq_estava_aberto:
                tempo_fechado = tempo_atual - tempo_inicio_fechamento_esq
                if tempo_fechado < TEMPO_PISCADA_LONGA:
                    if modo_scroll_ativo:
                        # Se o scroll estava ativo e piscou curto, desativa o scroll
                        modo_scroll_ativo = False
                        print("Modo Scroll: DESATIVADO")
                    elif (tempo_atual - ultimo_clique_esq > INTERVALO_ENTRE_CLIQUES):
                        # Clique esquerdo normal
                        pyautogui.click(button='left')
                        ultimo_clique_esq = tempo_atual
                olho_esq_estava_aberto = True

        # LÓGICA DO CLIQUE DIREITO (OLHO DIREITO)
        if ear_dir < EAR_DIR_FECHADO:
            if olho_dir_estava_aberto and (tempo_atual - ultimo_clique_dir > INTERVALO_ENTRE_CLIQUES):
                pyautogui.click(button='right')
                ultimo_clique_dir = tempo_atual
                olho_dir_estava_aberto = False
        else:
            olho_dir_estava_aberto = True

        # 3. LÓGICA DO CLIQUE DUPLO / ENTER (BOCA)
        abertura_boca = calcular_abertura_boca(BOCA_LABIO_SUP, BOCA_LABIO_INF, BOCA_CANTO_ESQ, BOCA_CANTO_DIR, face_landmarks)

        if abertura_boca > PROPORCAO_BOCA_ABERTA:
            if boca_estava_fechada and (tempo_atual - ultimo_clique_duplo > INTERVALO_ENTRE_CLIQUES):
                pyautogui.doubleClick()  # Mude para pyautogui.press('enter') se preferir o teclado
                ultimo_clique_duplo = tempo_atual
                boca_estava_fechada = False
        else:
            boca_estava_fechada = True

        # Feedback visual na tela
        cor_status = (0, 0, 255) if modo_scroll_ativo else (0, 255, 0)
        cv2.circle(frame, (int(nariz_x * w), int(nariz_y * h)), 6, cor_status, -1)
        status_texto = "MODO SCROLL ATIVO" if modo_scroll_ativo else "MODO MOUSE"
        cv2.putText(frame, status_texto, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, cor_status, 2)
        cv2.putText(frame, f"Olho Esq: {ear_esq:.2f} | Dir: {ear_dir:.2f}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

    cv2.imshow('Software de Acessibilidade', frame)
    if cv2.waitKey(1) & 0xFF == 27: break

cap.release()
cv2.destroyAllWindows()
