import asyncio
import json
import logging
from aiortc import RTCPeerConnection, RTCConfiguration, RTCSessionDescription

# CONFIGURAÇÃO DO SISTEMA DE LOGS (Gera um arquivo CSV limpo e estruturado)
logging.basicConfig(
    filename='historico_movimentos.csv',
    level=logging.INFO,
    format='%(asctime)s.%(msecs)03d, %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Adiciona o cabeçalho no arquivo de log assim que o programa inicia
with open('historico_movimentos.csv', 'a') as f:
    # Se o arquivo estiver vazio, escreve os títulos das colunas
    import os
    if os.stat('historico_movimentos.csv').st_size == 0:
        f.write("Data_Hora,Polegar_Y,Indicador_Y\n")

config = RTCConfiguration(iceServers=[])
pc = RTCPeerConnection(configuration=config)

@pc.on("datachannel")
def on_datachannel(channel):
    print(f"\n[CONECTADO] Conexão direta estabelecida com o emissor!")
    print("[INFO] Todos os movimentos recebidos estão sendo gravados em 'historico_movimentos.csv'.\n")
    
    @channel.on("message")
    def on_message(message):
        try:
            dados = json.loads(message)
            polegar = dados.get('polegar_y', 0.0)
            indicador = dados.get('indicador_y', 0.0)
            
            # 1. Exibe os dados de forma fluida no terminal (substituindo a mesma linha)
            print(f"Órtese Actuators ➔ Polegar: {polegar:.3f} | Indicador: {indicador:.3f}      ", end="\r")
            
            # 2. GRAVA NO LOG: Salva os valores separados por vírgula no arquivo
            logging.info(f"{polegar},{indicador}")
            
        except Exception:
            pass

async def main():
    try:
        oferta_texto = input("Cole a OFFER do Emissor aqui e aperte Enter: ")
        oferta_json = json.loads(oferta_texto)
        
        offer = RTCSessionDescription(sdp=oferta_json["sdp"], type=oferta_json["type"])
        await pc.setRemoteDescription(offer)
        
        answer = await pc.createAnswer()
        await pc.setLocalDescription(answer)
        
        payload = {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}
        print("\n=== COPIE A ANSWER ABAIXO E COLE NO EMISSOR ===")
        print(json.dumps(payload))
        print("===============================================\n")
        
        # Mantém o script escutando e registrando os dados por tempo indeterminado
        while True:
            await asyncio.sleep(1)
            
    except Exception as e:
        print(f"\n[ERRO CRÍTICO NO RECEPTOR]: {e}")
        input("\nPressione Enter para fechar...")

if __name__ == "__main__":
    asyncio.run(main())
