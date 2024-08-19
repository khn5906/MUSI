import requests
import schedule
import time
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET
import pandas as pd
import os


service_key = '6a5f787375034281bf07839da1fd0319'
current_date = datetime.now().strftime('%Y%m%d')


def daterange_yield(start_date, d_days):
    for n in range(d_days):
        yield start_date - timedelta(n)  # 값을 반환하면서 for 문 계속 진행

def get_performance_info(service_key, current_date, pages=10, rows=50):
    performance_list = []
    award_list = []
    
    start_date = datetime.strptime(current_date, '%Y%m%d')
    days = daterange_yield(start_date, 30)  # 공연 기간 중 최근30일이 포함된 공연

    for day in days:
        stdate = day.strftime('%Y%m%d')
        for page in range(1, pages + 1):
            # 공연중인 작품들 요청
            list_url = f'http://www.kopis.or.kr/openApi/restful/pblprfr?service={service_key}&stdate={stdate}&eddate={stdate}&cpage={page}&rows={rows}&prfstate=20'
            award_url = f'http://www.kopis.or.kr/openApi/restful/prfawad?service={service_key}&stdate={stdate}&eddate={stdate}&cpage={page}&rows={rows}'
            list_res = requests.get(list_url)  # 공연중인 작품들 요청
            award_res = requests.get(award_url)  # 공연중 & 공연완료 수상작 리스트 요청
            
            time.sleep(1)  # 서버 부하를 줄이기 위해 딜레이 추가
            if (list_res.status_code == 200) and (award_res.status_code == 200):
                list_root = ET.fromstring(list_res.content)
                award_root = ET.fromstring(award_res.content)
                list_items = list_root.findall('.//db')
                award_items = award_root.findall('.//db')
                
                if list_items or award_items:
                    for item in list_items:
                        prfid = item.find('mt20id').text if item.find('mt20id') is not None else 'N/A'
                        genrenm = item.find('genrenm').text if item.find('genrenm') is not None else 'N/A'
                        prfstate = item.find('prfstate').text if item.find('prfstate') is not None else 'N/A'
                        performance_list.append([prfid, genrenm, prfstate])
                    for item in award_items:
                        prfid = item.find('mt20id').text if item.find('mt20id') is not None else 'N/A'
                        awards = item.find('awards').text if item.find('awards') is not None else 'N/A'
                        award_list.append([prfid, awards])
                    
    list_column = ['PRFID', 'GENRENM','PRFSTATE']
    award_column = ['PRFID', 'AWARDS']
    df = pd.DataFrame(performance_list, columns=list_column)  # 공연중인 작품 전체
    list_df = df[(df['GENRENM'] == '뮤지컬') & (df['PRFSTATE']=='공연중')]
    award_df = pd.DataFrame(award_list, columns=award_column)
    
    total_df = pd.merge(award_df, list_df, on='PRFID', how='right')  # 공연중인 뮤지컬 리스트
    total_df=total_df.drop_duplicates()  # 중복행 제거 (공연중인 뮤지컬 리스트 + 수상내역 연결)
    
    current_dir = os.path.dirname(__file__)
    data_folder = os.path.join(current_dir, 'data')  # 현재 파일 경로 + /data
    os.makedirs(data_folder, exist_ok=True)
    
    date_folder = os.path.join(data_folder, f'data_{current_date}') # 현재 파일 경로 + /data/data_20240807 날짜별 폴더 생성
    os.makedirs(date_folder, exist_ok=True)
    
    save_path = os.path.join(date_folder, f'performance_list_{current_date}.csv')
    
    total_df.to_csv(save_path, index=False, encoding='utf-8-sig')
    return total_df;


