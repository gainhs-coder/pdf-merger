import io

import fitz  # PyMuPDF
import streamlit as st


st.set_page_config(page_title="PDF 합치기", page_icon="📄")


def format_size(size_bytes):
    return f"{size_bytes / 1024 / 1024:.2f} MB"


def merge_pdfs(uploaded_files):
    merged_doc = fitz.open()

    for uploaded_file in uploaded_files:
        uploaded_file.seek(0)
        file_bytes = uploaded_file.read()
        src_doc = fitz.open(stream=file_bytes, filetype="pdf")
        merged_doc.insert_pdf(src_doc)
        src_doc.close()

    return merged_doc


def optimize_pdf(doc):
    output = io.BytesIO()
    doc.save(
        output,
        garbage=4,
        deflate=True,
        clean=True,
    )
    output.seek(0)
    return output


def compress_by_rasterizing(doc, level):
    if level == "보통":
        zoom = 1.35
        jpg_quality = 65
    else:
        zoom = 1.0
        jpg_quality = 45

    new_doc = fitz.open()

    for page in doc:
        rect = page.rect
        pix = page.get_pixmap(
            matrix=fitz.Matrix(zoom, zoom),
            alpha=False,
        )

        img_bytes = pix.tobytes("jpeg", jpg_quality)

        new_page = new_doc.new_page(width=rect.width, height=rect.height)
        new_page.insert_image(rect, stream=img_bytes)

    output = io.BytesIO()
    new_doc.save(
        output,
        garbage=4,
        deflate=True,
        clean=True,
    )
    new_doc.close()
    output.seek(0)
    return output


st.title("PDF 합치기 + 용량 줄이기")
st.write("PDF 파일을 올린 순서대로 합치고, 용량을 줄입니다.")

uploaded_files = st.file_uploader(
    "합칠 PDF 파일을 순서대로 올려주세요.",
    type=["pdf"],
    accept_multiple_files=True,
)

compression_level = st.radio(
    "용량 줄이기 정도",
    ["보통", "많이 줄이기"],
    index=0,
    horizontal=True,
)

if compression_level == "보통":
    st.caption("품질을 어느 정도 유지하면서 이전보다 더 적극적으로 용량을 줄입니다.")
else:
    st.caption("용량을 더 많이 줄입니다. 대신 글자나 이미지가 조금 흐려질 수 있고, 글자 검색/복사가 안 될 수 있습니다.")

if uploaded_files:
    st.subheader("업로드된 순서")
    for index, uploaded_file in enumerate(uploaded_files, start=1):
        st.write(f"{index}. {uploaded_file.name} - {format_size(uploaded_file.size)}")

    original_size = sum(uploaded_file.size for uploaded_file in uploaded_files)
    st.info(f"원본 총 용량: {format_size(original_size)}")

    if len(uploaded_files) < 2:
        st.warning("PDF 파일을 2개 이상 올려주세요.")
    else:
        if st.button("PDF 만들기"):
            merged_doc = None

            try:
                with st.spinner("PDF를 합치고 용량을 줄이는 중입니다..."):
                    merged_doc = merge_pdfs(uploaded_files)

                    optimized_pdf = optimize_pdf(merged_doc)
                    compressed_pdf = compress_by_rasterizing(merged_doc, compression_level)

                    if len(compressed_pdf.getvalue()) < len(optimized_pdf.getvalue()):
                        result_pdf = compressed_pdf
                    else:
                        result_pdf = optimized_pdf

                result_size = len(result_pdf.getvalue())

                st.success("완료되었습니다.")

                col1, col2, col3 = st.columns(3)
                col1.metric("원본 용량", format_size(original_size))
                col2.metric("결과 용량", format_size(result_size))

                if original_size > 0:
                    reduction = (1 - result_size / original_size) * 100
                    col3.metric("감소율", f"{reduction:.1f}%")

                st.download_button(
                    label="PDF 다운로드",
                    data=result_pdf,
                    file_name="merged_compressed.pdf",
                    mime="application/pdf",
                )

            except Exception as e:
                st.error("PDF를 만드는 중 오류가 발생했습니다.")
                st.write("비밀번호가 걸린 PDF이거나 손상된 PDF가 포함되어 있을 수 있습니다.")
                st.exception(e)

            finally:
                if merged_doc is not None:
                    merged_doc.close()
