import asyncio
import json
import traceback
import cv2
import mediapipe as mp
import threading
import queue
import time
from aiortc import RTCPeerConnection, RTCConfiguration, RTCSessionDescription

# Fila para passar os frames processados da Thread para o Loop Principal Grafico
frame_queue = queue.Queue(maxsize=2)
# Canal global para a thread conseguir enviar os dados de rede
global_channel = None

def loop_da_camera():
    """Thread dedicada exclusivamente para capturar a camera e processar o MediaPipe"""
    global global_channel
    
    mp_hands = mp.solutions.hands
    mp_drawing = mp.solutions.drawing_utils 
    mp_drawing_styles = mp.solutions.drawing_styles
    
    hands = mp_hands.Hands(
        max_num_hands=1, 
        min_detection_confidence=0.7,
        min_tracking_confidence=0.5
    )
    
    # Inicializa de forma limpa
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        
    if not cap.isOpened():
        print("\n[ERRO] Nao consegui acessar a WebCam fisica de forma alguma!")
        return

    print("\n[SUCESSO] Captura de video iniciada em background.")
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            time.sleep(0.01)
            continue
            
        frame = cv2.flip(frame, 1)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(frame_rgb)
        
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # Desenha os landmarks coloridos no frame
                mp_drawing.draw_landmarks(
                    frame,
                    hand_landmarks,
                    mp_hands.HAND_CONNECTIONS,
                    mp_drawing_styles.get_default_hand_landmarks_style(),
                    mp_drawing_styles.get_default_hand_connections_style()
                )
                
                # Se o canal P2P estiver aberto, envia as coordenadas
                if global_channel and global_channel.readyState == "open":
                    dados_mao = {
                        "polegar_y": round(hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP].y, 3),   
                        "indicador_y": round(hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP].y, 3)  
                    }
                    try:
                        global_channel.send(json.dumps(dados_mao))
                    except Exception:
                        pass
        
        # Envia o frame atualizado para ser exibido na tela principal
        if not frame_queue.full():
            frame_queue.put(frame)
            
        time.sleep(0.01)
        
    cap.release()

async def main():
    global global_channel
    try:
        config = RTCConfiguration(iceServers=[])
        pc = RTCPeerConnection(configuration=config)
        channel = pc.createDataChannel("gestos_ortese", ordered=False, maxRetransmits=0)

        @channel.on("open")
        def on_open():
            global global_channel
            print("\n[SUCESSO] Canal P2P estabelecido! Ativando envio...")
            global_channel = channel

        # Cria a oferta de conexao
        offer = await pc.createOffer()
        await pc.setLocalDescription(offer)
        
        payload = {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}
        print("\n=== COPIE O TEXTO ABAIXO E COLE NO RECEPTOR ===")
        print(json.dumps(payload))
        print("==============================================\n")
        
        resposta_texto = input("Cole a ANSWER do Receptor aqui e aperte Enter: ")
        resposta_json = json.loads(resposta_texto)
        
        answer = RTCSessionDescription(sdp=resposta_json["sdp"], type=resposta_json["type"])
        await pc.setRemoteDescription(answer)
        
        print("\n[AGUARDANDO] Conexao fechada com sucesso! Inicializando tela gráfica...")
        
        # Inicia a thread da camera apos estabelecer a conexao
        t = threading.Thread(target=loop_da_camera, daemon=True)
        t.start()
        
        # LOOP GRAFICO PRINCIPAL: Roda obrigatoriamente na Thread mae do Windows
        print("[INFO] Pressione 'q' na janela de video para fechar o programa.")
        while True:
            if not frame_queue.empty():
                frame = frame_queue.get()
                cv2.imshow("MediaPipe - Linhas Cirurgicas da Mao", frame)
            
            # Atualiza os eventos de tela do Windows de forma nativa
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
            await asyncio.sleep(0.01)
            
        cv2.destroyAllWindows()
            
    except Exception as e:
        print(f"\n[ERRO CRITICO NO SCRIPT]: {e}")
        traceback.print_exc()
        input("\nPressione Enter para fechar...")

if __name__ == "__main__":
    asyncio.run(main())