def get_perf_details(dataFrame, service_key, current_date):
    prfId_list = dataFrame['PRFID'].to_list()  # 공연중인 뮤지컬 작품 리스트

    total_list = []
    
    # current_date의 날짜 형식이 'YYYYMMDD'라고 가정
    current_date_format = "%Y%m%d"
    current_date_obj = datetime.strptime(current_date, current_date_format)
    
    for prfid in prfId_list:  
        url = f"http://www.kopis.or.kr/openApi/restful/pblprfr/{prfid}?service={service_key}&newsql=Y"        
        res = requests.get(url)
        if res.status_code == 200:  # 정상적으로 데이터 받아온 경우
            root = ET.fromstring(res.content)
            item = root.find('.//db')
            
            if not item:
                continue
            
            prfpdto = item.find('prfpdto').text if item.find('prfpdto') is not None else 'N/A'
            prfpdfrom = item.find('prfpdfrom').text if item.find('prfpdfrom') is not None else 'N/A'
            date_format = "%Y.%m.%d"  # prfpdto와 prfpdfrom의 형식이 'YYYY.MM.DD'라고 가정
            
            # prfpdto를 datetime 객체로 변환
            if prfpdto != 'N/A':
                prfpdto_date = datetime.strptime(prfpdto, date_format)
                prfpdfrom_date = datetime.strptime(prfpdfrom, date_format)
                
                d_day = (prfpdto_date - current_date_obj).days  # d_day 계산

                # 종료 날짜가 오늘 날짜 이후인 경우만 데이터를 처리
                if prfpdto_date >= current_date_obj:     
                    mt20id = item.find('mt20id').text if item.find('mt20id') is not None else 'N/A'    # 타이틀
                    prfnm = item.find('prfnm').text if item.find('prfnm') is not None else 'N/A'
                    prfcast = item.find('prfcast').text if item.find('prfcast') is not None else 'N/A'
                    prfcrew = item.find('prfcrew').text if item.find('prfcrew') is not None else 'N/A'
                    prfruntime = item.find('prfruntime').text if item.find('prfruntime') is not None else 'N/A'
                    prfage = item.find('prfage').text if item.find('prfage') is not None else 'N/A'
                    entrpsnm = item.find('entrpsnm').text if item.find('entrpsnm') is not None else 'N/A'
                    pcseguidance = item.find('pcseguidance').text if item.find('pcseguidance') is not None else 'N/A'
                    poster = item.find('poster').text if item.find('poster') is not None else 'N/A'
                    mt10id = item.find('mt10id').text if item.find('mt10id') is not None else 'N/A'
                    fcltynm = item.find('fcltynm').text if item.find('fcltynm') is not None else 'N/A'
                    
                    styurls = item.find('styurls')
                    relates = item.find('relates')
                    
                    if styurls is not None:
                        styurl_text = [styurl.text for styurl in styurls.findall('styurl')]

                    if relates is not None:
                        relate_list = [
                        (relate.find('relatenm').text if relate.find('relatenm').text is not None else 'N/A',
                            relate.find('relateurl').text if relate.find('relateurl').text is not None else 'N/A')
                        for relate in relates.findall('relate')
                        ]
                    
                    total_list.append([mt20id, prfnm, prfpdfrom, prfpdto, d_day, prfcast, prfcrew, prfruntime, prfage, entrpsnm, pcseguidance, poster, relate_list, mt10id, fcltynm, styurl_text])
            else:
                continue

    if total_list:  # total_list가 비어있지 않을 때만 DataFrame을 생성하고 저장
        column_names = ['PRFID', 'PRFNM', 'PRFPDFROM', 'PRFPDTO', 'D_DAY', 'PRFCAST', 'PRFCREW', 'PRFRUNTIME', 'PRFAGE', 'ENTRPSNM', 'PCSEGUIDANCE', 'POSTER', 'RELATES', 'PLACEID', 'PLACENM' ,'INFO_URLS']
        df = pd.DataFrame(total_list, columns=column_names)
        
        current_dir = os.path.dirname(__file__)
        data_folder = os.path.join(current_dir, 'data')  # 현재 파일 경로 + /data
        os.makedirs(data_folder, exist_ok=True)
        
        date_folder = os.path.join(data_folder, f'data_{current_date}') # 현재 파일 경로 + /data/data_20240807 날짜별 폴더 생성
        os.makedirs(date_folder, exist_ok=True)
        
        save_path = os.path.join(date_folder, f'all_detail_list_{current_date}.csv')
        
        df.to_csv(save_path, index=False, encoding='utf-8-sig')
        return df  # 공연중인 뮤지컬 세부사항 데이터프레임 반환


