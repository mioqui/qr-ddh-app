# Requiere: pip install streamlit pandas qrcode pillow pymupdf

import streamlit as st
import pandas as pd
import qrcode
import fitz  # PyMuPDF
import os
import json
from PIL import Image, ImageDraw, ImageFont
import tempfile
import zipfile

st.title("🧭 Generador de QR + Inserción en PDFs (DDH)")

# Subida de archivos
uploaded_excel = st.file_uploader("📥 Sube tu archivo Excel con la lista de proyectos", type=["xlsx"])
uploaded_pdfs = st.file_uploader("📎 Sube los PDFs correspondientes (Layout)", type=["pdf"], accept_multiple_files=True)

if uploaded_excel and uploaded_pdfs:
    df = pd.read_excel(uploaded_excel)
    st.success("✅ Archivo Excel cargado correctamente.")
    st.dataframe(df)

    if st.button("🚀 Generar QRs e Insertar en PDFs"):
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = os.path.join(temp_dir, "output")
            os.makedirs(output_dir, exist_ok=True)

            archivos_zip = []

            # Fuente para texto grande
            try:
                fuente = ImageFont.truetype("Arial.ttf", 28)
            except:
                fuente = ImageFont.load_default()

            pdf_dict = {os.path.basename(pdf.name): pdf for pdf in uploaded_pdfs}

            for i, row in df.iterrows():
                cod = str(row["Cod Sondaje"]).strip()
                pdf_name = f"{cod} Layout.pdf"

                if pdf_name not in pdf_dict:
                    st.warning(f"⚠️ PDF no encontrado para: {cod}")
                    continue

                # Crear contenido QR
                data = {
                    "EE": row["EE"], "Cod Sondaje": row["Cod Sondaje"], "Tipo": row["Tipo"],
                    "Target": row["Target"], "Veta": row["Veta"], "Nivel": row["Nivel"],
                    "Labor": row["Labor"], "Categoria": row["Categoria"],
                    "Inclinacion": row["Inclinacion"], "Azimut": row["Azimut"]
                }
                json_str = json.dumps(data, ensure_ascii=False)
                qr = qrcode.make(json_str)
                qr_img = qr.convert("RGB")

                # Texto visible encima del QR
                texto = f"{row['Cod Sondaje']} | {row['Veta']} | {row['Nivel']}"
                draw_temp = ImageDraw.Draw(Image.new("RGB", (1, 1)))
                bbox = draw_temp.textbbox((0, 0), texto, font=fuente)
                ancho_texto = bbox[2] - bbox[0]
                alto_texto = bbox[3] - bbox[1]

                # Nueva imagen con espacio arriba para el texto
                ancho_qr, alto_qr = qr_img.size
                altura_total = alto_qr + alto_texto + 40
                img_final = Image.new("RGB", (ancho_qr, altura_total), "white")
                draw = ImageDraw.Draw(img_final)

                # Dibujar texto centrado arriba
                x_texto = (ancho_qr - ancho_texto) // 2
                draw.text((x_texto, 10), texto, fill="black", font=fuente)

                # Pegar QR debajo del texto
                img_final.paste(qr_img, (0, alto_texto + 20))

                # Guardar imagen
                img_path = os.path.join(output_dir, f"{cod}.png")
                img_final.save(img_path)
                archivos_zip.append(img_path)

                # Guardar PDF temporalmente
                pdf_bytes = pdf_dict[pdf_name].read()
                pdf_path = os.path.join(output_dir, pdf_name)
                with open(pdf_path, "wb") as f:
                    f.write(pdf_bytes)

                # Insertar QR en PDF
                doc = fitz.open(pdf_path)
                page = doc[0]
                rect = fitz.Rect(600, 870, 750, 1030)  # Ajustar si es necesario
                page.insert_image(rect, filename=img_path)

                final_pdf_path = os.path.join(output_dir, f"{cod} Layout QR.pdf")
                doc.save(final_pdf_path)
                doc.close()
                archivos_zip.append(final_pdf_path)

            # Crear ZIP
            zip_path = os.path.join(temp_dir, "QRs_y_PDFs.zip")
            with zipfile.ZipFile(zip_path, "w") as zipf:
                for archivo in archivos_zip:
                    zipf.write(archivo, os.path.basename(archivo))

            with open(zip_path, "rb") as f:
                st.download_button("📦 Descargar todos los QRs y PDFs en ZIP", f, file_name="QRs_y_PDFs.zip", mime="application/zip")