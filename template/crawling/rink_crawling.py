from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import pandas as pd
import numpy as np
import datetime
import schedule
import time
import os


# 함수 ----------------------------------------------------------------------------------------
def scroll_to_element(element):  #버튼위치로 스크롤링
    driver.execute_script("arguments[0].scrollIntoView(true);", element)
    time.sleep(0.5)

def get_current_page_number():  #현재 페이지 넘버찾기
    try:
        current_page_elem = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '#prdReview > div > div.bbsListWrap.reviewAll > div.pagination > ol > li.is-active'))
        )
        return current_page_elem.text
    except Exception as e:
        print(f"Error getting current page number: {e}")
        return None
    
def initialize_driver():  # WebDriver 초기화
    global driver
    options = webdriver.ChromeOptions()
    options.add_argument("headless")
    driver = webdriver.Chrome(options=options)
    
# -----------------------------------------------------------------------------------------------

    
def rink_crawling():

    initialize_driver()
    interpark_data = pd.DataFrame()
    
    df = pd.read_csv('final_link.csv', header=None, names=['title', 'link'])
    titles = df['title'].tolist()
    links = df['link'].tolist()
    
    # 기존 리뷰 데이터를 로드
    if os.path.exists('interpark_reviews.csv'):
        existing_reviews = pd.read_csv('interpark_reviews.csv')
        print('원래거')       
    else:
        existing_reviews = pd.DataFrame()
        print('새로')

        
    for tit,url in zip(titles,links):
        wait = WebDriverWait(driver, 3)
        driver.get(url)
        time.sleep(1)
        
        # 팝업 닫기
        try:
            close_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '#popup-prdGuide > div > div.popupFooter > button > span')))
            driver.execute_script("arguments[0].click();", close_btn)
        except TimeoutException:
            print("팝업 닫기 버튼을 찾을 수 없습니다.")
        except Exception as e:
            print(f"팝업 닫기 중 에러 발생: {e}")
        
        # 관람후기 클릭 및 정렬
        try:  
            try:
                review_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '#productMainBody > nav > ul > li.navItem.has-event > a')))           
                scroll_to_element(review_btn)
                driver.execute_script("arguments[0].click();", review_btn)
                
            except Exception as e:
                review_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), '관람후기')]")))                       
                scroll_to_element(review_btn)
                driver.execute_script("arguments[0].click();", review_btn)   

            empathy_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'a.sortLabel[data-target="DESC_BOOMUP_COUNT"]')))
            if empathy_btn:         
                scroll_to_element(empathy_btn)
                driver.execute_script("arguments[0].click();", empathy_btn)
                time.sleep(1)
            else:
                break                       

        except TimeoutException:
            print("관람후기 또는 정렬 버튼을 찾을 수 없습니다.")
        except Exception as e:
            print(f"관람후기 또는 정렬 버튼 클릭 중 에러 발생: {e}")
            continue
        
        date = [] #작성일
        reviews = []  #리뷰
        stars = []  #별점
        empathy = []  #공감
        urllst= []  #url리스트
        titlelst = []  #제목

        cnt=0
        while cnt<5:  #개수제한 750개 (15개 * 10page)
            try:
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                title = soup.find('h2', {'class': 'prdTitle'}).text    
                print(f'{cnt+1}) {title}')                  
                          
                # 페이지 버튼 클릭
                try:
                    page_btns = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#prdReview > div > div.bbsListWrap.reviewAll > div.pagination > ol > li')))
                    for btn in page_btns:                                           
                        scroll_to_element(btn)
                        driver.execute_script("window.scrollBy(0, -100);")
                        WebDriverWait(driver, 20).until(EC.element_to_be_clickable(btn))                            
                        btn.click()
                        time.sleep(2) 
                        
                        # date 추출
                        date_elements = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#prdReview > div > div.bbsListWrap.reviewAll > ul > li > div > div.bbsItemHead > div.rightSide > ul > li:nth-child(2)')))        
                        date.extend([element.text for element in date_elements])                        

                        # 리뷰 추출
                        review_elements = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#prdReview > div > div.bbsListWrap.reviewAll > ul > li > div > div.bbsItemBody > div.bbsBodyMain > p')))
                        reviews.extend([element.text for element in review_elements])

                        # 별점 추출
                        star_elements = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#prdReview > div > div.bbsListWrap.reviewAll > ul > li > div > div.bbsItemHead > div.leftSide > div > div.prdStarBack > div')))
                        stars.extend([element.get_attribute('data-star') for element in star_elements])
                        
                        empathy_elements = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#prdReview > div > div.bbsListWrap.reviewAll > ul > li > div > div.bbsItemHead > div.rightSide > ul > li:nth-child(4)')))
                        # 각 요소를 순회하면서 공감 수 추출
                        for element in empathy_elements:
                            if '공감' in element.text:
                                number = int(element.text.split('공감')[1].strip().split()[0])
                                empathy.append(number)                                
                                urllst.append(url)  # url저장    
                                titlelst.append(tit)  
               

                except NoSuchElementException as e:
                    print('페이지버튼을 찾을 수 없습니다.')
                    # date 추출
                    date_elements = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#prdReview > div > div.bbsListWrap.reviewAll > ul > li > div > div.bbsItemHead > div.rightSide > ul > li:nth-child(2)')))        
                    date.extend([element.text for element in date_elements])
                    
                    # 리뷰 추출
                    review_elements = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#prdReview > div > div.bbsListWrap.reviewAll > ul > li > div > div.bbsItemBody > div.bbsBodyMain > p')))
                    reviews.extend([element.text for element in review_elements])

                    # 별점 추출
                    star_elements = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#prdReview > div > div.bbsListWrap.reviewAll > ul > li > div > div.bbsItemHead > div.leftSide > div > div.prdStarBack > div')))
                    stars.extend([element.get_attribute('data-star') for element in star_elements])
                    
                    empathy_elements = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#prdReview > div > div.bbsListWrap.reviewAll > ul > li > div > div.bbsItemHead > div.rightSide > ul > li:nth-child(4)')))
                    # 각 요소를 순회하면서 공감 수 추출
                    for element in empathy_elements:
                        if '공감' in element.text:
                            number = int(element.text.split('공감')[1].strip().split()[0])
                            empathy.append(number)
                            urllst.append(url)  # url저장   
                            titlelst.append(tit)        

                    cnt = 100
                    break  

                # 다음 페이지 버튼 클릭
                try:
                    next_btn = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#prdReview > div > div.bbsListWrap.reviewAll > div.pagination > a')))
                    
                    if len(next_btn) > 1 and next_btn[1].find_element(By.CSS_SELECTOR, 'span.blind').text == '다음':
                        scroll_to_element(next_btn[1])
                        next_btn[1].click()
                        time.sleep(2)
                        new_page = get_current_page_number()
                        current_page = new_page  #페이지번호 업데이트
                        cnt +=1
                    elif len(next_btn) == 1:  #버튼이 하나만 있을때, 텍스트가 다음이면 클릭, 이전이면 마지막페이지
                        next_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '#prdReview > div > div.bbsListWrap.reviewAll > div.pagination > a')))
                        if next_btn.find_element(By.CSS_SELECTOR, 'span.blind').text == '다음':
                            next_btn.click()
                            new_page = get_current_page_number()
                            current_page = new_page  #페이지번호 업데이트
                            cnt +=1
                        else:
                            print("페이지 버튼을 전부 찾았습니다. 마지막 페이지 입니다.")
                            cnt = 100
                            break                               

                except Exception as e:                    
                    print('넥스트 버튼이 없습니다. 마지막 페이지 입니다.')
                    cnt = 100
                    break                      

            except TimeoutException as e:
                print(f"TimeoutException: {e}. Retrying...")
                # date 추출
                date_elements = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#prdReview > div > div.bbsListWrap.reviewAll > ul > li > div > div.bbsItemHead > div.rightSide > ul > li:nth-child(2)')))        
                date.extend([element.text for element in date_elements])  
                
                # 리뷰 추출
                review_elements = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#prdReview > div > div.bbsListWrap.reviewAll > ul > li > div > div.bbsItemBody > div.bbsBodyMain > p')))
                reviews.extend([element.text for element in review_elements])

                # 별점 추출
                star_elements = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#prdReview > div > div.bbsListWrap.reviewAll > ul > li > div > div.bbsItemHead > div.leftSide > div > div.prdStarBack > div')))
                stars.extend([element.get_attribute('data-star') for element in star_elements])
                
                empathy_elements = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#prdReview > div > div.bbsListWrap.reviewAll > ul > li > div > div.bbsItemHead > div.rightSide > ul > li:nth-child(4)')))
                # 각 요소를 순회하면서 공감 수 추출
                for element in empathy_elements:
                    if '공감' in element.text:
                        number = int(element.text.split('공감')[1].strip().split()[0])
                        empathy.append(number)
                        urllst.append(url)  # url저장   
                        titlelst.append(tit)        
                cnt = 100
                break  

                
            except Exception as e:
                print(f"에러: {e}")
                break


        titles = [title] * len(reviews) #리뷰개수만큼 타이틀개수 채우기
        # now = datetime.datetime.now().date().strftime("%Y.%m.%d")
        # date = [now] * len(reviews)
        print(len(titles), len(stars), len(reviews),len(empathy),len(titlelst),len(urllst),len(date))  #각리스트 길이 동일한지 확인

        temp_df = pd.DataFrame({
            'date' : date,
            'title': titles,
            'star': stars,
            'review': reviews,
            'empathy': empathy,
            'title2' : titlelst,
            'url': urllst,
        })
        
        # 기존 데이터와 새로운 데이터를 결합하기 전에 중복 제거
        
        combined_data = pd.concat([existing_reviews, temp_df])
        print("dupliation 전 ", combined_data)
    
        combined_data = combined_data.drop_duplicates(['date', 'title', 'review', 'empathy', 'title2', 'url'],keep='last')        
        # 'date' 기준으로 오름차순 정렬
        combined_data = combined_data.sort_values(by='date', ascending=True)
        print("dupliation 후 ", combined_data)
        # 데이터 저장
        combined_data.to_csv('interpark_reviews.csv', index=False, encoding='utf-8')

    driver.quit()
    # -----------------------------------------------------------------------------------------------
    

# 매일 새벽 1시 리뷰크롤링 설정
schedule.every().day.at("17:42:35").do(rink_crawling)

while True:
    schedule.run_pending()
    time.sleep(1)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      