from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib import auth
from django.contrib.auth.hashers import check_password
from django.urls import reverse
from django.core.mail import EmailMessage
from django.core.mail import EmailMessage
from django.shortcuts import render
from django.conf import settings
import logging, ast
import pandas as pd
from datetime import datetime, timedelta
from django.shortcuts import render


logger = logging.getLogger(__name__)
current_date = datetime.now().strftime('%Y%m%d')


def read_and_process_file(date_str, file_path):
        path=f'myweb/data/data_{date_str}/'
        path+=file_path
        df = pd.read_csv(path, encoding='utf-8-sig')
        df['POSTER'] = df['POSTER'].apply(lambda x: 'https' + x[4:] if x.startswith('http') else x)
        return df;


def home(request):
    try:
        file_path=f'top10_list_{current_date}.csv'
        df= read_and_process_file(current_date, file_path)
    
    except Exception as e:
        print(f'예외발생: {e}')
        yesterday = (datetime.strptime(current_date, '%Y%m%d') - timedelta(1)).strftime('%Y%m%d')
        file_path=f'top10_list_{yesterday}.csv'
        df = read_and_process_file(yesterday, file_path)
    
    rank_df=df[['PRFID','PRFNM','POSTER','D_DAY']]
    rank_list=rank_df.values.tolist()
    # [poster, name, prfid] 리스트에 넣기

    # CSV 파일 로드
    df = pd.read_csv('review_data.csv')  # 실제 경로로 수정

    # 중복되지 않는 title2 값 추출
    titles = df['title2'].unique()
    
    content={
        'rank_list':rank_list,
        'titles': titles,
    }
    return render(request, 'home.html', content)


def createAccount(request):  #회원가입
    if request.method == 'GET':
        return render(request, "registration/register.html")
    elif request.method == 'POST':
        username = request.POST.get("username");        
        password = request.POST.get("pwd1");

        try:
            User.objects.create_user(username=username, password=password)
            msg = "<script>";
            msg += "alert('회원가입 되었습니다.');";
            msg += "location.href='/login/';";
            msg += "</script>";
            return HttpResponse(msg);
        except:
            msg = "<script>";
            msg += "alert('같은 아이디가 존재합니다. 다시 가입하세요.');";
            msg += "location.href='/register/';";
            msg += "</script>";
            return HttpResponse(msg);

def login(request):  #로그인
    if request.method == 'GET':
        return render(request, 'registration/login.html');
    
    elif request.method == 'POST':
        username = request.POST['username']
        password = request.POST['pwd']

        #user = User.objects.get(username=username, password=password);
        user = auth.authenticate(request, username=username, password=password);
        print(user)
        if user is not None:
            auth.login(request, user)
            
            msg = "<script>";
            msg += "alert('로그인 되었습니다.');";
            msg += "location.href='/home/';";
            msg += "</script>";
            return HttpResponse(msg);
        
        else:
            msg = "<script>";
            msg += "alert('로그인 아이디/비밀번호가 틀립니다. 다시 로그인 하세요.');";
            msg += "location.href='/login/';";
            msg += "</script>";
            return HttpResponse(msg);

def logout(request):  #로그아웃
    auth.logout(request);
    return render(request, "registration/logged_out.html");

def myinfo(request):
    user = request.user;
        
    if user.is_active :
        if request.method == 'GET':
            userInfo = User.objects.get(username=user.username);            
            content = {
            'userInfo':userInfo    }
            return render(request, 'registration/myinfo.html', content)
        
        else: # POST 로 접근            
            origin = request.POST['origin']            

            # check_password(평문, 해쉬된암호)
            if check_password(origin, user.password):          
                password = request.POST.get('pwd1')            
                userInfo.set_password(password)
                userInfo.save()
                msg = "<script>";
                msg += "alert('회원정보 수정이 완료되었습니다. 다시 로그인 해주세요.');";
                msg += "location.href='/login/';";
                msg += "</script>";
                return HttpResponse(msg);     
            else:
                msg = "<script>";
                msg += "alert('비밀번호가 틀려 회원정보를 수정 할 수 없습니다.');";
                msg += "location.href='/myinfo/';";
                msg += "</script>";
                return HttpResponse(msg);
    else:
        msg = "<script>";
        msg += "alert('회원탈퇴가 완료되었습니다. 다음에 또 뵙겠습니다♥');";
        msg += "location.href='/home';";
        msg += "</script>";
        return HttpResponse(msg);
    
def myinfoDel(request):    
    User.objects.get(username = request.user.username).delete();
    # 사용자 정보를 삭제합니다.
    User.delete()
    msg = "<script>";
    msg += "alert('회원정보를 삭제했습니다.');";
    msg += 'location.href="/home/";';
    msg += "</script>";
    return HttpResponse(msg);
    

