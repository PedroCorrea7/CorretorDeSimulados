import cv2
import numpy as np
import streamlit as st
from PIL import Image

st.set_page_config(page_title="Corretor de Simulados", layout="wide")
st.title("Corretor de Simulados")

# --- MAPEAMENTOS GLOBAIS ---
MAP_60Q = [
    {"q_inicio": 1, "qtd": 10, "X": 50, "Y": 208, "W": 146, "H": 500},
    {"q_inicio": 11, "qtd": 10, "X": 248, "Y": 208, "W": 146, "H": 500},
    {"q_inicio": 21, "qtd": 10, "X": 437, "Y": 208, "W": 146, "H": 500},
    {"q_inicio": 31, "qtd": 10, "X": 629, "Y": 208, "W": 146, "H": 500},
    {"q_inicio": 41, "qtd": 10, "X": 820, "Y": 208, "W": 146, "H": 500},
    {"q_inicio": 51, "qtd": 10, "X": 1011, "Y": 208, "W": 146, "H": 500},
]

MAP_45Q = [
    {"q_inicio": 1, "qtd": 10, "X": 51, "Y": 209, "W": 149, "H": 500},
    {"q_inicio": 11, "qtd": 10, "X": 247, "Y": 209, "W": 149, "H": 500},
    {"q_inicio": 21, "qtd": 10, "X": 436, "Y": 209, "W": 149, "H": 500},
    {"q_inicio": 31, "qtd": 10, "X": 628, "Y": 209, "W": 149, "H": 500},
    {"q_inicio": 41, "qtd": 5, "X": 819, "Y": 209, "W": 149, "H": 500},
]

