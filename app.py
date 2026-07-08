import io

import fitz
import streamlit as st
from pypdf import PdfWriter


st.set_page_config(page_title="PDF 합치기", page_icon="📄")


def format_size(size_bytes):
    return f"{size_bytes / 1024 / 1024:.2f} MB"


def merge_pdfs(uploaded_files):
    writer = PdfWriter()

    for file in uploaded_files:
        file.seek(0)
        writer.append(file)

    output = io.BytesIO()
    writer.write(output)
    writer.close()
    output.seek(0)
    return output


def compress_pdf(pdf_bytes, level):
    if level == "없음":
        return pdf_bytes

    doc = fitz.open(stream=pdf_bytes.getvalue(), filetype="pdf")
    result = io.BytesIO()

    if level == "보통":
        zoom = 1.4
        jpeg_quality = 70
    else:
        zoom = 1.0
        jpeg_quality = 45

    new_doc = fitz.open()

    for page in doc:
        pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
        img_pdf = fitz.open("pdf", pix.pdfocr_tobytes(compress=True))
        new_doc.insert_pdf(img_pdf)

    new_doc.save(
        result,
        garbage=4,
        deflate=True,
        clean=True,
    )

    new_doc.close()
    doc.close()
    result.seek(0)
    return result


st.title("PDF 합치기")
st.write("PDF 파일을 올린 순서대로 합치고, 용량도 줄일 수 있습니다.")

uploaded_files = st.file_uploader(
    "합칠 PDF 파일을 순서대로 올려주세요.",
    type=["pdf"],
    accept_multiple_files=True,
)

compression_level = st.radio(
    "용량 줄이기",
    ["없음", "보통", "강하게"],
    index=1,
    horizontal=True,
)

if compression_level == "없음":
    st.caption("압축 없이 그대로 합칩니다.")
elif compression_level == "보통":
    st.caption("추천: 품질을 어느 정도 유지하면서 용량을 줄입니다.")
else:
    st.caption("용량을 더 많이 줄입니다. 대신 글자나 이미지가 조금 흐려질 수 있습니다.")

if uploaded_files:
    st.subheader("업로드된 순서")
    for index, file in enumerate(uploaded_files, start=1):
        st.write(f"{index}. {file.name} - {format_size(file.size)}")

    original_size = sum(file.size for file in uploaded_files)
    st.info(f"원본 총 용량: {format_size(original_size)}")

    if len(uploaded_files) < 2:
        st.warning("PDF 파일을 2개 이상 올려주세요.")
    else:
        if st.button("PDF 만들기"):
            try:
                with st.spinner("PDF를 만들고 있습니다..."):
                    merged_pdf = merge_pdfs(uploaded_files)
                    result_pdf = compress_pdf(merged_pdf, compression_level)

                result_size = len(result_pdf.getvalue())

                st.success("완료되었습니다.")

                col1, col2, col3 = st.columns(3)
                col1.metric("원본 용량", format_size(original_size))
                col2.metric("결과 용량", format_size(result_size))

                if original_size > 0:
                    reduction = (1 - result_size / original_size) * 100
                    col3.metric("감소율", f"{reduction:.1f}%")

                file_name = "merged.pdf" if compression_level == "없음" else "merged_compressed.pdf"

                st.download_button(
                    label="PDF 다운로드",
                    data=result_pdf,
                    file_name=file_name,
                    mime="application/pdf",
                )

            except Exception as e:
                st.error("PDF를 만드는 중 오류가 발생했습니다.")
                st.exception(e)
