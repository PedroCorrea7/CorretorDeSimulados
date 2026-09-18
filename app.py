import cv2
import numpy as np
import streamlit as st
from PIL import Image

st.set_page_config(page_title="Calibração Final", layout="centered")
st.title("⚙️ Passo 4.2: Calibração das Colunas 2 e 3")

arquivo_gabarito = st.file_uploader("Carregar imagem do Gabarito", type=["jpg", "jpeg", "png"])

if arquivo_gabarito:
    img_pil = Image.open(arquivo_gabarito)
    img_array = np.array(img_pil.convert('RGB'))
    img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)

    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    _, thresh = cv2.threshold(blurred, 120, 255, cv2.THRESH_BINARY_INV)

    contornos, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    candidatos = []
    
    for c in contornos:
        area = cv2.contourArea(c)
        x, y, w, h = cv2.boundingRect(c)
        proporcao = float(w) / float(h)
        if 50 < area < 5000 and 0.5 < proporcao < 1.5:
            candidatos.append((x + w // 2, y + h // 2, c))

    if len(candidatos) >= 4:
        candidatos = sorted(candidatos, key=lambda p: p[0] + p[1])
        topo_esq = candidatos[0]   
        base_dir = candidatos[-1]  
        restantes = [p for p in candidatos if p not in (topo_esq, base_dir)]
        restantes = sorted(restantes, key=lambda p: p[0] - p[1])
        base_esq = restantes[0]    
        topo_dir = restantes[-1]   
        
        LARGURA, ALTURA = 800, 1000
        
        pts_origem = np.float32([[topo_esq[0], topo_esq[1]], [topo_dir[0], topo_dir[1]], [base_dir[0], base_dir[1]], [base_esq[0], base_esq[1]]])
        pts_destino = np.float32([[0, 0], [LARGURA, 0], [LARGURA, ALTURA], [0, ALTURA]])
        matriz = cv2.getPerspectiveTransform(pts_origem, pts_destino)
        img_alinhada = cv2.warpPerspective(img_cv, matriz, (LARGURA, ALTURA))
        
        st.sidebar.header("Encontre a Coluna")
        
        # Valores iniciais baseados na sua Coluna 1
        x_col = st.sidebar.slider("Posição X (Arraste para a direita)", 0, LARGURA, 300)
        y_col = st.sidebar.slider("Posição Y", 0, ALTURA, 319)
        w_col = st.sidebar.slider("Largura da Coluna", 50, 400, 169)
        h_col = st.sidebar.slider("Altura da Coluna", 100, 800, 660)
        
        img_mapeada = img_alinhada.copy()
        
        # Grade principal
        cv2.rectangle(img_mapeada, (x_col, y_col), (x_col + w_col, y_col + h_col), (0, 0, 255), 2)
        
        # Grade interna (20 questões, 5 alternativas)
        passo_y = int(h_col / 20)
        passo_x = int(w_col / 5)
        for q in range(20):
            for alt in range(5):
                caixa_x = x_col + (alt * passo_x)
                caixa_y = y_col + (q * passo_y)
                cv2.rectangle(img_mapeada, (caixa_x, caixa_y), (caixa_x + passo_x, caixa_y + passo_y), (255, 0, 0), 1)

        st.image(cv2.cvtColor(img_mapeada, cv2.COLOR_BGR2RGB), use_container_width=True)
        st.info(f"**Coordenadas da grade atual:** X={x_col}, Y={y_col}, W={w_col}, H={h_col}")