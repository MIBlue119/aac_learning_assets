import streamlit as st
import pandas as pd
from io import BytesIO
# from docx import Document
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from openai import OpenAI
import os

from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', )
MODEL="gpt-4o"
client = OpenAI(api_key=OPENAI_API_KEY)


SYSTEM_PROMPT="""你是一位經驗豐富的特殊教育專家，擁有20年以上的教學經驗和多項特教認證。你的專長是為各種特殊需求的學生設計個性化的學習教材。
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

def generate_learning_asset(case_info, learn_assets_class, learn_assets_contents, prompt=SYSTEM_PROMPT, model = MODEL):
    # Combine user info and scenario for the prompt
    prompt = prompt.replace('<case_info>', case_info).replace('<learn_assets_class', learn_assets_class).replace('<learn_assets_contents>', learn_assets_contents)
    
    # Call OpenAI API to generate content
    response = client.chat.completions.create(
        model=model,
        messages=[
          {"role": "system", "content": prompt},
        ]
    )
    
    return response.choices[0].message.content



import markdown
from xhtml2pdf import pisa
from io import StringIO, BytesIO
import base64


from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Image, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from markdown.extensions import Extension
from markdown.inlinepatterns import ImageInlineProcessor, IMAGE_LINK_RE

class CustomImageExtension(Extension):
    def extendMarkdown(self, md):
        md.inlinePatterns.register(CustomImageProcessor(IMAGE_LINK_RE, md), 'image', 150)

class CustomImageProcessor(ImageInlineProcessor):
    def handleMatch(self, m, data):
        src = m.group(4)
        alt = m.group(2) or ''
        return f'<reportlab_image src="{src}" alt="{alt}"/>', m.start(0), m.end(0)

def export_to_pdf(content, filename):
    buffer = BytesIO()
    
    # Register the font
    font_path = "/Users/weirenlan/Desktop/self_project/aac_learning_assets/jf-openhuninn-2.0.ttf"
    pdfmetrics.registerFont(TTFont('OpenHuninn', font_path))
    
    # Create PDF document
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    
    # Create a style that uses the Chinese font
    styles = getSampleStyleSheet()
    chinese_style = ParagraphStyle(
        'ChineseStyle',
        parent=styles['Normal'],
        fontName='OpenHuninn',
        fontSize=12,
        leading=14  # line spacing
    )
    
    # Convert Markdown to ReportLab-friendly format
    md = markdown.Markdown(extensions=[CustomImageExtension()])
    converted_content = md.convert(content)
    
    # Process the converted content
    story = []
    for line in converted_content.split('\n'):
        if line.strip():
            if line.startswith('<reportlab_image'):
                # Extract src and alt from the custom tag
                src = line.split('src="')[1].split('"')[0]
                alt = line.split('alt="')[1].split('"')[0]
                # Add Image to the story
                try:
                    img = Image(src, width=300, height=200)  # Adjust size as needed
                    story.append(img)
                    story.append(Spacer(1, 12))  # Add some space after the image
                except:
                    # If image can't be loaded, add a placeholder text
                    story.append(Paragraph(f"Image: {alt}", chinese_style))
            else:
                p = Paragraph(line, chinese_style)
                story.append(p)
    
    # Build PDF
    doc.build(story)
    
    buffer.seek(0)
    return buffer
# def get_base64_font(font_path):
#     with open(font_path, "rb") as font_file:
#         return base64.b64encode(font_file.read()).decode('utf-8')
# def export_to_pdf(content, filename):
#     buffer = BytesIO()
    
#     # Register the font
#     font_path = "/Users/weirenlan/Desktop/self_project/aac_learning_assets/jf-openhuninn-2.0.ttf"
#     pdfmetrics.registerFont(TTFont('OpenHuninn', font_path))
    
#     # Create PDF document
#     doc = SimpleDocTemplate(buffer, pagesize=letter)
    
#     # Create a style that uses the Chinese font
#     styles = getSampleStyleSheet()
#     chinese_style = ParagraphStyle(
#         'ChineseStyle',
#         parent=styles['Normal'],
#         fontName='OpenHuninn',
#         fontSize=12,
#         leading=14  # line spacing
#     )
    
#     # Convert Markdown to HTML
#     html = markdown.markdown(content)
    
#     # Convert HTML to Paragraphs
#     story = []
#     for line in html.split('\n'):
#         if line.strip():
#             p = Paragraph(line, chinese_style)
#             story.append(p)
    
#     # Build PDF
#     doc.build(story)
    
#     buffer.seek(0)
#     return buffer

# def export_to_pdf(content, filename):
#     # Convert Markdown to HTML
#     html = markdown.markdown(content)
#     # Get the base64 encoded font
#     font_path = "/Users/weirenlan/Desktop/self_project/aac_learning_assets/jf-openhuninn-2.0.ttf"
#     base64_font = get_base64_font(font_path)

#     # Wrap the HTML content in a basic HTML structure with CSS for Chinese font support
#     html = f"""
#     <html>
#     <head>
#         <meta charset="utf-8">
#         <style>
#             @font-face {{
#                 font-family: 'OpenHuninn';
#                 src: url(data:font/truetype;charset=utf-8;base64,{base64_font}) format('truetype');
#             }}
#             body {{
#                 font-family: 'OpenHuninn', sans-serif;
#             }}
#         </style>
#     </head>
#     <body>
#     {html}
#     </body>
#     </html>
#     """
    
