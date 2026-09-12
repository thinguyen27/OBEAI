import requests
import json
from bs4 import BeautifulSoup

# --- CẤU HÌNH ---
MOODLE_URL = "http://localhost:8081/moodle/webservice/rest/server.php"
TOKEN = "247058d0d61edcc3b66f30623719c558"
QUIZ_ID = 2              # ID của bài quiz
USER_ID = 3                # ID của student01

def call_moodle_api(function_name, **kwargs):
    """Hàm base để gọi Moodle REST API"""
    params = {
        "wstoken": TOKEN,
        "wsfunction": function_name,
        "moodlewsrestformat": "json"
    }
    params.update(kwargs)
    
    response = requests.get(MOODLE_URL, params=params)
    response.raise_for_status()
    return response.json()

def extract_selected_answer(html_content):
    """
    HÀM CỐT LÕI XỬ LÝ ĐẢO ĐÁP ÁN
    Dùng BeautifulSoup để bóc tách mã HTML Moodle trả về, tìm ra đúng text đáp án đã chọn.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 1. Tìm thẻ input radio được check (chính là đáp án sinh viên đã chọn)
    selected_radio = soup.find('input', {'type': 'radio', 'checked': 'checked'})
    
    if not selected_radio:
        return "Bỏ trống / Không xác định"
    
    # 2. Định vị thẻ chứa text của đáp án này
    # Trong cấu trúc DOM của Moodle, input radio và text đáp án thường nằm chung trong 1 thẻ <div> có class 'answer' hoặc 'd-flex'
    parent_div = selected_radio.find_parent('div')
    
    if parent_div:
        # 3. Lấy text. Cần cẩn thận vì Moodle hay nhét thêm các span hiển thị "a.", "b."
        # Ta phải xóa thẻ span chứa số thứ tự để lấy đúng nội dung gốc
        number_span = parent_div.find('span', class_='answernumber')
        if number_span:
            number_span.decompose() # Xóa thẻ này khỏi cây DOM
            
        # Lấy nội dung text sạch còn lại
        clean_text = parent_div.get_text(strip=True)
        return clean_text
        
    return "Lỗi phân tích DOM"

def main():
    print(f"--- BẮT ĐẦU KÉO DỮ LIỆU TỪ QUIZ_ID={QUIZ_ID}, USER_ID={USER_ID} ---")
    
    # 1. Lấy mã lượt thi (Attempt ID)
    print("1. Gọi API: mod_quiz_get_user_attempts...")
    attempts_data = call_moodle_api("mod_quiz_get_user_attempts", quizid=QUIZ_ID, userid=USER_ID, status="finished")
    
    if "exception" in attempts_data:
        print(f"LỖI API: {attempts_data['message']}")
        return
        
    attempts = attempts_data.get('attempts', [])
    if not attempts:
        print("Không tìm thấy lượt thi nào đã hoàn thành của sinh viên này.")
        return
        
    attempt_id = attempts[0]['id']  # Lấy lượt làm bài đầu tiên
    print(f"-> Đã lấy được Attempt ID: {attempt_id}")
    
    # 2. Lấy chi tiết bài làm dựa vào Attempt ID
    print(f"\n2. Gọi API: mod_quiz_get_attempt_review (Attempt ID: {attempt_id})...")
    review_data = call_moodle_api("mod_quiz_get_attempt_review", attemptid=attempt_id)
    
    questions = review_data.get('questions', [])
    
    print("\n--- KẾT QUẢ BÓC TÁCH ---")
    for q in questions:
        slot = q.get('slot')       # Số thứ tự câu hỏi
        mark = q.get('mark')       # Điểm số đạt được
        status = q.get('state')    # Trạng thái (đúng/sai)
        raw_html = q.get('html')   # Nguyên cục HTML Moodle trả về
        
        # Gọi hàm bóc tách HTML
        selected_text = extract_selected_answer(raw_html)
        
        print(f"Câu {slot}:")
        print(f"  - Trạng thái: {status} | Điểm: {mark}")
        print(f"  - Đáp án sinh viên đã chọn (Bóc tách từ HTML): {selected_text}")
        print("-" * 30)

if __name__ == "__main__":
    main()