import pandas as pd
import os

def create_excel_template(output_path):
    print("⏳ Đang khởi tạo file Excel Template cho Giảng viên...")
    
    # 1. Định nghĩa cấu trúc cột (Master Data Schema)
    columns = [
        "Question_ID", "CLO", "Bloom", "Question_Text", 
        "Option_A", "Option_B", "Option_C", "Option_D", 
        "Correct_Option", "Source_Ref"
    ]
    
    # 2. Tạo 2 dòng dữ liệu mẫu (Sample data)
    sample_data = [
        [
            "Q01", "CLO1", "Hiểu", 
            "Moodle đóng vai trò là hệ thống gì trong giáo dục?", 
            "Hệ điều hành", "Hệ quản trị CSDL", "Hệ thống Quản lý Học tập", "Trình biên dịch", 
            "C", "Bài 1, Slide 15"
        ],
        [
            "Q02", "CLO2", "Nhớ", 
            "Trường Đại học Công nghệ Kỹ thuật TP. HCM (HCMUTE) thành lập năm nào?", 
            "1960", "1962", "1964", "1970", 
            "B", "Chương 1 - Lịch sử trường"
        ]
    ]
    
    df = pd.DataFrame(sample_data, columns=columns)
    
    # SỬA LỖI WINERROR 3 TẠI ĐÂY: Kiểm tra nếu có tên thư mục thì mới tạo
    dir_name = os.path.dirname(output_path)
    if dir_name: 
        os.makedirs(dir_name, exist_ok=True)
    
    # 4. Xuất file và định dạng giao diện Excel (Dùng xlsxwriter)
    with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Question_Bank')
        
        workbook = writer.book
        worksheet = writer.sheets['Question_Bank']
        
        header_format = workbook.add_format({
            'bold': True,
            'text_wrap': True,
            'valign': 'vcenter',
            'align': 'center',
            'fg_color': '#D7E4BC',
            'border': 1
        })
        
        center_format = workbook.add_format({'align': 'center', 'valign': 'vcenter'})
        left_format = workbook.add_format({'align': 'left', 'valign': 'vcenter', 'text_wrap': True})

        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)
            
        worksheet.set_column('A:A', 15, center_format) 
        worksheet.set_column('B:C', 12, center_format)  
        worksheet.set_column('D:D', 50, left_format)    
        worksheet.set_column('E:H', 25, left_format)    
        worksheet.set_column('I:I', 15, center_format)  
        worksheet.set_column('J:J', 25, center_format)  
        
        worksheet.freeze_panes(1, 0)

    print("=" * 60)
    print(f"✅ ĐÃ TẠO THÀNH CÔNG TEMPLATE TẠI:\n👉 {output_path}")
    print("=" * 60)

if __name__ == "__main__":
    # TÌM ĐƯỜNG DẪN TUYỆT ĐỐI CHUẨN XÁC VÀO THƯ MỤC 'data/input' CỦA SKELETON
    # __file__ trỏ tới: backend/app/services/converter/generate_excel_template.py
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Lùi lại 3 cấp (converter -> services -> app -> backend) rồi vào data/input
    target_dir = os.path.abspath(os.path.join(current_dir, "..", "..", "..", "data", "input"))
    
    OUTPUT_FILE = os.path.join(target_dir, "OBE_Question_Bank.xlsx")
    
    create_excel_template(OUTPUT_FILE)