#     # Create a PDF from the HTML
#     result = BytesIO()
#     pdf = pisa.pisaDocument(StringIO(html), result)
    
#     if not pdf.err:
#         result.seek(0)
#         return result
#     return None



# def export_to_docx(content, filename):
#     doc = Document()
#     doc.add_paragraph(content)
#     buffer = BytesIO()
#     doc.save(buffer)
#     buffer.seek(0)
#     return buffer

st.title("特教學習助手 - AI 個性化學習單生成器")

# Basic info input
st.header("學生基本資料")
name = st.text_input("姓名")
gender = st.radio("性別", ["男", "女"])
disability = st.multiselect("障礙類別", ["智能障礙", "視覺障礙", "聽覺障礙", "語言障礙", "肢體障礙", "腦性麻痺", "身體病弱", "情緒行為障礙", "學習障礙", "自閉症", "多重障礙", "發展遲緩", "其他障礙"])
communication_issues = st.multiselect("溝通問題", ["缺乏溝通動機", "無法有效表達", "詞彙量不足", "答非所問", "清晰度不佳"])
communication_methods = st.multiselect("溝通方式", ["眼睛凝視", "臉部表情", "肢體動作", "聲音", "聲調抑揚頓挫", "手勢", "手語", "口語", "實物", "照片", "圖片", "字卡", "書寫/打字", "語音溝通器", "其他"])
strengths = st.multiselect("優勢能力", ["專注力佳", "記憶力佳", "創造力與想像力佳", "視覺與空間能力佳", "問題解決能力佳", "細節識別佳", "其他"])
weaknesses = st.multiselect("弱勢能力", ["社交互動弱", "語言溝通弱", "注意力不集中", "情緒波動大", "動作協調困難", "學習困難", "感覺處理困難", "其他"])
teaching_time = st.number_input("預計教學時間 (分鐘)", min_value=1, max_value=120, value=20)

# learn_assets_class selection
st.header("學習類型選擇")
learn_assets_class = st.radio("請選擇學習類型", ["生活自理", "專注力遊戲"])

# learn_assets_contents selection
st.header("學習單內容選擇")
learn_assets_contents = st.radio("請選擇學習單內容", [
    """主題是如廁方面-會坐馬桶小便，步驟包括：
1.敲門確定沒人。2.脫下褲子。3.坐在馬桶小便。4.拿衛生紙對折。5.由前
往後擦屁股。6.把衛生紙丟到垃圾桶。7.沖馬桶。8.穿上褲子。9.洗手。""",
    """主題是動物園，預設情境：有一隻可愛的小兔子迷
路了，讓我們來帶牠回家吧。按下開始後，提醒學生睜大眼睛找一找，兔子在哪
裡？接著需從6格、9格、12格、15格版面中找到唯一的兔子（其他格子內為無尾
熊），順利通過時顯示：迷路的小兔子已經成功找到自己的家了！表示完成任務。
"""
])

if st.button("生成學習單"):
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
    learning_asset = generate_learning_asset(info, learn_assets_class, learn_assets_contents)
    
    # Display generated content
    st.subheader("生成的學習單")
    st.markdown(learning_asset)
    
    # Export options
    st.subheader("匯出選項")
    pdf_content = export_to_pdf(learning_asset, "learning_asset.pdf")
    if pdf_content:
        st.download_button(
            label="下載 PDF",
            data=pdf_content.getvalue(),
            file_name="learning_asset.pdf",
            mime="application/pdf"
        )
    else:
        st.error("PDF generation failed")   
    # col1, col2 = st.columns(2)
    
    # with col1:
    #     pdf_buffer = export_to_pdf(learning_asset, "learning_asset.pdf")
    #     st.download_button(
    #         label="下載 PDF",
    #         data=pdf_buffer,
    #         file_name="learning_asset.pdf",
    #         mime="application/pdf"
    #     )
    
    # with col2:
    #     docx_buffer = export_to_docx(learning_asset, "learning_asset.docx")
    #     st.download_button(
    #         label="下載 Word 文件",
    #         data=docx_buffer,
    #         file_name="learning_asset.docx",
    #         mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    #     )