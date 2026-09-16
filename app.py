import os
import json
import streamlit as st
from PIL import Image
from google import genai
from google.genai import types

st.set_page_config(page_title="Corretor de Simulados", layout="centered")
st.title("📋 Corretor Automático de Simulados")

api_key = st.text_input("Insira sua chave de API do Google GenAI:", type="password")

if api_key:
    client = genai.Client(api_key=api_key)

    st.subheader("1. Carregar Gabarito Oficial (Gabarito Chave)")
    gabarito_oficial_file = st.file_uploader("Escolha o arquivo do gabarito oficial", type=["jpg", "jpeg", "png"], key="oficial")

    st.subheader("2. Carregar Gabarito do Aluno")
    gabarito_aluno = st.file_uploader("Escolha o arquivo do gabarito do aluno", type=["jpg", "jpeg", "png"], key="aluno")

    prompt_instrucao = """
    Analise esta imagem de folha de gabarito. Extraia as marcações marcadas para cada questão.
    Retorne ESTRITAMENTE um JSON no seguinte formato (sem formatação markdown ```json):
    {"1": "A", "2": "C", "3": "D", "4": "B", "5": "E"}
    Se uma questão estiver em branco ou com rasura/dupla marcação, a questão e contada como errada.
    """

    def extrair_respostas(imagem):
        response = client.models.generate_content(
            model='gemini-2.5-flash'
            contents=[imagem, prompt_instrucao]
            config=types.GenerateContentConfig(
                response_mime_type='application/json'
            )
        )
        return json.loads(response.text)

    if st.button("Processar e Corrigir"):
        if gabarito_oficial_file and gabarito_aluno:
            with st.spinner("Processando..."):
                img_oficial = Image.open(gabarito_oficial_file)
                chave_respostas = extrair_respostas(img_oficial)
                st.success("Gabarito oficial processado com sucesso!")
                st.json(chave_respostas)

            st.divider()
            st.subheader("Resultado da Correção do Gabarito do Aluno")

            for idx, file_aluno in enumerate(gabarito_aluno):
                with st.spinner(f"Processando{file_aluno.name}..."):
                    img_aluno = Image.open(file_aluno)
                    respostas_aluno = extrair_respostas(img_aluno)

                    acertos = 0
                    total = len(chave_respostas)

                    for q, resp_certa in chave_respostas.items():
                        if respostas_aluno.get(q) == resp_certa:
                            acertos += 1

                    st.write(f"**Aluno/Arquivo:** {file_aluno.name}")
                    st.write(f"**Pontuação:** {acertos} / {total}")
                    st.divider()

        else:
            st.error("Por favor, carregue ambos os arquivos de gabarito antes de processar.")