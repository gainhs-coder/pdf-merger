import io

import streamlit as st
from pypdf import PdfWriter


st.set_page_config(page_title="PDF 합치기", page_icon="📄")

st.title("PDF 합치기")
st.write("PDF 파일을 올린 순서대로 그대로 합칩니다. 페이지 회전, 크기 조정, 압축 등은 하지 않습니다.")

uploaded_files = st.file_uploader(
    "합칠 PDF 파일을 순서대로 올려주세요.",
    type=["pdf"],
    accept_multiple_files=True,
)

if uploaded_files:
    st.subheader("업로드된 순서")
    for index, file in enumerate(uploaded_files, start=1):
        st.write(f"{index}. {file.name}")

    if len(uploaded_files) < 2:
        st.warning("PDF 파일을 2개 이상 올려주세요.")
    else:
        if st.button("PDF 합치기"):
            writer = PdfWriter()

            try:
                for file in uploaded_files:
                    file.seek(0)
                    writer.append(file)

                output = io.BytesIO()
                writer.write(output)
                writer.close()
                output.seek(0)

                st.success("PDF 합치기가 완료되었습니다.")

                st.download_button(
                    label="합친 PDF 다운로드",
                    data=output,
                    file_name="merged.pdf",
                    mime="application/pdf",
                )

            except Exception as e:
                st.error("PDF를 합치는 중 오류가 발생했습니다.")
                st.exception(e)
