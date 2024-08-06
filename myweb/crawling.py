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
        yield start_date - timedelta(days=n)  # 값을 반환하면서 for 문 계속 진행

def get_performance_info(service_key, current_date, pages=10, rows=50):
    performance_list = []
    award_list = []
    
    start_date = datetime.strptime(current_date, '%Y%m%d')
    days = daterange_yield(start_date, 30)  # 정상 작동시 3개월동안의 공연 정보로 진행하기

    for day in days:
        print('------day:', day, '---------')
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
                    print(f'prfid: {prfid}, genrenm: {genrenm}, awards: {awards}')
                    
    list_column = ['PRFID', 'GENRENM','PRFSTATE']
    award_column = ['PRFID', 'AWARDS']
    df = pd.DataFrame(performance_list, columns=list_column)  # 공연중인 작품 전체
    list_df = df[(df['GENRENM'] == '뮤지컬') & (df['PRFSTATE']=='공연중')]
    award_df = pd.DataFrame(award_list, columns=award_column)
    
    total_df = pd.merge(award_df, list_df, on='PRFID', how='right')  # 공연중인 뮤지컬 리스트
    total_df=total_df.drop_duplicates()  # 중복행 제거 (공연중인 뮤지컬 리스트 + 수상내역 연결)
    
    current_dir = os.path.dirname(__file__)
    data_dir = os.path.join(current_dir, 'data')  # 현재 파일 경로 + /data
    os.makedirs(data_dir, exist_ok=True)
    
    save_path = os.path.join(data_dir, f'performance_list_{current_date}.csv')
    total_df.to_csv(save_path, index=False, encoding='utf-8-sig')
    print('get performance list: ', total_df)
    return total_df

def get_perf_details(dataFrame, service_key, current_date):
    prfId_list = dataFrame['PRFID'].to_list()  # 공연중인 뮤지컬 작품 리스트

    total_list = []
    
    for prfid in prfId_list:  
        url = f"http://www.kopis.or.kr/openApi/restful/pblprfr/{prfid}?service={service_key}&newsql=Y"        
        res = requests.get(url)
        if res.status_code == 200:  # 정상적으로 데이터 받아온 경우
            root = ET.fromstring(res.content)
            item = root.find('.//db')
            
            if not item:
                continue
        
            mt20id = item.find('mt20id').text if item.find('mt20id') is not None else 'N/A'    # 타이틀
            prfnm = item.find('prfnm').text if item.find('prfnm') is not None else 'N/A'
            prfpdfrom = item.find('prfpdfrom').text if item.find('prfpdfrom') is not None else 'N/A'
            prfpdto = item.find('prfpdto').text if item.find('prfpdto') is not None else 'N/A'
            prfcast = item.find('prfcast').text if item.find('prfcast') is not None else 'N/A'
            prfcrew = item.find('prfcrew').text if item.find('prfcrew') is not None else 'N/A'
            prfruntime = item.find('prfruntime').text if item.find('prfruntime') is not None else 'N/A'
            prfage = item.find('prfage').text if item.find('prfage') is not None else 'N/A'
            entrpsnm = item.find('entrpsnm').text if item.find('entrpsnm') is not None else 'N/A'
            pcseguidance = item.find('pcseguidance').text if item.find('pcseguidance') is not None else 'N/A'
            poster = item.find('poster').text if item.find('poster') is not None else 'N/A'
            mt10id = item.find('mt10id').text if item.find('mt10id') is not None else 'N/A'
            
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
                
            total_list.append([mt20id, prfnm, prfpdfrom, prfpdto, prfcast, prfcrew, prfruntime, prfage, entrpsnm, pcseguidance, poster, relate_list, mt10id, styurl_text])

    column_names = ['PRFID', 'PRFNM', 'PRFPDFROM', 'PRFPDTO', 'PRFCAST', 'PRFCREW', 'PRFRUNTIME', 'PRFAGE', 'ENTRPSNM', 'PCSEGUIDANCE', 'POSTER', 'RELATES', 'PLACEID', 'INFO URLS']
    df = pd.DataFrame(total_list, columns=column_names)
    
    current_dir = os.path.dirname(__file__)
    data_dir = os.path.join(current_dir, 'data')  # 현재 파일 경로 + /data
    os.makedirs(data_dir, exist_ok=True)
    
    save_path = os.path.join(data_dir, f'all_detail_list_{current_date}.csv')
    df.to_csv(save_path, index=False, encoding='utf-8-sig')
    print('완료')
    return df  # 공연중인 뮤지컬 세부사항 데이터프레임 반환

