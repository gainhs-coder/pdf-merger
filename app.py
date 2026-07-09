import io

import fitz  # PyMuPDF
import streamlit as st


st.set_page_config(page_title="PDF 합치기", page_icon="📄")


def format_size(size_bytes):
    return f"{size_bytes / 1024 / 1024:.2f} MB"


def merge_and_optimize_pdfs(uploaded_files):
    merged_doc = fitz.open()

    for uploaded_file in uploaded_files:
        uploaded_file.seek(0)
        file_bytes = uploaded_file.read()
        src_doc = fitz.open(stream=file_bytes, filetype="pdf")
        merged_doc.insert_pdf(src_doc)
        src_doc.close()

    normal_output = io.BytesIO()
    merged_doc.save(normal_output)
    normal_output.seek(0)

    optimized_output = io.BytesIO()
    merged_doc.save(
        optimized_output,
        garbage=4,
        deflate=True,
        clean=True,
    )
    optimized_output.seek(0)

    merged_doc.close()

    # 최적화했는데 오히려 커지는 PDF도 있어서, 그런 경우에는 기본 병합본을 사용합니다.
    if len(optimized_output.getvalue()) < len(normal_output.getvalue()):
        return optimized_output

    return normal_output


st.title("PDF 합치기 + 용량 줄이기")
st.write("PDF 파일을 올린 순서대로 합치고, 글자 품질을 최대한 유지하면서 용량을 줄입니다.")

uploaded_files = st.file_uploader(
    "합칠 PDF 파일을 순서대로 올려주세요.",
    type=["pdf"],
    accept_multiple_files=True,
)

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
            try:
                with st.spinner("PDF를 합치고 용량을 줄이는 중입니다..."):
                    result_pdf = merge_and_optimize_pdfs(uploaded_files)

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
