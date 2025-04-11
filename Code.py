import pandas as pd
import numpy as np
import torch
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from langchain.docstore.document import Document
from transformers import pipeline
import pdfplumber

# Documento organizado como lista de documentos con metadatos (base inicial)
base_documents = [
    # UNA CLUB
    Document(
        page_content="El rango de precios de Una Club es desde $4,500,000.",
        metadata={"project": "UNA CLUB", "category": "RANGO DE PRECIOS", "source": "base"}
    ),
    Document(
        page_content="Las amenidades de Una Club incluyen: dos torres y 62 pisos con 352 lujosas residencias de entre 2 y 5 habitaciones (1,785 a 10,000 pies cuadrados), playa privada con cabañas, sillas de playa y sombrillas, club para niños y adolescentes.",
        metadata={"project": "UNA CLUB", "category": "AMENIDADES", "source": "base"}
    ),
    Document(
        page_content="Una Club es desarrollado por Fortune International y Château Group.",
        metadata={"project": "UNA CLUB", "category": "DESARROLLADOR", "source": "base"}
    ),
    Document(
        page_content="La arquitectura de Una Club es un diseño único y lujoso de Arquitectónica. Incluye parque para perros, spa para mascotas, piscinas (piscina para miembros del club, piscina de torre, piscina de entrenamiento), servicio de spa concierge y áreas privadas y exclusivas.",
        metadata={"project": "UNA CLUB", "category": "ARQUITECTURA", "source": "base"}
    ),
    Document(
        page_content="El diseño de interiores de Una Club cuenta con interiores espléndidos por Patricia Anastassiadis.",
        metadata={"project": "UNA CLUB", "category": "DISEÑO DE INTERIORES", "source": "base"}
    ),
    Document(
        page_content="La fecha de entrega de Una Club es: la torre sur en 2027 y la torre norte en 2029.",
        metadata={"project": "UNA CLUB", "category": "FECHA DE ENTREGA", "source": "base"}
    ),
    Document(
        page_content="La ubicación de Una Club está en Sunny Isles Beach, en la reconocida Collins Avenue de Miami. Ofrece cercanía a lugares de entretenimiento, Aventura, Bal Harbour y el Aeropuerto de Fort Lauderdale. Incluye terraza exterior de bienestar con piscinas de inmersión, restaurante exclusivo abierto al público con bar lounge y comedor privado, terraza frente al mar, área multifuncional para eventos, club de negocios con sala de juntas John Jacob Astor, oficinas privadas, sala de conferencias, espacios de coworking, sala de trading, y entresuelo con áreas de comedor privadas, cocina de chef y área de preparación.",
        metadata={"project": "UNA CLUB", "category": "UBICACIÓN", "source": "base"}
    ),

    # BRICKELL HOME LUXURY
    Document(
        page_content="El rango de precios de Brickell Home Luxury es desde $8,000,000.",
        metadata={"project": "BRICKELL HOME LUXURY", "category": "RANGO DE PRECIOS", "source": "base"}
    ),
    Document(
        page_content="Las amenidades de Brickell Home Luxury incluyen: torre de 25 pisos con 56 residencias frente al mar de 3 a 8 habitaciones (3,300 a 12,600 pies cuadrados), restaurante exclusivo para residentes, espacios sociales curados, piscinas estilo resort, spa al aire libre y servicios junto a la piscina.",
        metadata={"project": "BRICKELL HOME LUXURY", "category": "AMENIDADES", "source": "base"}
    ),
    Document(
        page_content="Brickell Home Luxury es desarrollado por Related Group y Two Roads Development.",
        metadata={"project": "BRICKELL HOME LUXURY", "category": "DESARROLLADOR", "source": "base"}
    ),
    Document(
        page_content="La arquitectura de Brickell Home Luxury está diseñada por Skidmore, Owings & Merrill - SOM. Incluye cancha de pickleball y áreas de fitness de última generación.",
        metadata={"project": "BRICKELL HOME LUXURY", "category": "ARQUITECTURA", "source": "base"}
    ),
    Document(
        page_content="El diseño de interiores de Brickell Home Luxury cuenta con espacios únicos gracias a Rottet Studio.",
        metadata={"project": "BRICKELL HOME LUXURY", "category": "DISEÑO DE INTERIORES", "source": "base"}
    ),
    Document(
        page_content="La fecha de entrega de Brickell Home Luxury está prevista para 2026.",
        metadata={"project": "BRICKELL HOME LUXURY", "category": "FECHA DE ENTREGA", "source": "base"}
    ),
    Document(
        page_content="La ubicación de Brickell Home Luxury está en Bal Harbour, un destino elegante y exclusivo en el sur de Florida, con simuladores de realidad virtual.",
        metadata={"project": "BRICKELL HOME LUXURY", "category": "UBICACIÓN", "source": "base"}
    )
]

