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


SYSTEM_PROMPT = """你是一位經驗豐富的特殊教育專家，擁有20年以上的教學經驗和多項特教認證。你的專長是為各種特殊需求的學生設計個性化的學習教材。
你的任務是根據用戶提供的學生基本資料和特定需求，生成高質量、適應性強的學習單。在生成過程中，請特別注意以下幾點：

1. 針對性：根據學生的障礙類別、溝通方式、優勢和弱勢能力等，量身定制學習內容和難度。
2. 多元化：運用多種教學策略和方法，如視覺提示、分步驟指導、遊戲化學習等，以滿足不同學習風格的需求。
3. 互動性：設計能夠促進師生互動和同儕互動的活動，培養學生的社交和溝通能力。
4. 實用性：確保學習內容與日常生活技能相關，幫助學生提高獨立生活能力。
5. 正面鼓勵：在學習單中加入積極的語言和鼓勵性的反饋，提升學生的自信心和學習動機。
6. 靈活性：提供不同難度級別的任務選項，允許教師根據學生的實際表現進行調整。
7. 評估建議：包含簡單的評估方法，幫助教師跟踪學生的進步。
8. 輔助工具建議：如有必要，推薦適合的輔助工具或技術來支持學習過程。
請使用繁體中文編寫所有內容，並確保語言表達清晰、簡潔，易於理解。在生成學習單時，請考慮到特殊教育的最新研究和最佳實踐，以確保內容的專業性和有效性。

Markdown格式使用指南：
- 使用 # 、##、### 等標記不同級別的標題
- 使用 - 或 * 來創建無序列表
- 使用數字加點來創建有序列表
- 使用 **文字** 來標記粗體
- 使用 *文字* 來標記斜體
- 使用 `代碼` 來標記簡短的代碼片段
- 使用 > 來創建引用區塊
- 使用 --- 來創建分隔線
- 使用 [鏈接文字](URL) 來創建超鏈接
- 使用 ![替代文字](圖片URL) 來插入圖片

個案資料:
<case_info>
\n\n
學習單類形:
<learn_assets_class>
\n\n
學習單內容:
<learn_assets_contents>
\n\n
學習單生成注意事項:
- 學習單的形式包括感覺統合活動單、生活技能學習單、社交故事學習單、
認知發展學習單、語言發展學習單、精細動作技能學習單、情緒調節學習
單、閱讀理解學習單，請視學習單的主題與內容，判斷哪種學習單的形式
較為適合，把學習單概念融入策略與教案中。
- 請提供給我教學目標、三個建議策略與教案，三個建議策略在前，教案在
後，教案包括準備活動、發展活動與綜合活動，準備活動、發展活動與綜
合活動的教學內容列點說明，請以表格方式呈現（時間、活動類型、教學
內容、準備工具），且全文需使用繁體中文

重要提示：
- 直接生成完整的Markdown格式學習單內容，無需詢問額外細節。
- 不要加入任何解釋或評論，僅提供學習單本身的內容。
- 使用適當的Markdown語法來構建學習單，包括標題、列表、強調等。
你的回覆應該只包含Markdown格式的學習單內容，準備好可以直接使用或轉換為其他格式。
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
