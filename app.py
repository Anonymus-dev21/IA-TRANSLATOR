import streamlit as st
import os
from dotenv import load_dotenv
import google.generativeai as genai
from langdetect import detect


load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")


if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)
else:
    st.error("⚠️ No se encontró la API Key en el archivo .env.")


def update_translation():
   
    if st.session_state.get("texto") and st.session_state.get("idioma_destino"):
        try:
            idioma_origen = detect(st.session_state.texto)
            prompt = (
                f"Traduce este texto al {st.session_state.idioma_destino}. "
                f"Debe ser claro, preciso y corto, no debes explicar en la respuesta lo que el texto expresa, solo traducirlo explicitamente al idioma que se lo requiere y no  especificar el tema por escrito, solo traducirlo. Manteniendo el contexto: '{st.session_state.contexto}'. "
                f"Tono: {st.session_state.tono}. Texto: {st.session_state.texto}"
            )
            model = genai.GenerativeModel("gemini-1.5-pro-latest")
            response = model.generate_content(prompt)
            st.session_state.traduccion = response.text
        except Exception as e:
            st.session_state.traduccion = f"❌ Error al traducir: {e}"

# Interfaz estilo Google Translate / DeepL
st.title("🔄 Traductor Inteligente")
st.write("Traducción rápida y precisa con contexto.")

col1, col2 = st.columns(2)

# Columna 1 (entrada y contexto) con on_change en cada widget
with col1:
    st.selectbox("Tono", ["Neutro", "Formal", "Informal", "Coloquial"],
                  key="tono", )
    st.text_area("Texto original", height=200, placeholder="Escribe o pega el texto aquí...",
                 key="texto", on_change=update_translation)
    st.text_input("Contexto del mensaje (opcional)",
                  placeholder="Ej: conversación de negocios, mensaje personal...",
                  key="contexto", )
 
    if st.button("Generar Traducción"):
        update_translation()

with col2:
    st.selectbox("Idioma de destino", ["Español", "Inglés", "Francés", "Alemán", "Coreano", "Italiano", "Portugués", "Chino", "Japonés", "Ruso", "Árabe", "Hindi"],
                  key="idioma_destino", on_change=update_translation)
    st.text_area("Traducción", value=st.session_state.get('traduccion', ''),
                 height=200, disabled=True, placeholder="La traducción aparecerá aquí...")

def es_relacionado_con_lenguaje(texto):
    palabras_clave = [
        "idioma", "traduce", "traducción", "traduccion", "traducir", "traducido" "lingüística",
        "lenguaje", "gramática", "vocabulario", "traduzcas",  "significado",
        "pronunciación", "dialecto", "semántica", "sintaxis",
        "comunicación", "escritura", "lectura", "interpretación",
        "palabra", "frase", "oración", "texto", "diccionario",
        "traductor", "intérprete", "bilingüe", "multilingüe",
        "idiomas", "extranjero", "nativo", "aprender", "enseñar",
        "hablar", "escribir", "leer", "entender", "comprender",
    ]
    return any(palabra in texto.lower() for palabra in palabras_clave)

# Función para generar el prompt de chat incluyendo el historial y el nuevo mensaje
def generar_contexto_chat(nuevo_mensaje):
    contexto = ""
    for msg in st.session_state.messages:
        rol = "Usuario" if msg["role"] == "user" else "Asistente"
        contexto += f"{rol}: {msg['content']}\n"
    contexto += f"Usuario: {nuevo_mensaje}\nAsistente:"
    return contexto

# Chat en tiempo real
st.subheader("💬 Chat en tiempo real")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Mostrar historial de mensajes
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Escribe tu mensaje..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Si es el primer mensaje de la conversación, se aplica el filtro de temas lingüísticos.
    if len(st.session_state.messages) == 1:
        if not es_relacionado_con_lenguaje(prompt):
            respuesta_no = "Lo siento, solo respondo consultas relacionadas con el lenguaje."
            st.session_state.messages.append({"role": "assistant", "content": respuesta_no})
            with st.chat_message("assistant"):
                st.markdown(respuesta_no)
        else:
            prompt_contexto = generar_contexto_chat(prompt)
            try:
                model = genai.GenerativeModel("gemini-1.5-pro-latest")
                response = model.generate_content(prompt_contexto)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
                with st.chat_message("assistant"):
                    st.markdown(response.text)
            except Exception as e:
                st.error(f"❌ Error al generar respuesta: {e}")
    else:
        # Si ya hay un historial, se usa el contexto completo sin aplicar nuevamente el filtro.
        prompt_contexto = generar_contexto_chat("Solo Responde si consideras que esta relacionado con un agente del lenguaje y la traducción, sino responde un mensaje generico como que no es posible porque solo sos un agente del lenguaje. Si consideras que el mensaje es apto para un agente del lenguaje hace lo siguiente:  " + prompt)
        try:
            model = genai.GenerativeModel("gemini-1.5-pro-latest")
            response = model.generate_content(prompt_contexto)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            with st.chat_message("assistant"):
                st.markdown(response.text)
        except Exception as e:
            st.error(f"❌ Error al generar respuesta: {e}")