# Función para extraer información de un PDF y convertirla en documentos
def process_pdf(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        text = ""
        for page in pdf.pages:
            text += page.extract_text() or ""  # Aseguramos que no haya None

    print("Lectura y extracción de información de archivos PDF:")
    print(text)  # Mostramos el texto completo para depuración

    # Dividimos el texto en líneas para procesar
    lines = text.split('\n')
    pdf_documents = []
    current_project = None

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Detectamos el proyecto
        if "UNA CLUB" in line.upper():
            current_project = "UNA CLUB"
        elif "BRICKELL HOME LUXURY" in line.upper():
            current_project = "BRICKELL HOME LUXURY"

        # Solo procesamos líneas que no sean preguntas (sin "?")
        if current_project and "?" not in line:
            category = None
            line_lower = line.lower()
            if "rango de precios" in line_lower or "desde $" in line_lower or "precio" in line_lower:
                category = "RANGO DE PRECIOS"
            elif "amenidades" in line_lower:
                category = "AMENIDADES"
            elif "desarrollador" in line_lower:
                category = "DESARROLLADOR"
            elif "arquitectura" in line_lower:
                category = "ARQUITECTURA"
            elif "diseño de interiores" in line_lower:
                category = "DISEÑO DE INTERIORES"
            elif "fecha de entrega" in line_lower:
                category = "FECHA DE ENTREGA"
            elif "ubicación" in line_lower or "ubicado" in line_lower:
                category = "UBICACIÓN"

            if category:
                pdf_documents.append(Document(
                    page_content=line,
                    metadata={"project": current_project, "category": category, "source": "pdf"}
                ))

    return pdf_documents

# Configuramos el modelo de embeddings
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# Creamos el vector store para los datos base
base_vector_store = FAISS.from_documents(base_documents, embeddings)

# Solicitar y procesar un PDF (opcional)
print("Por favor, ingrese la ruta de un archivo PDF con información (opcional). Si no desea usar uno, presione Enter para continuar.")
pdf_path = input("Ruta del PDF: ")
pdf_vector_store = None
if pdf_path:
    try:
        pdf_docs = process_pdf(pdf_path)
        if pdf_docs:
            pdf_vector_store = FAISS.from_documents(pdf_docs, embeddings)
            print(f"Se han añadido {len(pdf_docs)} secciones del PDF al sistema.")
            print("Contenido extraído del PDF:")
            for doc in pdf_docs:
                print(f"- {doc.page_content} (Proyecto: {doc.metadata['project']}, Categoría: {doc.metadata['category']})")
        else:
            print("El PDF no contiene información estructurada útil (solo preguntas o texto no procesable). Usando datos base.")
    except Exception as e:
        print(f"Error al procesar el PDF: {e}. Usando datos base.")
else:
    print("No se proporcionó un PDF. Usando datos base.")

# Configuramos el modelo de Question Answering
qa_pipeline = pipeline("question-answering", model="deepset/roberta-base-squad2")

# Función para responder consultas
def answer_query(query, vector_store):
    # Determinamos el proyecto de la pregunta
    project = "UNA CLUB" if "UNA CLUB" in query.upper() else "BRICKELL HOME LUXURY" if "BRICKELL" in query.upper() else None

    # Determinamos la categoría objetivo según la pregunta
    category = None
    query_lower = query.lower()
    if "precio" in query_lower or "costo" in query_lower or "rango de precios" in query_lower:
        category = "RANGO DE PRECIOS"
    elif "amenidades" in query_lower:
        category = "AMENIDADES"
    elif "desarrollador" in query_lower:
        category = "DESARROLLADOR"
    elif "arquitectura" in query_lower:
        category = "ARQUITECTURA"
    elif "diseño de interiores" in query_lower:
        category = "DISEÑO DE INTERIORES"
    elif "fecha de entrega" in query_lower:
        category = "FECHA DE ENTREGA"
    elif "ubicación" in query_lower:
        category = "UBICACIÓN"

    # Buscamos documentos relevantes con el retriever
    retriever = vector_store.as_retriever(search_kwargs={"k": 3})
    retrieved_docs = retriever.get_relevant_documents(query)

    # Filtramos por proyecto y categoría
    if project:
        retrieved_docs = [doc for doc in retrieved_docs if doc.metadata["project"] == project]
    if category:
        retrieved_docs = [doc for doc in retrieved_docs if doc.metadata["category"] == category]

    # Combinamos el contexto
    context = "\n".join([doc.page_content for doc in retrieved_docs]) if retrieved_docs else "No se encontró información relevante."

    # Si no hay contexto relevante, devolvemos un mensaje
    if not retrieved_docs:
        return "No se encontró información relevante.", context

    # Usamos el modelo de QA para extraer la respuesta
    result = qa_pipeline(question=query, context=context)
    answer = result["answer"]
    return answer, context

# Interfaz simple para consultas
print("\nBienvenido al sistema de consultas de Million Luxury (con soporte para PDFs). Ingrese su pregunta (o 'salir' para terminar):")
while True:
    query = input("Pregunta: ")
    if query.lower() == 'salir':
        break
    # Usamos el vector_store del PDF si existe y tiene datos, sino el base
    vector_store_to_use = pdf_vector_store if pdf_vector_store else base_vector_store
    answer, context = answer_query(query, vector_store_to_use)
    print(f"Respuesta: {context}\n")