def get_boxoffice_rank(dataFrame, current_date, service_key):  # 공연중인 뮤지컬 세부사항 데이터프레임을 받아서 병합
    boxoffice_rank_list = []
    
    current_date_day = datetime.strptime(current_date, '%Y%m%d')
    days = daterange_yield(current_date_day, 7)  # current_date: 일주일의 시작일
    
    for day in days:
        print('------day:', day, '---------')
        date = day.strftime('%Y%m%d')  # 20240701 형태의 날짜로 변환
        url = f"http://kopis.or.kr/openApi/restful/boxoffice?service={service_key}&ststype=week&date={date}"
        res = requests.get(url)
        
        if res.status_code == 200:  # 정상응답 받았을 경우
            root = ET.fromstring(res.content)
            items = root.findall('.//boxof')  # XML 형식의 데이터에서 boxof 태그 모두를 가져오기
            for item in items:
                if item.find('cate').text == '뮤지컬':  # 뮤지컬 내에서 높은 순위 순으로 크롤링
                    prfId = item.find('mt20id').text if item.find('mt20id') is not None else 'N/A'  # 공연 id
                    rnum = item.find('rnum').text if item.find('rnum') is not None else 'N/A'
                    boxoffice_rank_list.append([int(rnum), prfId])
            print('크롤링 완료')

    column_names = ['TOTAL RANK', 'PRFID']  # 전체 공연 순위, 공연id
    df = pd.DataFrame(boxoffice_rank_list, columns=column_names)
    df['TOTAL RANK'] = pd.to_numeric(df['TOTAL RANK'], errors='coerce') 
    
    average_rank_df = df.groupby('PRFID', as_index=False)[['TOTAL RANK']].mean().reset_index()
    average_rank_df.rename(columns={'TOTAL RANK': 'AVG RANK'}, inplace=True)
    
    # 디테일 공연 정보와 병합
    total_df = pd.merge(dataFrame, average_rank_df, on='PRFID', how='left')
    total_df=total_df.sort_values('AVG RANK')  # 순위순으로 오름차순 정렬
    
    current_dir = os.path.dirname(__file__)
    data_dir = os.path.join(current_dir, 'data')  # 현재 파일 경로 + /data
    os.makedirs(data_dir, exist_ok=True)
    
    save_path = os.path.join(data_dir, f'final_musical_detail_{current_date}.csv')
    total_df.to_csv(save_path, index=False, encoding='utf-8-sig')
    
    print('완료')
    current_dir = os.path.dirname(__file__)
    data_dir = os.path.join(current_dir, 'data')  # 현재 파일 경로 + /data
    os.makedirs(data_dir, exist_ok=True)
    
    top10_save_path = os.path.join(data_dir, f'musical_top10_{current_date}.csv')
    top_10_df = total_df[total_df['AVG RANK'].notna()].head(10)
    top_10_df['AVG RANK_DESC']=(top_10_df.iloc[-1,-1]+top_10_df.iloc[0, -1])-top_10_df['AVG RANK']
    top_10_df.to_csv(top10_save_path, index=False, encoding='utf-8-sig')
    
    return total_df, top_10_df;

def job():
    current_date = datetime.now().strftime('%Y%m%d')
    all_performance_df = get_performance_info(service_key, current_date)
    ing_musical_df = get_perf_details(all_performance_df, service_key, current_date)
    final_detail_df, rank_only_df = get_boxoffice_rank(ing_musical_df, current_date, service_key)
    return final_detail_df, rank_only_df;

job()