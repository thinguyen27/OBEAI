import requests
import json
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv

# --- CẤU HÌNH BẢO MẬT TỪ FILE .ENV ---
# Tìm và nạp các biến môi trường từ file .env
load_dotenv()

# Kéo dữ liệu từ biến môi trường ra
MOODLE_URL = os.getenv("MOODLE_URL")
TOKEN = os.getenv("MOODLE_TOKEN")

# Bẫy lỗi: Đề phòng trường hợp quên tạo file .env hoặc quên điền Token
if not TOKEN or not MOODLE_URL:
    raise ValueError("🚨 LỖI BẢO MẬT: Không tìm thấy MOODLE_TOKEN hoặc MOODLE_URL trong file .env!")

DEFAULT_COURSE_ID = 2  # ID của khóa học "Khảo sát Đồ án HTTT" (Cái này không nhạy cảm, để cứng cũng được)

def call_moodle_api(function_name, **kwargs):
    """Hàm base để gọi Moodle REST API có bẫy lỗi chi tiết"""
    params = {
        "wstoken": TOKEN,
        "wsfunction": function_name,
        "moodlewsrestformat": "json"
    }
    # Cập nhật các tham số truyền vào (xử lý cả mảng như courseids[0])
    for key, value in kwargs.items():
        if isinstance(value, list):
            for i, item in enumerate(value):
                params[f"{key}[{i}]"] = item
        else:
            params[key] = value
            
    response = requests.get(MOODLE_URL, params=params)
    
    if response.status_code != 200:
        print(f"\n[!] LỖI HTTP {response.status_code}")
        print("[!] Chi tiết từ Moodle:", response.text)
        response.raise_for_status()
        
    return response.json()

def extract_selected_answer(html_content):
    """HÀM CỐT LÕI XỬ LÝ ĐẢO ĐÁP ÁN"""
    soup = BeautifulSoup(html_content, 'html.parser')
    selected_radio = soup.find('input', {'type': 'radio', 'checked': 'checked'})
    if not selected_radio:
        return "Bỏ trống / Không xác định"
    
    parent_div = selected_radio.find_parent('div')
    if parent_div:
        number_span = parent_div.find('span', class_='answernumber')
        if number_span:
            number_span.decompose() 
        clean_text = parent_div.get_text(strip=True)
        return clean_text
        
    return "Lỗi phân tích DOM"

def main():
    print("="*60)
    print(" 🚀 HỆ THỐNG ĐỒNG BỘ DỮ LIỆU MOODLE (OBE API) 🚀 ")
    print("="*60)
    
    # --- PHẦN 1: TẠO MENU TRỰC QUAN ĐỂ CHỌN QUIZ ---
    course_input = input(f"Nhập ID Khóa học (Nhấn Enter để dùng mặc định là {DEFAULT_COURSE_ID}): ")
    course_id = int(course_input) if course_input.strip() else DEFAULT_COURSE_ID
    
    print("\nĐang tải danh sách bài thi từ Moodle...")
    quizzes_data = call_moodle_api("mod_quiz_get_quizzes_by_courses", courseids=[course_id])
    
    quizzes = quizzes_data.get('quizzes', [])
    if not quizzes:
        print(f"\n[!] Khóa học (ID={course_id}) này hiện chưa có bài Quiz nào!")
        return

    print("\n" + "-"*40)
    print(" DANH SÁCH BÀI KIỂM TRA ĐANG CÓ")
    print("-"*40)
    
    # In ra menu cho người dùng chọn
    for idx, quiz in enumerate(quizzes, start=1):
        print(f" [{idx}] {quiz['name']} (Giới hạn: {quiz.get('timeopen', 0)} -> {quiz.get('timeclose', 0)})")
        
    try:
        choice = int(input("\n👉 Nhập số thứ tự bài thi bạn muốn tải dữ liệu về (1, 2, 3...): "))
        if choice < 1 or choice > len(quizzes):
            print("Lựa chọn không hợp lệ!")
            return
    except ValueError:
        print("Vui lòng nhập một con số hợp lệ!")
        return
        
    # Lấy ra ID thực sự ẩn đằng sau lựa chọn của người dùng
    selected_quiz = quizzes[choice - 1]
    QUIZ_ID = selected_quiz['id']
    QUIZ_NAME = selected_quiz['name']
    
    print(f"\n✅ Đã chọn: '{QUIZ_NAME}' (Mã ẩn trên hệ thống: {QUIZ_ID})")
    print("-" * 60)
    
    # --- PHẦN 2: THỰC THI KÉO DỮ LIỆU (Giống code cũ) ---
    print(f"\n1. Đang quét danh sách sinh viên đã nộp bài '{QUIZ_NAME}'...")
    attempts_data = call_moodle_api("mod_quiz_get_attempts", quizid=QUIZ_ID, status="finished")
    
    if "exception" in attempts_data:
        print(f"LỖI API: {attempts_data['message']}")
        return
        
    attempts = attempts_data.get('attempts', [])
    total_students = len(attempts)
    
    if total_students == 0:
        print("Không có sinh viên nào hoàn thành bài thi này.")
        return
        
    print(f"-> Tìm thấy {total_students} sinh viên đã nộp bài. Đang tiến hành bóc tách...\n")
    
    all_class_data = {
        "quiz_id": QUIZ_ID,
        "quiz_name": QUIZ_NAME,
        "total_students": total_students,
        "student_results": []
    }
    
    for index, attempt in enumerate(attempts, start=1):
        attempt_id = attempt['id']
        user_id = attempt['userid']
        
        print(f"[{index}/{total_students}] Đang bóc tách bài của User ID: {user_id}...")
        
        review_data = call_moodle_api("mod_quiz_get_attempt_review", attemptid=attempt_id)
        questions = review_data.get('questions', [])
        
        student_record = {
            "user_id": user_id,
            "attempt_id": attempt_id,
            "answers": []
        }
        
        for q in questions:
            student_record["answers"].append({
                "slot": q.get('slot'),
                "status": q.get('state'),
                "mark": q.get('mark'),
                "selected_answer": extract_selected_answer(q.get('html'))
            })
            
        all_class_data["student_results"].append(student_record)
        
    # --- XUẤT FILE ---
    file_name = f"moodle_class_results_quiz{QUIZ_ID}.json"
    with open(file_name, "w", encoding="utf-8") as f:
        json.dump(all_class_data, f, ensure_ascii=False, indent=4)
        
    print("\n" + "="*50)
    print(f"🎉 ĐỒNG BỘ THÀNH CÔNG! Dữ liệu '{QUIZ_NAME}' đã được lưu ra file: {file_name}")

if __name__ == "__main__":
    main()