#####################################################
# 공연 순위 가져오기
def get_boxoffice_rank(dataFrame, current_date, service_key):  # 공연중인 뮤지컬 세부사항 데이터프레임을 받아서 병합
    boxoffice_rank_list_30 = []
    boxoffice_rank_list_7 = []
    
    current_date_day = datetime.strptime(current_date, '%Y%m%d')
    days_30 = daterange_yield(current_date_day, 30)  # 30일 동안의 랭킹 가져오기
    
    for day in days_30:
        date = day.strftime('%Y%m%d')  # 20240701 형태의 날짜로 변환
        
        url = f"http://kopis.or.kr/openApi/restful/boxoffice?service={service_key}&ststype=week&date={date}"
        res = requests.get(url)
        
        if res.status_code == 200:  # 정상응답 받았을 경우
            root = ET.fromstring(res.content)
            items = root.findall('.//boxof')  # XML 형식의 데이터에서 boxof 태그 모두를 가져오기
            for item in items:
                if item.find('cate').text == '뮤지컬':  # 뮤지컬 내에서 높은 순위 순으로 크롤링
                    prfId = item.find('mt20id').text if item.find('mt20id') is not None else 'N/A'  # 공연 id
                    rnum = item.find('rnum').text if item.find('rnum') is not None else 'N/A'  # 전체 순위
                    boxoffice_rank_list_30.append([int(rnum), prfId])
    print('30일 크롤링 완료')
            
    days_7 = daterange_yield(current_date_day, 7)  # 7일 동안의 랭킹 가져오기
    for day in days_7:
        date = day.strftime('%Y%m%d')  # 20240701 형태의 날짜로 변환
        
        url = f"http://kopis.or.kr/openApi/restful/boxoffice?service={service_key}&ststype=week&date={date}"
        res = requests.get(url)
        
        if res.status_code == 200:  # 정상응답 받았을 경우
            root = ET.fromstring(res.content)
            items = root.findall('.//boxof')  # XML 형식의 데이터에서 boxof 태그 모두를 가져오기
            for item in items:
                if item.find('cate').text == '뮤지컬':  # 뮤지컬 내에서 높은 순위 순으로 크롤링
                    prfId = item.find('mt20id').text if item.find('mt20id') is not None else 'N/A'  # 공연 id
                    rnum = item.find('rnum').text if item.find('rnum') is not None else 'N/A'  # 전체 순위
                    boxoffice_rank_list_7.append([int(rnum), prfId])
    print('7일 크롤링 완료')
            
    column_names_7 = ['7DAYS RANK', 'PRFID']  # 전체 공연 순위, 공연id
    df_7days = pd.DataFrame(boxoffice_rank_list_7, columns=column_names_7)
    df_7days['7DAYS RANK'] = pd.to_numeric(df_7days['7DAYS RANK'], errors='coerce')  # total rank 열을 숫자형으로 다시 전환/ 값이 없으면 nan값으로 두기
    
    column_names_30 = ['30DAYS RANK', 'PRFID'] 
    df_30days = pd.DataFrame(boxoffice_rank_list_30, columns=column_names_30)
    df_30days['30DAYS RANK'] = pd.to_numeric(df_30days['30DAYS RANK'], errors='coerce')  # total rank 열을 숫자형으로 다시 전환/ 값이 없으면 nan값으로 두기
    
    average_rank_7days = df_7days.groupby('PRFID')[['7DAYS RANK']].mean().reset_index()
    average_rank_30days = df_30days.groupby('PRFID')[['30DAYS RANK']].mean().reset_index()
    
    # 디테일 공연 정보와 병합
    total_df = pd.merge(dataFrame, average_rank_7days, on='PRFID', how='left')
    # total_df=total_df.sort_values('AVG RANK')  # 순위순으로 오름차순 정렬
    final_merge_df = pd.merge(total_df, average_rank_30days, on='PRFID', how='left')
    
    # 일주일 순위 평균으로 정렬 후 순위 부여
    final_merge_df=final_merge_df.sort_values('7DAYS RANK')
    final_merge_df.loc[final_merge_df['7DAYS RANK'].notna(), '7DAYS RANK']=range(1, len(final_merge_df[final_merge_df['7DAYS RANK'].notna()])+1)
    
    # 한달 순위 평균 정렬 후 순위 부여
    final_merge_df=final_merge_df.sort_values('30DAYS RANK')
    final_merge_df.loc[final_merge_df['30DAYS RANK'].notna(), '30DAYS RANK']=range(1, len(final_merge_df[final_merge_df['30DAYS RANK'].notna()])+1)
    
    current_dir = os.path.dirname(__file__)
    data_folder = os.path.join(current_dir, 'data')  # 현재 파일 경로 + /data
    os.makedirs(data_folder, exist_ok=True)
    
    date_folder = os.path.join(data_folder, f'data_{current_date}') # 현재 파일 경로 + /data/data_20240807 날짜별 폴더 생성
    os.makedirs(date_folder, exist_ok=True)
    
    save_path = os.path.join(date_folder, f'daily_final_{current_date}.csv')
    final_merge_df.to_csv(save_path, index=False, encoding='utf-8-sig')
    
    ################# home 페이지의 순위 롤링 배너에서 사용
    top10_save_path = os.path.join(date_folder, f'top10_list_{current_date}.csv')
    top_10_df = final_merge_df[final_merge_df['30DAYS RANK'].notna()].head(10)
    top_10_df['AVG RANK_DESC']=(top_10_df.iloc[-1,-1]+top_10_df.iloc[0, -1])-top_10_df['30DAYS RANK']
    top_10_df.to_csv(top10_save_path, index=False, encoding='utf-8-sig')
    
    return total_df, top_10_df;


