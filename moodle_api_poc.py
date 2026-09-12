import requests
import json
from bs4 import BeautifulSoup

# --- CONFIGURATION ---
MOODLE_URL = "http://localhost:8081/moodle/webservice/rest/server.php"
TOKEN = "247058d0d61edcc3b66f30623719c558"
QUIZ_ID = 1              # The ID of the quiz instance in the Moodle database
USER_ID = 3              # The internal user ID of the student (e.g., student01)

def call_moodle_api(function_name, **kwargs):
    """
    Base function to make Moodle REST API calls with comprehensive error handling.
    """
    params = {
        "wstoken": TOKEN,
        "wsfunction": function_name,
        "moodlewsrestformat": "json"
    }
    params.update(kwargs)
    
    response = requests.get(MOODLE_URL, params=params)
    
    # Catch HTTP errors (e.g., 403 Forbidden, 404 Not Found)
    if response.status_code != 200:
        print(f"\n[!] HTTP ERROR {response.status_code}")
        print("[!] Details from Moodle:", response.text)
        response.raise_for_status()
        
    return response.json()

def extract_selected_answer(html_content):
    """
    CORE FUNCTION TO HANDLE THE SHUFFLING MISMATCH ISSUE.
    Parses the raw HTML returned by Moodle using BeautifulSoup to extract 
    the exact text of the student's selected answer, bypassing shuffled labels.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 1. Find the checked radio input (which represents the student's selected answer)
    selected_radio = soup.find('input', {'type': 'radio', 'checked': 'checked'})
    
    if not selected_radio:
        return "Blank / Undefined"
    
    # 2. Locate the parent container holding the answer text.
    # In Moodle's DOM structure, the radio input and label text are usually wrapped in a <div>.
    parent_div = selected_radio.find_parent('div')
    
    if parent_div:
        # 3. Extract the clean text. 
        # Moodle often injects sequence labels like "a.", "b." inside a span.
        # We must remove this span from the DOM to retrieve the exact original text.
        number_span = parent_div.find('span', class_='answernumber')
        if number_span:
            number_span.decompose() # Remove the sequence span from the DOM tree
            
        # Retrieve the remaining clean text content
        clean_text = parent_div.get_text(strip=True)
        return clean_text
        
    return "DOM Parsing Error"

def main():
    print(f"--- BẮT ĐẦU KÉO DỮ LIỆU TỪ QUIZ_ID={QUIZ_ID}, USER_ID={USER_ID} ---")
    
    # 1. Retrieve the Attempt ID
    print("1. Gọi API: mod_quiz_get_user_attempts...")
    attempts_data = call_moodle_api("mod_quiz_get_user_attempts", quizid=QUIZ_ID, userid=USER_ID, status="finished")
    
    if "exception" in attempts_data:
        print(f"LỖI API: {attempts_data['message']}")
        return
        
    attempts = attempts_data.get('attempts', [])
    if not attempts:
        print("Không tìm thấy lượt thi nào đã hoàn thành của sinh viên này.")
        return
        
    attempt_id = attempts[0]['id']
    print(f"-> Đã lấy được Attempt ID: {attempt_id}")
    
    # 2. Retrieve detailed item-level review data based on the Attempt ID
    print(f"\n2. Gọi API: mod_quiz_get_attempt_review (Attempt ID: {attempt_id})...")
    review_data = call_moodle_api("mod_quiz_get_attempt_review", attemptid=attempt_id)
    
    questions = review_data.get('questions', [])
    
    # --- CREATE JSON STRUCTURE FOR STORAGE ---
    output_data = {
        "quiz_id": QUIZ_ID,
        "user_id": USER_ID,
        "attempt_id": attempt_id,
        "results": []
    }
    
    print("\n--- KẾT QUẢ BÓC TÁCH ---")
    for q in questions:
        slot = q.get('slot')       # Question sequence number
        mark = q.get('mark')       # Marks obtained
        status = q.get('state')    # Correctness state
        raw_html = q.get('html')   # Raw HTML rendered by Moodle
        
        # Parse HTML to extract the actual selected text
        selected_text = extract_selected_answer(raw_html)
        
        print(f"Câu {slot}: Trạng thái: {status} | Điểm: {mark} | Đáp án chọn: {selected_text}")
        
        # Append item-level data to the results list
        output_data["results"].append({
            "slot": slot,
            "status": status,
            "mark": mark,
            "selected_answer": selected_text
        })
        
    # --- EXPORT TO JSON FILE ---
    file_name = f"moodle_result_user{USER_ID}_quiz{QUIZ_ID}.json"
    
    # ensure_ascii=False is crucial to preserve Vietnamese unicode characters
    with open(file_name, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=4)
        
    print("-" * 50)
    print(f"✅ Đã xuất dữ liệu thành công ra file: {file_name}")

if __name__ == "__main__":
    main()