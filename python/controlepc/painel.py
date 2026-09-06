import tkinter as tk
import customtkinter as ctk
import time

# ==============================================================================
# CONFIGURAÇÕES DE CONEXÃO COM O ESP32
# ==============================================================================
MOCK_MODE = True  # Mudar aqui para False quando conectar ao ESP32
PORTA_SERIAL = "COM3"  # Altere para a porta do seu ESP32
BAUD_RATE = 115200

if not MOCK_MODE:
    import serial
    try:
        ser = serial.Serial(PORTA_SERIAL, BAUD_RATE, timeout=1)
        print(f"[CONEXÃO] Conectado com sucesso na porta {PORTA_SERIAL}")
    except Exception as e:
        print(f"[ERRO] Não foi possível abrir a porta {PORTA_SERIAL}. Entrando em Modo Simulação automática. Erro: {e}")
        MOCK_MODE = True

ctk.set_appearance_mode("Dark")  
ctk.set_default_color_theme("blue")  

class AppServos(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Controle de Servomotores - ESP32 (Acessibilidade Ativada)")
        # Janela um pouco mais larga para acomodar a grande barra de botões macros
        self.geometry("1100x700")
        self.resizable(True, True)

        # Configurações do projeto
        self.MIN_ANGULO = 10
        self.MAX_ANGULO = 170
        self.PASSO = 10
        self.NUM_SERVOS = 5
        
        # Configuração da Suavização: Alvos mudam gradualmente
        self.PASSO_SUAVE = 2  
        self.INTERVALO_MS = 25  

        self.valores_servos = {}
        
        # Título Principal
        self.titulo = ctk.CTkLabel(self, text="PAINEL DE CONTROLE DOS SERVOMOTORES", font=ctk.CTkFont(size=22, weight="bold"))
        self.titulo.pack(pady=20)

        # Container Principal para os Sliders
        self.frame_servos = ctk.CTkFrame(self)
        self.frame_servos.pack(pady=10, padx=20, fill="x")

        for i in range(1, self.NUM_SERVOS + 1):
            self.valores_servos[i] = tk.IntVar(value=90)

            frame_coluna = ctk.CTkFrame(self.frame_servos, fg_color="transparent")
            frame_coluna.pack(side="left", expand=True, padx=10, pady=15)

            lbl_nome = ctk.CTkLabel(frame_coluna, text=f"SERVO {i}", font=ctk.CTkFont(size=14, weight="bold"))
            lbl_nome.pack(pady=5)

            btn_mais = ctk.CTkButton(frame_coluna, text="+", width=50, height=35,
                                     font=ctk.CTkFont(size=16, weight="bold"),
                                     command=lambda s=i: self.alterar_angulo(s, self.PASSO))
            btn_mais.pack(pady=5)

            slider = ctk.CTkSlider(frame_coluna, from_=self.MIN_ANGULO, to=self.MAX_ANGULO, 
                                   orientation="vertical", height=220, width=20,
                                   variable=self.valores_servos[i],
                                   command=lambda val, s=i: self.ao_deslizar(s))
            slider.pack(pady=10)

            btn_menos = ctk.CTkButton(frame_coluna, text="-", width=50, height=35,
                                      font=ctk.CTkFont(size=16, weight="bold"),
                                      command=lambda s=i: self.alterar_angulo(s, -self.PASSO))
            btn_menos.pack(pady=5)

            lbl_graus = ctk.CTkLabel(frame_coluna, text="90°", font=ctk.CTkFont(size=14, weight="bold"))
            lbl_graus.pack(pady=5)
            
            setattr(self, f"lbl_graus_{i}", lbl_graus)

        # ==============================================================================
        # SEGUNDO NÍVEL: COMPONENTES GIGANTES DE ACESSIBILIDADE HIERÁRQUICA
        # ==============================================================================
        # Frame master para os botões do segundo nível
        self.frame_botoes = ctk.CTkFrame(self)
        self.frame_botoes.pack(pady=25, padx=20, fill="x", expand=True)

        # Configuração da fonte dos botões macros (maior para facilitar a leitura e mira)
        fonte_macro = ctk.CTkFont(size=15, weight="bold")
        ALTURA_BOTAO = 65  # Altura ampliada para criar um retângulo massivo de clique

        # Botão 1: Zerar
        self.btn_zerar = ctk.CTkButton(self.frame_botoes, text="ZERAR TODOS\n(10°)", fg_color="#d32f2f", hover_color="#b71c1c",
                                       font=fonte_macro, command=self.iniciar_zerar_todos, height=ALTURA_BOTAO)
        self.btn_zerar.pack(side="left", expand=True, fill="x", padx=10, pady=15)

        # Botão 2: Subir Tudo
        self.btn_subir_todos = ctk.CTkButton(self.frame_botoes, text="SUBIR TODOS\n(170°)", fg_color="#388e3c", hover_color="#1b5e20",
                                             font=fonte_macro, command=self.iniciar_subir_todos, height=ALTURA_BOTAO)
        self.btn_subir_todos.pack(side="left", expand=True, fill="x", padx=10, pady=15)

        # Botão 3: Posição de Pinça
        self.btn_pinça = ctk.CTkButton(self.frame_botoes, text="POSIÇÃO PINÇA\n(Servo 1 e 2)", fg_color="#1565c0", hover_color="#0d47a1",
                                       font=fonte_macro, command=self.iniciar_posicao_pinca, height=ALTURA_BOTAO)
        self.btn_pinça.pack(side="left", expand=True, fill="x", padx=10, pady=15)

        # Botão 4: Encerrar Software (Substituiu o antigo botão de rodapé)
        self.btn_sair = ctk.CTkButton(self.frame_botoes, text="ENCERRAR\nSOFTWARE", fg_color="#555555", hover_color="#333333",
                                      font=fonte_macro, command=self.quit, height=ALTURA_BOTAO)
        self.btn_sair.pack(side="left", expand=True, fill="x", padx=10, pady=15)

        self.atualizar_todos_labels()

    # ==============================================================================
    # LÓGICA E MÉTODOS DE CONTROLE
    # ==============================================================================
    def enviar_comando(self, num_servo, angulo):
        comando = f"S{num_servo}:{angulo}\n"
        if MOCK_MODE:
            print(f"[MOCK SERIAL] Enviado para o ESP32 -> {comando.strip()}")
        else:
            try:
                ser.write(comando.encode('utf-8'))
            except Exception as e:
                print(f"[ERRO SERIAL] Falha ao enviar dado: {e}")

    def atualizar_label_individual(self, num_servo):
        atual_val = self.valores_servos[num_servo].get()
        label = getattr(self, f"lbl_graus_{num_servo}")
        label.configure(text=f"{atual_val}°")

    def atualizar_todos_labels(self):
        for i in range(1, self.NUM_SERVOS + 1):
            self.atualizar_label_individual(i)

    def ao_deslizar(self, num_servo):
        val_cru = self.valores_servos[num_servo].get()
        val_arredondado = round(val_cru / self.PASSO) * self.PASSO
        val_arredondado = max(self.MIN_ANGULO, min(val_arredondado, self.MAX_ANGULO))
        
        self.valores_servos[num_servo].set(val_arredondado)
        self.atualizar_label_individual(num_servo)
        self.enviar_comando(num_servo, val_arredondado)

    def alterar_angulo(self, num_servo, mudanca):
        val_atual = self.valores_servos[num_servo].get()
        novo_val = val_atual + mudanca
        
        if novo_val < self.MIN_ANGULO:
            novo_val = self.MIN_ANGULO
        elif novo_val > self.MAX_ANGULO:
            novo_val = self.MAX_ANGULO
            
        self.valores_servos[num_servo].set(novo_val)
        self.atualizar_label_individual(num_servo)
        self.enviar_comando(num_servo, novo_val)

    def animar_servos(self, alvos_dicionario):
        continuar_animacao = False
        for num_servo, angulo_alvo in alvos_dicionario.items():
            angulo_atual = self.valores_servos[num_servo].get()
            if angulo_atual != angulo_alvo:
                continuar_animacao = True
                if angulo_atual < angulo_alvo:
                    novo_angulo = min(angulo_atual + self.PASSO_SUAVE, angulo_alvo)
                else:
                    novo_angulo = max(angulo_atual - self.PASSO_SUAVE, angulo_alvo)
                self.valores_servos[num_servo].set(novo_angulo)
                self.atualizar_label_individual(num_servo)
                self.enviar_comando(num_servo, novo_angulo)
        
        if continuar_animacao:
            self.after(self.INTERVALO_MS, lambda: self.animar_servos(alvos_dicionario))

    def iniciar_zerar_todos(self):
        print("\n--- Iniciando Movimento Suave: Zerar Todos (10°) ---")
        destinos = {i: self.MIN_ANGULO for i in range(1, self.NUM_SERVOS + 1)}
        self.animar_servos(destinos)

    def iniciar_subir_todos(self):
        print("\n--- Iniciando Movimento Suave: Subir Todos (170°) ---")
        destinos = {i: self.MAX_ANGULO for i in range(1, self.NUM_SERVOS + 1)}
        self.animar_servos(destinos)

    def iniciar_posicao_pinca(self):
        print("\n--- Iniciando Movimento Suave: Posição de Pinça (Servos 1 e 2) ---")
        destinos = {1: self.MAX_ANGULO, 2: self.MAX_ANGULO}
        self.animar_servos(destinos)

if __name__ == "__main__":
    app = AppServos()
    app.mainloop()
