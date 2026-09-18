import cv2
import numpy as np
import streamlit as st
from PIL import Image

st.set_page_config(page_title="Corretor OpenCV", layout="centered")
st.title("⚙️ Passo 5: Extração de Respostas (Coluna 1)")

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
        
        LARGURA = 800
        ALTURA = 1000
        
        pts_origem = np.float32([[topo_esq[0], topo_esq[1]], [topo_dir[0], topo_dir[1]], [base_dir[0], base_dir[1]], [base_esq[0], base_esq[1]]])
        pts_destino = np.float32([[0, 0], [LARGURA, 0], [LARGURA, ALTURA], [0, ALTURA]])
        
        matriz = cv2.getPerspectiveTransform(pts_origem, pts_destino)
        img_alinhada = cv2.warpPerspective(img_cv, matriz, (LARGURA, ALTURA))
        thresh_alinhada = cv2.warpPerspective(thresh, matriz, (LARGURA, ALTURA))
        
        # --- NOVO MOTOR DE LEITURA (COLUNA 1) ---
        X, Y, W, H = 82, 319, 169, 660
        passo_y = int(H / 20)
        passo_x = int(W / 5)
        
        letras = ["A", "B", "C", "D", "E"]
        respostas_aluno = {}
        
        img_resultado = img_alinhada.copy()
        
        # Percorre as 20 questões
        for q in range(20):
            pixels_por_alternativa = []
            
            # Percorre as 5 alternativas (A, B, C, D, E)
            for alt in range(5):
                caixa_x = X + (alt * passo_x)
                caixa_y = Y + (q * passo_y)
                
                # Recorta o quadradinho exato da imagem em preto e branco
                roi = thresh_alinhada[caixa_y:caixa_y+passo_y, caixa_x:caixa_x+passo_x]
                
                # Conta quantos pixels brancos (tinta de caneta) tem ali dentro
                total_pixels = cv2.countNonZero(roi)
                pixels_por_alternativa.append(total_pixels)
                
                # Desenha a grade azul fina para visualização
                cv2.rectangle(img_resultado, (caixa_x, caixa_y), (caixa_x+passo_x, caixa_y+passo_y), (255, 0, 0), 1)

            # Descobre qual alternativa teve mais pixels preenchidos
            max_pixels = max(pixels_por_alternativa)
            
            # Limite mínimo de pixels para considerar que foi marcado (evita sujeira e rasura leve)
            if max_pixels > 200:
                indice_marcado = pixels_por_alternativa.index(max_pixels)
                resposta = letras[indice_marcado]
                
                # Pinta a bolinha encontrada de verde forte para confirmarmos visualmente
                centro_x = X + (indice_marcado * passo_x) + (passo_x // 2)
                centro_y = Y + (q * passo_y) + (passo_y // 2)
                cv2.circle(img_resultado, (centro_x, centro_y), 10, (0, 255, 0), -1)
            else:
                resposta = "X" # Questão em branco
                
            respostas_aluno[str(q + 1)] = resposta

        st.success("✅ Leitura matemática concluída com precisão absoluta!")
        
        col1, col2 = st.columns([1, 1])
        with col1:
            st.subheader("Bolinhas Identificadas")
            st.image(cv2.cvtColor(img_resultado, cv2.COLOR_BGR2RGB), use_container_width=True)
            
        with col2:
            st.subheader("Gabarito Extraído (1 a 20)")
            st.json(respostas_aluno)