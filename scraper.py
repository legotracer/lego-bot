import sys
sys.stdout.reconfigure(encoding='utf-8')  # UTF-8 인코딩 적용

import requests
import hashlib
import hmac
import urllib.parse
from time import gmtime, strftime
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# 쿠팡 OpenAPI 설정
ACCESS_KEY = '8e64ab3e-4237-40bb-b4c7-1d15f048fea2'
SECRET_KEY = 'd8b8d3928f3b5791b59fc0c03df71da6c887b1f7'
DOMAIN = 'https://api-gateway.coupang.com'

### 🔹 쿠팡 가격 조회 (OpenAPI 사용) ###
def generate_hmac(method, url, secret_key, access_key):
    path, *query = url.split("?")
    datetime_gmt = strftime('%y%m%d', gmtime()) + 'T' + strftime('%H%M%S', gmtime()) + 'Z'
    message = datetime_gmt + method + path + (query[0] if query else "")
    signature = hmac.new(bytes(secret_key, "utf-8"), message.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"CEA algorithm=HmacSHA256, access-key={access_key}, signed-date={datetime_gmt}, signature={signature}"

def get_coupang_price(lego_number):
    method = 'GET'
    url = f"/v2/providers/affiliate_open_api/apis/openapi/products/search?keyword={urllib.parse.quote(lego_number)}&limit=1"
    auth = generate_hmac(method, url, SECRET_KEY, ACCESS_KEY)

    response = requests.request(method=method, url=f"{DOMAIN}{url}", headers={"Authorization": auth, "Content-Type": "application/json;charset=UTF-8"})

    if response.status_code == 200:
        try:
            product_data = response.json().get('data', {}).get('productData', [])
            if not product_data:
                return "쿠팡에서 해당 상품을 찾을 수 없습니다."

            first_item = product_data[0]
            price = f"{first_item['productPrice']}원"
            product_url = first_item['productUrl']
            
            print(f"쿠팡 가격 조회 성공: {price} ({product_url})")  
            return f"{price} [쿠팡에서 구매하기]({product_url})"

        except KeyError:
            return "쿠팡에서 가격을 찾을 수 없습니다."

    return "쿠팡에서 가격을 찾을 수 없습니다."

### 🔹 레고몰 가격 조회 (Selenium 사용) ###
def get_lego_price(lego_number):
    url = f"https://www.lego.com/ko-kr/search?q={lego_number}"

    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # 창 없이 실행
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    try:
        print(f"레고몰 페이지 접속: {url}")
        driver.get(url)
        
        # 🔹 JavaScript가 가격을 로딩할 때까지 기다림 (최대 10초)
        price_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "span[data-test='product-price']"))
        )

        # 🔹 상품 링크 찾기
        link_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "a[data-test='product-leaf-title-link']"))
        )
        product_url = link_element.get_attribute("href")

        # 🔹 가격 가져오기 (JavaScript가 비동기로 로드하는 경우도 처리)
        price = price_element.text.strip()
        if not price:
            price = driver.execute_script("return arguments[0].innerText;", price_element).strip()

        price = price.replace(",", "").replace(" 원", "") + "원"
        print(f"레고몰 가격 조회 성공: {price} ({product_url})")

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        price = "레고 공식몰에서 가격을 찾을 수 없습니다."
        product_url = f"https://www.lego.com/ko-kr/search?q={lego_number}"  # 기본 검색 링크

    finally:
        driver.quit()  # 🔹 브라우저 종료

    return f"{price} [레고몰에서 구매하기]({product_url})"

# 🔹 테스트 실행
if __name__ == "__main__":
    lego_number = "60440"
    print(f"🔍 레고 {lego_number} 가격 조회")
    print(f"🛒 쿠팡: {get_coupang_price(lego_number)}")
    print(f"🛒 레고 공식몰: {get_lego_price(lego_number)}")