#############################################
# 공연시설 지역코드 가져오기
def get_hall_info(dataFrame, place_names, current_date, service_key):
    pages=15
    rows=30
    place_list=[]
    
    for place_name in place_names:
        for page in range(pages): 
            fclty_url=f'http://www.kopis.or.kr/openApi/restful/prfplc?service={service_key}&cpage={page}&rows={rows}&\
                shprfnmfct={place_name}'
            
            res=requests.get(fclty_url)
            
            if res.status_code == 200: # 정상 응답 받았을 경우
                root=ET.fromstring(res.content)
                items=root.findall('.//db')
               
                if items is not None:
                    for item in items:
                        place_id=item.find('mt10id').text if item.find('mt10id').text is not None else 'N/A'
                        place_name=item.find('fcltynm').text if item.find('fcltynm').text is not None else 'N/A'
                        sido_code=item.find('sidonm').text if item.find('sidonm').text is not None else 'N/A'
                        gugun_code=item.find('gugunnm').text if item.find('gugunnm').text is not None else 'N/A'
                        place_list.append([place_id, place_name, sido_code, gugun_code])
        
    column_names=['PLACEID','PLACENM','SI DO','GU GUN']
    df=pd.DataFrame(place_list, columns=column_names)
    total_df=pd.merge(dataFrame, df, on='PLACEID', how='left')  
    place_ids=total_df['PLACEID'].to_list()
    
    place_details=[]
    for placeId in place_ids:
        place_url = f'http://www.kopis.or.kr/openApi/restful/prfplc/{placeId}?service={service_key}'
        
        place_res=requests.get(place_url)
        if place_res.status_code == 200:
            root=ET.fromstring(place_res.content)
            item=root.find('.//db')
            
            if item is not None:
                address=item.find('adres').text if item.find('adres').text is not None else 'N/A'
                telno=item.find('telno').text if item.find('telno').text is not None else 'N/A'
                relateurl=item.find('relateurl').text if item.find('relateurl').text is not None else 'N/A'
                print('relate_url:', relateurl)
                restaurant=item.find('restaurant') if item.find('restaurant') is not None else 'N/A'
                cafe=item.find('cafe') if item.find('cafe') is not None else 'N/A'
                store=item.find('store') if item.find('store') is not None else 'N/A'
                nolibang=item.find('nolibang') if item.find('nolibang') is not None else 'N/A'
                parkbarrier=item.find('parkbarrier') if item.find('parkbarrier') is not None else 'N/A'
                restbarrier=item.find('restbarrier') if item.find('restbarrier') is not None else 'N/A'
                elevbarrier=item.find('elevbarrier') if item.find('elevbarrier') is not None else 'N/A'
                parkinglot=item.find('parkinglot') if item.find('parkinglot') is not None else 'N/A'
                place_details.append([placeId, address, telno, relateurl, restaurant, cafe, 
                                      store, nolibang, parkbarrier, restbarrier,
                                      elevbarrier, parkinglot])
    column_names=['PLACEID','ADRES','TELNO','RELATE URL','RESTAURANT','CAFE','STORE','NOLIBANG','PARK BARRIER','REST BARRIER',
                  'ELEV BARRIER','PARKINGLOT']
    detail_df=pd.DataFrame(place_details, columns=column_names)
    merged_df=pd.merge(total_df, detail_df, on='PLACEID', how='left')
    
    # 폴더에 저장
    current_dir = os.path.dirname(__file__)
    data_folder = os.path.join(current_dir, 'data')  # 현재 파일 경로 + /data
    os.makedirs(data_folder, exist_ok=True)
    
    date_folder = os.path.join(data_folder, f'data_{current_date}') # 현재 파일 경로 + /data/data_20240807 날짜별 폴더 생성
    os.makedirs(date_folder, exist_ok=True)
    
    save_path = os.path.join(date_folder, f'daily_final_{current_date}.csv') # 최종 파일 저장!!!!!!!
    merged_df.to_csv(save_path, encoding='utf-8-sig', index=False)
    result_df=pd.read_csv(save_path, encoding='utf-8-sig')
    result_df=result_df.drop_duplicates()
    result_df.to_csv(save_path, encoding='utf-8-sig', index=False)
    return total_df;



def job():
    current_date = datetime.now().strftime('%Y%m%d')
    print('현재 날짜:', current_date)
    all_performance_df = get_performance_info(service_key, current_date)
    print('all_performance_df 완료')
    ing_musical_df = get_perf_details(all_performance_df, service_key, current_date)
    print('ing_musical_df 완료')
    boxof_detail_df, rank_only_df = get_boxoffice_rank(ing_musical_df, current_date, service_key)
    print('boxof_detail_df 완료')
    place_names=boxof_detail_df['PLACENM'].to_list()
    print('place_names 완료')
    hall_detail_info=get_hall_info(boxof_detail_df, place_names,current_date, service_key)
    print('전체 완료')


job()



# 매일 19시에 실행 (kopis 정보 업데이트 시간 반영)
schedule.every().day.at("19:10").do(job)

while True:
    schedule.run_pending()
    time.sleep(1)
