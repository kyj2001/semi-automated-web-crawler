"""
과거 아르바이트에서 사용했던 대표전화 조사 반자동화 코드를
현재 관점에서 개선하여 재구성한 버전입니다.

당시에는 실제 웹사이트를 대상으로 Selenium을 사용했지만,
현재는 대상 사이트의 크롤링 정책을 고려하여 외부 요청 없이
examples 디렉터리의 로컬 HTML을 통해 동작을 재현합니다.

주요 개선 사항
- 기능별 함수 분리
- 구체적인 예외 처리
- 업체명 비교 정규화
- WebDriver 종료 보장
- 요청 간격 제어 로직 분리
- 최대 50개 단위 배치 처리
"""

import time
from pathlib import Path

from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


# 경로 설정
PROJECT_DIR = Path(__file__).resolve().parent
EXAMPLES_DIR = PROJECT_DIR / "examples"
SEARCH_RESULT_FILE = EXAMPLES_DIR / "search_result.html"

# DOM 선택자
SEARCH_RESULT_SELECTOR = "li.list_item"
TITLE_SELECTOR = ".tit"

# 실행 설정
WAIT_TIMEOUT = 5
MAX_BATCH_SIZE = 50

# 요청 간격 설정
REQUEST_INTERVAL_SECONDS = 2
ENABLE_REQUEST_INTERVAL = False


def create_driver():
    # Chrome WebDriver 생성
    options = webdriver.ChromeOptions()

    # options.add_argument("--headless")

    return webdriver.Chrome(options=options)


def normalize_text(text):
    # 공백·줄바꿈 제거 후 비교
    return "".join(text.split()).lower()


def validate_example_files():
    # 테스트 파일 존재 여부 확인
    if not SEARCH_RESULT_FILE.exists():
        raise FileNotFoundError(
            f"검색 결과 예제 파일을 찾을 수 없습니다: {SEARCH_RESULT_FILE}"
        )


def wait_between_requests():
    # 외부 요청 환경에서 요청 간격 적용
    if ENABLE_REQUEST_INTERVAL:
        time.sleep(REQUEST_INTERVAL_SECONDS)


def load_search_results(driver):
    # 로컬 검색 결과 페이지 로드
    driver.get(SEARCH_RESULT_FILE.as_uri())

    WebDriverWait(driver, WAIT_TIMEOUT).until(
        EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, SEARCH_RESULT_SELECTOR)
        )
    )


def find_detail_url(driver, keyword):
    # 입력 업체와 일치하는 상세 페이지 탐색
    normalized_keyword = normalize_text(keyword)

    items = driver.find_elements(
        By.CSS_SELECTOR,
        SEARCH_RESULT_SELECTOR,
    )

    for item in items:
        try:
            title_element = item.find_element(
                By.CSS_SELECTOR,
                TITLE_SELECTOR,
            )

            brand_text = title_element.text.strip()

            if normalize_text(brand_text) != normalized_keyword:
                continue

            link_element = title_element.find_element(
                By.TAG_NAME,
                "a",
            )

            detail_url = link_element.get_attribute("href")

            if detail_url:
                return detail_url

        except NoSuchElementException:
            continue

    return None


def extract_phone_number(driver, detail_url):
    # 상세 페이지에서 대표전화 추출
    driver.get(detail_url)

    phone_li = WebDriverWait(driver, WAIT_TIMEOUT).until(
        EC.presence_of_element_located(
            (
                By.XPATH,
                '//li[contains(., "대표전화")]',
            )
        )
    )

    phone_element = phone_li.find_element(
        By.TAG_NAME,
        "b",
    )

    phone = phone_element.text.strip()

    return phone if phone else None


def process_keyword(driver, keyword):
    # 업체 하나 처리
    try:
        load_search_results(driver)

        detail_url = find_detail_url(
            driver,
            keyword,
        )

        if not detail_url:
            return f"{keyword} (검색 결과 없음)"

        wait_between_requests()

        phone = extract_phone_number(
            driver,
            detail_url,
        )

        if not phone:
            return f"{keyword} (대표전화 없음)"

        return f"{keyword} {phone}"

    except TimeoutException:
        return f"{keyword} (페이지 요소 로딩 실패)"

    except NoSuchElementException:
        return f"{keyword} (필요한 요소를 찾을 수 없음)"

    except WebDriverException as error:
        return (
            f"{keyword} "
            f"(브라우저 오류: {error.__class__.__name__})"
        )


def find_representative_numbers(keywords):
    # 입력 업체 순차 처리
    driver = create_driver()
    results = []

    try:
        total = len(keywords)

        for index, keyword in enumerate(
            keywords,
            start=1,
        ):
            print(
                f"[{index}/{total}] "
                f"{keyword} 검색 중..."
            )

            result = process_keyword(
                driver,
                keyword,
            )

            results.append(result)

            wait_between_requests()

    finally:
        driver.quit()

    return results


def read_keywords():
    # 최대 50개까지 입력
    print(
        f"업체명을 줄 단위로 입력하세요. "
        f"최대 {MAX_BATCH_SIZE}개까지 입력할 수 있습니다."
    )
    print("빈 줄을 입력하면 검색을 시작합니다.")

    keywords = []

    while len(keywords) < MAX_BATCH_SIZE:
        line = input().strip()

        if not line:
            break

        keywords.append(line)

    if len(keywords) == MAX_BATCH_SIZE:
        print(
            f"\n최대 배치 크기 "
            f"{MAX_BATCH_SIZE}개에 도달했습니다."
        )

    return keywords


def main():
    # 실행 전 테스트 환경 확인
    try:
        validate_example_files()

    except FileNotFoundError as error:
        print(error)
        return

    keywords = read_keywords()

    if not keywords:
        print("입력된 업체명이 없습니다.")
        return

    print(
        f"\n총 {len(keywords)}개 업체의 "
        f"검색을 시작합니다.\n"
    )

    results = find_representative_numbers(
        keywords
    )

    print("\n검색 결과")

    for result in results:
        print(f"- {result}")


if __name__ == "__main__":
    main()