def extrair_respostas(img_pil, mapa_colunas):
    img_array = np.array(img_pil.convert('RGB'))
    img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
    img_h, img_w = img_cv.shape[:2]

    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 31, 10)

    contornos, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    candidatos = []
    
    for c in contornos:
        area = cv2.contourArea(c)
        x, y, w, h = cv2.boundingRect(c)
        proporcao = float(w) / float(h)
        if 80 < area < 8000 and 0.4 < proporcao < 1.6:
            candidatos.append((x + w // 2, y + h // 2, c))

    if len(candidatos) < 4:
        st.error("Erro: Não foi possível detetar os 4 marcadores nos cantos do gabarito.")
        st.stop()

    candidatos.sort(key=lambda p: np.hypot(p[0] - 0, p[1] - 0))
    topo_esq = candidatos.pop(0)
    candidatos.sort(key=lambda p: np.hypot(p[0] - img_w, p[1] - img_h))
    base_dir = candidatos.pop(0)
    candidatos.sort(key=lambda p: np.hypot(p[0] - img_w, p[1] - 0))
    topo_dir = candidatos.pop(0)
    candidatos.sort(key=lambda p: np.hypot(p[0] - 0, p[1] - img_h))
    base_esq = candidatos.pop(0)
    
    # Formato Paisagem
    LARGURA, ALTURA = 1200, 800
    pts_origem = np.float32([[topo_esq[0], topo_esq[1]], [topo_dir[0], topo_dir[1]], [base_dir[0], base_dir[1]], [base_esq[0], base_esq[1]]])
    pts_destino = np.float32([[0, 0], [LARGURA, 0], [LARGURA, ALTURA], [0, ALTURA]])
    
    matriz = cv2.getPerspectiveTransform(pts_origem, pts_destino)
    thresh_alinhada = cv2.warpPerspective(thresh, matriz, (LARGURA, ALTURA))
    img_alinhada = cv2.warpPerspective(img_cv, matriz, (LARGURA, ALTURA))
    
    #alternativas (A, B, C, D)
    letras = ["A", "B", "C", "D"]
    respostas = {}
    
    for col in mapa_colunas:
        X, Y, W, H = col["X"], col["Y"], col["W"], col["H"]
        
        passo_y = int(H / 10)
        passo_x = int(W / 4)
        
        for q in range(col["qtd"]):
            pixels_por_alternativa = []
            
            for alt in range(4):
                caixa_x = X + (alt * passo_x)
                caixa_y = Y + (q * passo_y)
                
                # Ignora 20% das bordas para não ler as linhas da tabela ou parênteses
                margem_x = int(passo_x * 0.2)
                margem_y = int(passo_y * 0.2)
                
                roi = thresh_alinhada[caixa_y + margem_y : caixa_y + passo_y - margem_y, 
                                      caixa_x + margem_x : caixa_x + passo_x - margem_x]
                                      
                pixels_por_alternativa.append(cv2.countNonZero(roi))
                
                # Mantém o desenho da grelha normal para referência visual
                cv2.rectangle(img_alinhada, (caixa_x, caixa_y), (caixa_x+passo_x, caixa_y+passo_y), (255, 0, 0), 1)

            copia_ordenada = sorted(pixels_por_alternativa, reverse=True)
            maior_tinta = copia_ordenada[0]
            segunda_maior_tinta = copia_ordenada[1]
            
            media_vazias = sum(copia_ordenada[1:]) / 3 

            if maior_tinta < (media_vazias + 80): 
                resposta = "X"
            elif segunda_maior_tinta > (maior_tinta - 40):
                resposta = "X"
            else:
                indice_marcado = pixels_por_alternativa.index(maior_tinta)
                resposta = letras[indice_marcado]
                
                cx = X + (indice_marcado * passo_x) + (passo_x // 2)
                cy = Y + (q * passo_y) + (passo_y // 2)
                cv2.circle(img_alinhada, (cx, cy), 15, (0, 255, 0), -1)
                
            numero_questao = col["q_inicio"] + q
            respostas[str(numero_questao)] = resposta
            
    return respostas, img_alinhada

# --- INTERFACE DE USUÁRIO (STREAMLIT) ---
st.sidebar.header("Configuração da Prova")
tipo_prova = st.sidebar.radio("Selecione o modelo do gabarito:", ["60 Questões", "45 Questões"])
total_questoes = 60 if "60" in tipo_prova else 45
mapa_atual = MAP_60Q if total_questoes == 60 else MAP_45Q

# Limpa a memória do gabarito se o usuário trocar o tipo de prova
if "tipo_prova_salvo" not in st.session_state or st.session_state.tipo_prova_salvo != tipo_prova:
    st.session_state.gabarito_oficial = None
    st.session_state.tipo_prova_salvo = tipo_prova

if st.session_state.gabarito_oficial is None:
    st.subheader(f"1. Carregar Gabarito Oficial ({tipo_prova})")
    st.info("Envie a foto focada em apenas UM gabarito (metade da folha).")
    gabarito_oficial_file = st.file_uploader("Escolha a imagem do gabarito MESTRE", type=["jpg", "jpeg", "png"], key="oficial")
    
    if st.button("Ler e Memorizar Gabarito Oficial"):
        if gabarito_oficial_file:
            img_oficial = Image.open(gabarito_oficial_file)
            respostas_chave, _ = extrair_respostas(img_oficial, mapa_atual)
            st.session_state.gabarito_oficial = respostas_chave
            st.rerun()
        else:
            st.error("Carregue a imagem primeiro.")
else:
    st.success(f"✅ Gabarito Oficial ({tipo_prova}) guardado na memória!")
    if st.button("🗑️ Limpar Memória (Mudar Gabarito)"):
        st.session_state.gabarito_oficial = None
        st.rerun()

    st.divider()

    st.subheader("2. Corrigir Prova do Aluno")
    gabarito_aluno_file = st.file_uploader("Escolha a imagem da folha do aluno", type=["jpg", "jpeg", "png"], key="aluno")

    if st.button("Processar e Corrigir"):
        if gabarito_aluno_file:
            img_aluno = Image.open(gabarito_aluno_file)
            respostas_aluno, img_feedback = extrair_respostas(img_aluno, mapa_atual)
            
            chave_respostas = st.session_state.gabarito_oficial
            acertos = 0
            dados_tabela = []
            
            for q in range(1, total_questoes + 1):
                q_str = str(q)
                resp_certa = chave_respostas.get(q_str, "X")
                resp_do_aluno = respostas_aluno.get(q_str, "X")
                
                status = "✅ Acertou" if resp_do_aluno == resp_certa and resp_certa != "X" else "❌ Errou"
                if resp_do_aluno == resp_certa and resp_certa != "X":
                    acertos += 1
                
                dados_tabela.append({
                    "Questão": q_str,
                    "Oficial": resp_certa,
                    "Aluno": resp_do_aluno,
                    "Status": status
                })

            st.metric(label="Pontuação Final", value=f"{acertos} / {total_questoes}")
            
            col1, col2 = st.columns([2, 1])
            with col1:
                st.subheader("Leitura do Computador")
                st.image(cv2.cvtColor(img_feedback, cv2.COLOR_BGR2RGB), use_container_width=True)
            with col2:
                st.subheader("Boletim")
                st.dataframe(dados_tabela, use_container_width=True, height=700)
        else:
            st.error("Por favor, carregue a folha do aluno.")