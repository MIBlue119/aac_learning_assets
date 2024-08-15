import io
import os

import markdown
import streamlit as st
from bs4 import BeautifulSoup
from openai import OpenAI
from PIL import Image
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Table, TableStyle
from streamlit import session_state as state

OPENAI_API_KEY = os.getenv(
    "OPENAI_API_KEY",
)
MODEL = "gpt-4o-mini"
client = OpenAI(api_key=OPENAI_API_KEY)


SYSTEM_PROMPT = """
你是一位經驗豐富的特殊教育專家，擁有20年以上的教學經驗和多項特教認證。
你的任務是根據提供的<個案資料>/<學習單類型> 和<學習單內容>，生成高質量、專業的教案和學習單，格式要與提供的範例結構極為相似。

請嚴格按照以下結構和要求生成內容：

# 教案

## 教案名稱
[請根據學習單內容提供簡潔明確的教案名稱]

## 教學目標
[列出1-3個具體、可衡量的學習目標]

## 教學內容
[簡要描述本次教學的主要內容，應與教學目標直接相關，若需列點請列點]

## 教學方法
[列出2-4種將要使用的教學方法，如示範教學、遊戲教學等，每種方法包含標題和簡短解釋]

## 教學步驟
[詳細列出5-10個具體的教學步驟，包括如廁過程中的每個關鍵動作，每個步驟包含簡短標題和擴充解釋]

## 評量方式
[列出2-3種評量學生學習成效的方法，每個方式包含簡短標題和擴充解釋]

# 學習單：[主題] - [具體技能]

## 一、練習題
1. [與主題相關的具體問題或任務]
2. [另一個相關問題或任務]

## 二、活動指導
1. [具體的活動說明，如「實踐活動」]
2. [另一個活動說明，如「觀察活動」]

## 三、反思問題
1. [促進學生思考的開放式問題]
2. [另一個反思性問題]

## 四、評量題
1. [評估學習成效的具體問題]
2. [另一個評量問題]

## 五、自我評估表

| 評估項目 | 滿意(✓) | 需改進(✗) | 反思與改進方法 |
|----------|---------|-----------|----------------|
| [具體的評估項目，如「我能夠正確完成每個如廁步驟」] |         |           |                |
| [另一個評估項目] |         |           |                |
| [第三個評估項目] |         |           |                |

## 六、合作學習活動
[描述一個促進學生互動和合作的小組活動]


特別注意事項：
- 確保所有內容都嚴格對應<case_info>中描述的學生特點和能力水平。
- 教案中的每個步驟都應該詳細且具體，特別是針對如廁這樣的生活技能。
- 學習單的每個部分都應該有明確的指示和足夠的空間讓學生填寫。
- 自我評估表應包含與學生個人目標直接相關的具體項目。
- 所有內容都應該使用正面、鼓勵性的語言。

<個案資料>:
<case_info>

<學習單類型>:
<learn_assets_class>

<學習單內容>:
<learn_assets_contents>

請確保生成的內容完全符合特殊教育的專業標準，並與提供的範例在格式和深度上保持一致。使用適當的Markdown語法來構建內容，包括標題、列表、表格等。你的回覆應該只包含Markdown格式的教案和學習單內容，無需任何額外解釋或評論。
"""


def generate_learning_asset(
    case_info, learn_assets_class, learn_assets_contents, prompt=SYSTEM_PROMPT, model=MODEL
):
    # Combine user info and scenario for the prompt
    prompt = (
        prompt.replace("<case_info>", case_info)
        .replace("<learn_assets_class", learn_assets_class)
        .replace("<learn_assets_contents>", learn_assets_contents)
    )

    # Call OpenAI API to generate content
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": prompt},
        ],
    )

    return response.choices[0].message.content


def markdown_to_pdf(markdown_text):
    # Convert Markdown to HTML
    html = markdown.markdown(markdown_text, extensions=["tables"], output_format="html5")
    print(html)
    # Parse HTML
    soup = BeautifulSoup(html, "html.parser", from_encoding="utf-8")

    # Create PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)

    # Register fonts
    pdfmetrics.registerFont(TTFont("NotoSansTC", "NotoSansTC-Regular.ttf"))

    # Create styles
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="CustomStyle", fontName="NotoSansTC", fontSize=12, leading=14, encoding="utf-8"
        )
    )

    # Update default styles to use the Chinese font
    for style in styles.byName.values():
        style.fontName = "NotoSansTC"

    # Convert HTML elements to ReportLab elements
    elements = []
    for element in soup.find_all(["p", "h1", "h2", "h3", "ul", "ol", "li", "table"]):
        if element.name in ["p", "h1", "h2", "h3"]:
            style = (
                "Heading1"
                if element.name == "h1"
                else (
                    "Heading2"
                    if element.name == "h2"
                    else "Heading3" if element.name == "h3" else "CustomStyle"
                )
            )
            elements.append(Paragraph(element.text, styles[style]))
        elif element.name in ["ul", "ol"]:
            for li in element.find_all("li"):
                bullet = "• " if element.name == "ul" else f"{len(elements)+1}. "
                elements.append(Paragraph(f"{bullet}{li.text}", styles["CustomStyle"]))
        elif element.name == "table":
            data = []
            for row in element.find_all("tr"):
                data.append(
                    [
                        Paragraph(cell.text, styles["CustomStyle"])
                        for cell in row.find_all(["th", "td"])
                    ]
                )
            table = Table(data)
            table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("FONTNAME", (0, 0), (-1, -1), "NotoSansTC"),
                        ("FONTSIZE", (0, 0), (-1, -1), 12),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
                        ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                        ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    ]
                )
            )
            elements.append(table)

    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer


def main():
    st.title("特教學習助手 - AI 個性化學習單生成器")

    # Load and display the images
    col1, col2 = st.columns(2)

    with col1:
        image1 = Image.open("scenario.png")
        st.image(image1, caption="特教學習場景", use_column_width=True)

    with col2:
        image2 = Image.open("logo.png")
        st.image(image2, caption="Unlimiter ATEL Inc.", use_column_width=True)

    # Add some space
    st.write("")
    st.write("")

    # Basic info input
    st.header("學生基本資料")
    name = st.text_input("姓名", value="王小明")
    gender = st.radio("性別", ["男", "女"], index=0)
    disability = st.multiselect(
        "障礙類別",
        [
            "智能障礙",
            "視覺障礙",
            "聽覺障礙",
            "語言障礙",
            "肢體障礙",
            "腦性麻痺",
            "身體病弱",
            "情緒行為障礙",
            "學習障礙",
            "自閉症",
            "多重障礙",
            "發展遲緩",
            "其他障礙",
        ],
        default=["自閉症"],
    )
    communication_issues = st.multiselect(
        "溝通問題",
        ["缺乏溝通動機", "無法有效表達", "詞彙量不足", "答非所問", "清晰度不佳"],
        default=["答非所問", "詞彙量不足", "無法有效表達", "缺乏溝通動機"],
    )
    communication_methods = st.multiselect(
        "溝通方式",
        [
            "眼睛凝視",
            "臉部表情",
            "肢體動作",
            "聲音",
            "聲調抑揚頓挫",
            "手勢",
            "手語",
            "口語",
            "實物",
            "照片",
            "圖片",
            "字卡",
            "書寫/打字",
            "語音溝通器",
            "其他",
        ],
        default=["肢體動作", "聲音"],
    )
    strengths = st.multiselect(
        "優勢能力",
        [
            "專注力佳",
            "記憶力佳",
            "創造力與想像力佳",
            "視覺與空間能力佳",
            "問題解決能力佳",
            "細節識別佳",
            "其他",
        ],
        default=["視覺與空間能力佳"],
    )
    weaknesses = st.multiselect(
        "弱勢能力",
        [
            "社交互動弱",
            "語言溝通弱",
            "注意力不集中",
            "情緒波動大",
            "動作協調困難",
            "學習困難",
            "感覺處理困難",
            "其他",
        ],
        default=["社交互動弱"],
    )
    teaching_time = st.number_input("預計教學時間 (分鐘)", min_value=1, max_value=120, value=20)

    # learn_assets_class selection
    st.header("學習類型選擇")
    learn_assets_class = st.radio("請選擇學習類型", ["生活自理", "專注力遊戲"])

    # learn_assets_contents selection
    st.header("學習單內容選擇")
    learn_assets_contents = st.radio(
        "請選擇學習單內容",
        [
            """主題是如廁方面-會坐馬桶小便，步驟包括：
    1.敲門確定沒人。2.脫下褲子。3.坐在馬桶小便。4.拿衛生紙對折。5.由前
    往後擦屁股。6.把衛生紙丟到垃圾桶。7.沖馬桶。8.穿上褲子。9.洗手。""",
            """主題是動物園，預設情境：有一隻可愛的小兔子迷
    路了，讓我們來帶牠回家吧。按下開始後，提醒學生睜大眼睛找一找，兔子在哪
    裡？接著需從6格、9格、12格、15格版面中找到唯一的兔子（其他格子內為無尾
    熊），順利通過時顯示：迷路的小兔子已經成功找到自己的家了！表示完成任務。
    """,
        ],
    )

    if st.button("生成學習單"):
        with st.spinner("正在生成學習單..."):
            # Prepare info string
            info = f"""
            姓名: {name}
            性別: {gender}
            障礙類別: {', '.join(disability)}
            溝通問題: {', '.join(communication_issues)}
            溝通方式: {', '.join(communication_methods)}
            優勢能力: {', '.join(strengths)}
            弱勢能力: {', '.join(weaknesses)}
            預計教學時間: {teaching_time} 分鐘
            """

            # Generate learning asset
            state.learning_asset = generate_learning_asset(
                info, learn_assets_class, learn_assets_contents
            )

            st.success("學習單已生成!")

    # 顯示生成的內容（如果存在）
    if "learning_asset" in state:
        st.subheader("生成的學習單")
        st.markdown(state.learning_asset)

        # Export options
        st.subheader("匯出選項")
        col1, col2 = st.columns(2)
        with col1:
            pdf_buffer = markdown_to_pdf(state.learning_asset)
            st.download_button(
                label="下載 PDF",
                data=pdf_buffer,
                file_name="learning_asset.pdf",
                mime="application/pdf",
            )

    # 添加重置按鈕
    # Add some space
    st.write("")
    st.write("")
    if st.button("重置(清空生成內容)"):
        state.clear()
        st.rerun()


if __name__ == "__main__":
    main()
