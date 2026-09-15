import pandas as pd
import html
import os

def escape_cdata(text):
    """Bọc nội dung vào CDATA để Moodle không bị lỗi khi có ký tự đặc biệt (<, >, &)"""
    # Đảm bảo input là string và thay thế giá trị rỗng
    safe_text = str(text) if pd.notna(text) else ""
    return f"<![CDATA[{safe_text}]]>"

def generate_moodle_xml(excel_file_path, output_xml_path):
    print(f"📥 Đang đọc dữ liệu từ: {excel_file_path}")
    
    try:
        df = pd.read_excel(excel_file_path)
    except FileNotFoundError:
        print("[!] Không tìm thấy file Excel. Hãy chắc chắn bạn đã tạo file đúng tên và chạy file tạo mẫu trước!")
        return

    # Bắt đầu cấu trúc Moodle XML
    xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n<quiz>\n'

    # Duyệt qua từng dòng (từng câu hỏi) trong file Excel
    for index, row in df.iterrows():
        q_id = row['Question_ID']
        clo = row['CLO']
        bloom = row['Bloom']
        q_text = row['Question_Text']
        source = row['Source_Ref']
        correct_opt = str(row['Correct_Option']).strip().upper() # Đảm bảo là A, B, C, D
        
        # Tên câu hỏi trên Moodle = ID + CLO + Bloom để GV dễ tìm
        question_name = f"[{q_id}][{clo}][{bloom}] {str(q_text)[:30]}..." 
        
        # Thêm phần Source_Ref ẩn vào text câu hỏi để lưu vết tài liệu
        full_q_text = f"{q_text}<br><br><i><small>(Nguồn tham chiếu: {source})</small></i>"

        xml_content += f'''
    <!-- Câu hỏi: {q_id} -->
    <question type="multichoice">
        <name>
            <text>{escape_cdata(question_name)}</text>
        </name>
        <questiontext format="html">
            <text>{escape_cdata(full_q_text)}</text>
        </questiontext>
        <single>true</single>
        <shuffleanswers>true</shuffleanswers>
        <answernumbering>abc</answernumbering>
'''
        # Duyệt qua 4 phương án A, B, C, D
        options = {'A': row['Option_A'], 'B': row['Option_B'], 'C': row['Option_C'], 'D': row['Option_D']}
        
        for key, value in options.items():
            # Moodle quy định: 100 là đúng, 0 là sai
            fraction = "100" if key == correct_opt else "0"
            
            xml_content += f'''
        <answer fraction="{fraction}" format="html">
            <text>{escape_cdata(value)}</text>
        </answer>'''
        
        # Đóng thẻ câu hỏi
        xml_content += '''
    </question>
'''

    # Đóng thẻ quiz
    xml_content += '</quiz>'

    # Đảm bảo thư mục output tồn tại trước khi ghi file
    os.makedirs(os.path.dirname(output_xml_path), exist_ok=True)

    # Xuất ra file
    with open(output_xml_path, "w", encoding="utf-8") as f:
        f.write(xml_content)
        
    print(f"✅ HOÀN TẤT! Đã sinh ra file Moodle XML tại:\n👉 {output_xml_path}")
    print(f"-> Tổng số câu hỏi đã xử lý: {len(df)}")
    print("👉 Hướng dẫn: Mở Moodle -> Question Bank -> Import -> Chọn định dạng 'Moodle XML format' và upload file này lên.")


if __name__ == "__main__":
    # TÌM ĐƯỜNG DẪN TUYỆT ĐỐI VÀO SKELETON
    # __file__ trỏ tới: backend/app/services/converter/xml_generator.py
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Lùi lại 3 cấp (converter -> services -> app -> backend)
    backend_dir = os.path.abspath(os.path.join(current_dir, "..", "..", ".."))
    
    # Lấy file Excel từ data/input và xuất file XML ra data/output
    EXCEL_INPUT = os.path.join(backend_dir, "data", "input", "OBE_Question_Bank.xlsx")
    XML_OUTPUT = os.path.join(backend_dir, "data", "output", "Moodle_Import_Ready.xml")
    
    generate_moodle_xml(EXCEL_INPUT, XML_OUTPUT)