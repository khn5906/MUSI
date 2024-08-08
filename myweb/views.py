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
import logging
import pandas as pd
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)
current_date = datetime.now().strftime('%Y%m%d')

def home(request):
    df=pd.read_csv(f'myweb/data/data_{current_date}/top10_list_{current_date}.csv', encoding='utf-8-sig')
    df['POSTER']=df['POSTER'].apply(lambda x : x[4:])
    df['POSTER'] = df['POSTER'].apply(lambda x: 'https' + x if x.startswith('://') else x)
    
    rank_df=df[['PRFID','PRFNM','POSTER']]
    # print(rank_df['POSTER'])
    rank_list=rank_df.values.tolist()
    print('------------------')
    print(rank_list)
    # [poster, name, prfid] 리스트에 넣기
    
    content={
        'rank_list':rank_list,
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
            msg += "location.href='http://localhost:8000/login/';";
            msg += "</script>";
            return HttpResponse(msg);
        except:
            msg = "<script>";
            msg += "alert('같은 아이디가 존재합니다. 다시 가입하세요.');";
            msg += "location.href='http://localhost:8000/register/';";
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
            msg += "location.href='http://localhost:8000/home/';";
            msg += "</script>";
            return HttpResponse(msg);
        
        else:
            msg = "<script>";
            msg += "alert('로그인 아이디/비밀번호가 틀립니다. 다시 로그인 하세요.');";
            msg += "location.href='http://localhost:8000/login/';";
            msg += "</script>";
            return HttpResponse(msg);

def logout(request):  #로그아웃
    auth.logout(request);
    return render(request, "registration/logged_out.html");

def myinfo(request):
    return render(request, "registration/myinfo.html");

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
            msg += "location.href='http://localhost:8000/contact';";
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
            email_body2 = f"{name}님, 안녕하세요.\n\n문의해 주셔서 감사합니다.\n고객님의 문의를 잘 접수하였습니다.\n최대한 빠른 시일 내에 답변드리겠습니다.\n\n MUSI 드림"
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
            msg += "location.href='http://localhost:8000/contact';";
            msg += "</script>";
            return HttpResponse(msg)
        
        msg = "<script>";
        msg += "alert('메일전송을 완료했습니다.');";
        msg += "location.href='http://localhost:8000/';";
        msg += "</script>";
        return HttpResponse(msg)
    
def tableau_musi(request):
    return render(request, 'tableau_musi.html');

def story(request):
    file_path=f'myweb/data/data_{current_date}/final_musical_detail_{current_date}.csv'
    df=pd.read_csv(file_path, encoding='utf-8-sig')
    return render(request, 'story.html');


import pandas as pd
from datetime import datetime, timedelta
from django.shortcuts import render

def reservation(request, prfid):
    current_date = datetime.now().strftime('%Y%m%d')
    
    def read_and_process_file(date_str):
        df = pd.read_csv(f'myweb/data/data_{date_str}/final_musical_detail_{date_str}.csv', encoding='utf-8-sig')
        df['POSTER'] = df['POSTER'].apply(lambda x: 'https' + x[4:] if x.startswith('http') else x)
        return df
    
    try:
        df = read_and_process_file(current_date)
    except Exception as e:
        print(f'예외발생: {e}')
        yesterday = (datetime.strptime(current_date, '%Y%m%d') - timedelta(1)).strftime('%Y%m%d')
        df = read_and_process_file(yesterday)
    
    ids = df['PRFID'].tolist()
    prfid_idx = next((idx for idx, id in enumerate(ids) if prfid == id), None)
    
    if prfid_idx is not None:
        rlt_list = df.iloc[prfid_idx, :].tolist()
        col_list = df.columns.tolist()
        
        content_dict = {col: rlt for col, rlt in zip(col_list, rlt_list)}
        
        content = {
            'content_dict': content_dict,
        }
        print('----------------')
        print(content_dict)
        return render(request, 'reservation.html', content)
    else:
        return render(request, 'error.html', {'message': 'Requested PRFID not found'})