def contact(request):
    
    if request.method == 'GET':
        return render(request, "contact.html")
    
    elif request.method == 'POST':
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        name = request.POST.get('name')
        email = request.POST.get('email')

        if (subject == "" or message == "" or name=="" or email==""):
            msg = "<script>";
            msg += "alert('내용을 전부 입력해주세요.');";
            msg += "location.href='/contact';";
            msg += "</script>";
            return HttpResponse(msg);
    
        else:      
            # 이메일 제목 설정 (예: "Subject - Name")
            email_subject = f"{subject} - {name}"
            
            # 이메일 본문 내용 설정
            email_body = f"Message from {name} - {email}\n\n제목:{subject}\n내용:{message}"
            
            email_to_musi = EmailMessage(
                email_subject,  # 제목
                email_body,     # 본문 내용
                to=['khn5906puruni.com@gmail.com'],  # 받는 이메일
            )

            email_subject2 = f"[MUSI] {name}님, 문의를 잘 접수하였습니다."
            email_body2 = (
                f"{name}님, 안녕하세요.\n\n"
                "문의해 주셔서 감사합니다.\n"
                "고객님의 문의를 잘 접수하였습니다.\n"
                "최대한 빠른 시일 내에 답변드리겠습니다.\n\n"
                "MUSI 드림"
                " ----------------------------------------------------\n\n"
                f"<문의내용>\n제목: {subject}\n내용:\n{message}")
            email_to_cos = EmailMessage(
                email_subject2,  
                email_body2,     
                to=[email],  
            )
        
        try:
            email_to_musi.send() 
            email_to_cos.send() 

        except Exception as e:
            logger.error(f"Failed to send email to admin: {e}")
            msg = "<script>";
            msg += f"alert('관리자에게 메일 전송을 실패했습니다. 다시 시도해주세요.');";
            msg += "location.href='/contact';";
            msg += "</script>";
            return HttpResponse(msg)
        
        msg = "<script>";
        msg += "alert('메일전송을 완료했습니다.');";
        msg += "location.href='/';";
        msg += "</script>";
        return HttpResponse(msg)
    
def tableau_musi(request):
    return render(request, 'tableau_musi.html');

#################################################### 민정 수정_20240810
def story(request):
    current_date = datetime.now().strftime('%Y%m%d')

    try:
        # 전체 공연 리스트 (제목, 공연장, 날짜, 자세히보기 버튼 -> reservation 페이지로 이동)
        file_path=f'myweb/data/data_{current_date}/daily_final_{current_date}.csv'
        df = pd.read_csv(file_path, encoding='utf-8-sig')
        df['POSTER'] = df['POSTER'].apply(lambda x: 'https' + x[4:] if x.startswith('http') else x)
    
    except Exception as e:
        print(f'예외발생: {e}')
        yesterday = (datetime.strptime(current_date, '%Y%m%d') - timedelta(1)).strftime('%Y%m%d')
        file_path = f'myweb/data/data_{yesterday}/daily_final_{yesterday}.csv'
        df = pd.read_csv(file_path, encoding='utf-8-sig')
        df['POSTER'] = df['POSTER'].apply(lambda x: 'https' + x[4:] if x.startswith('http') else x)

    query = request.GET.get('query', '')
    print('query:', query)
    
    # 검색어가 있을 경우 필터링
    if query:
        df = df[df['PRFNM'].str.contains(query, case=False)]

    # 검색 결과가 없을 경우
    if df.empty:
        content = {
            'no_results': True,
        }
    else:
        # 페이지에 필요한 컬럼만 가져오기
        mainPage_df = df[['PRFID','PRFNM','PLACENM_x', 'PRFPDFROM','PRFPDTO','POSTER','D_DAY']]
        mainPage_prfs = mainPage_df.values.tolist()
        contents_list = []

        col_names = mainPage_df.columns
        for val in mainPage_prfs:
            im_dict = {}
            for col, v in zip(col_names, val):
                im_dict[col] = v
            contents_list.append(im_dict)

        content = {
            'contents_list': contents_list,
        }

    return render(request, 'story.html', content)


##########################################################
def reservation(request, prfid):
    current_date = datetime.now().strftime('%Y%m%d')
    
    try:
        file_path=f'daily_final_{current_date}.csv'
        df = read_and_process_file(current_date, file_path)
        
    except Exception as e:
        print(f'예외발생: {e}')
        yesterday = (datetime.strptime(current_date, '%Y%m%d') - timedelta(1)).strftime('%Y%m%d')
        file_path=f'daily_final_{yesterday}.csv'
        df = read_and_process_file(yesterday, file_path)
    
    ids = df['PRFID'].tolist()
    prfid_idx = next((idx for idx, id in enumerate(ids) if prfid == id), None)
    
    if prfid_idx is not None:
        rlt_list = df.iloc[prfid_idx, :].tolist()  # 해당되는 열의 모든 정보 가져오기
        col_list = df.columns.tolist()
        
        content_dict = {col: rlt for col, rlt in zip(col_list, rlt_list)}
        content_dict['PCSEGUIDANCE']=content_dict.get('PCSEGUIDANCE').replace(', ', '<br>')
        
        content_dict['RELATES'] = ast.literal_eval(content_dict['RELATES'])  # ast 모듈로 텍스트를 리스트로 변환
        content_dict['INFO_URLS'] = ast.literal_eval(content_dict['INFO_URLS'])
        content_dict['INFO_URLS'] = [url for url in content_dict['INFO_URLS']]
        
        
        url_sites=content_dict['RELATES']
        
        content_dict['RELATES'] = { site: url for site, url in url_sites }
        print(content_dict)
        content = {
            'content_dict': content_dict,
        }
        print('----------------')
        print(content_dict)
        return render(request, 'reservation.html', content)
    else:
        return render(request, 'error.html', {'message': 'Requested PRFID not found'})