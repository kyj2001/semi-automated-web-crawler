"""
아르바이트 중 반복적으로 수행하던 외식·프랜차이즈 업체의
대표전화 번호 조사 작업을 반자동화하기 위해 작성한 코드입니다.

당시 실제 사용했던 코드 구조를 최대한 그대로 보존한 버전입니다.
대상 웹사이트의 구조가 변경되었을 수 있으므로 현재 정상 동작은 보장하지 않습니다.
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# 메인 사이트 주소
BASE_URL = "https://www.jumpoline.com"

def find_representative_numbers(keywords):
    options = webdriver.ChromeOptions()
    # options.add_argument('--headless')  # 브라우저 안 띄우고 싶으면 주석 해제
    driver = webdriver.Chrome(options=options)

    results = []

    for keyword in keywords:
        driver.get(BASE_URL)

        # 검색창 대기 및 입력
        try:
            search_input = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, 'searchword'))
            )
        except:
            print(f"❌ 검색창 로딩 실패: {keyword}")
            continue

        search_input.clear()
        search_input.send_keys(keyword)
        search_input.send_keys(Keys.RETURN)
        time.sleep(2)  # 검색 결과 로딩 대기

        try:
            items = driver.find_elements(By.CSS_SELECTOR, 'li.list_item')
            matched = False

            for item in items:
                title_element = item.find_element(By.CSS_SELECTOR, '.tit')
                brand_text = title_element.text.replace('\n', '').strip()

                if brand_text == keyword:
                    # 상세 페이지 링크 추출 및 절대 URL 생성
                    detail_relative_url = title_element.find_element(By.TAG_NAME, 'a').get_attribute('href')
                    if detail_relative_url.startswith("/"):
                        detail_url = BASE_URL + detail_relative_url
                    else:
                        detail_url = detail_relative_url

                    # 상세 페이지 이동
                    driver.get(detail_url)
                    time.sleep(2)

                    # 대표전화 추출
                    try:
                        phone_li = driver.find_element(By.XPATH, '//li[contains(text(), "대표전화")]')
                        phone = phone_li.find_element(By.TAG_NAME, 'b').text.strip()
                        results.append(f"{keyword} {phone}")
                    except:
                        results.append(f"{keyword} (대표전화 없음)")

                    matched = True
                    break

            if not matched:
                results.append(f"{keyword} (검색 결과 없음)")

        except Exception as e:
            results.append(f"{keyword} (오류 발생: {str(e)})")

    driver.quit()
    return results


# ✅ 키워드 입력 및 실행
if __name__ == "__main__":
    print("🔹 키워드를 줄 단위로 입력하세요 (빈 줄 입력 시 종료):")
    keywords = []
    while True:
        line = input().strip()
        if line == "":
            break
        keywords.append(line)

    print(f"\n🔍 총 {len(keywords)}개 검색 중...\n")
    result_lines = find_representative_numbers(keywords)

    print("📞 결과:")
    for line in result_lines:
        print("-", line)
