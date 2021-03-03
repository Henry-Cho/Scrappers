from pymongo import MongoClient
import jwt
import datetime
import hashlib
import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template, jsonify, request, redirect, url_for
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta


app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config['UPLOAD_FOLDER'] = "./static/profile_pics"

SECRET_KEY = 'SPARTA'

# client = MongoClient('mongodb://test:test@localhost', 27017)

client = MongoClient('localhost', 27017)
db = client.scrappers


@app.route('/')
def home():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])

        return render_template('index.html')
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login", msg="로그인 정보가 존재하지 않습니다."))


@app.route('/login')
def login():
    msg = request.args.get("msg")
    return render_template('login.html', msg=msg)


@app.route('/user/<username>')
def user(username):
    # 각 사용자의 프로필과 글을 모아볼 수 있는 공간
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        status = (username == payload["id"])  # 내 프로필이면 True, 다른 사람 프로필 페이지면 False

        user_info = db.users.find_one({"username": username}, {"_id": False})
        return render_template('user.html', user_info=user_info, status=status)
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))


@app.route('/sign_in', methods=['POST'])
def sign_in():
    # 로그인
    username_receive = request.form['username_give']
    password_receive = request.form['password_give']

    pw_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
    result = db.users.find_one({'username': username_receive, 'password': pw_hash})

    if result is not None:
        payload = {
         'id': username_receive,
         'exp': datetime.utcnow() + timedelta(seconds=60 * 60 * 24)  # 로그인 24시간 유지
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')

        return jsonify({'result': 'success', 'token': token})
    # 찾지 못하면
    else:
        return jsonify({'result': 'fail', 'msg': '아이디/비밀번호가 일치하지 않습니다.'})


@app.route('/sign_up/save', methods=['POST'])
def sign_up():
    username_receive = request.form['username_give']
    password_receive = request.form['password_give']
    password_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
    doc = {
        "username": username_receive,                               # 아이디
        "password": password_hash,                                  # 비밀번호
        "profile_name": username_receive,                           # 프로필 이름 기본값은 아이디
        "profile_pic": "",                                          # 프로필 사진 파일 이름
        "profile_pic_real": "profile_pics/profile_placeholder.png", # 프로필 사진 기본 이미지
        "profile_info": ""                                          # 프로필 한 마디
    }
    db.users.insert_one(doc)
    return jsonify({'result': 'success'})


@app.route('/sign_up/check_dup', methods=['POST'])
def check_dup():
    username_receive = request.form['username_give']
    exists = bool(db.users.find_one({"username": username_receive}))
    return jsonify({'result': 'success', 'exists': exists})



@app.route('/saveBox')
def saveBox() :
    return render_template("saved.html")

@app.route('/api/list', methods=['GET'])
def show_news():
    db.finalPrac.remove({ });

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36'}
    data = requests.get('https://news.naver.com/', headers=headers)

    soup = BeautifulSoup(data.text, 'html.parser')

    trs = soup.select("#_rankingList0 > li")
    naver = "https://news.naver.com"

    for tr in trs:
        top_article_title = tr.select_one(r'div > div > div > a.list_tit.nclicks\(\'rig\.renws2\'\)').text
        top_article_src = tr.select_one(r'div > div > div > a.list_press.nclicks\(\'rig\.renws2pname\'\)').text
        top_article_img = tr.select_one('a > img')['src']

        top_article_img = top_article_img.replace('?type=nf88_60', '')
        # img src 가 nonetype 인 경우 대안 만들었습니당
        if top_article_img is None:
            top_article_img = "https://res-5.cloudinary.com/crunchbase-production/image/upload/c_lpad,f_auto,q_auto:eco/v1504499304/in36bktetqoapibgeabo.png"
        top_article_url_incomplete = tr.select_one(r'div > div > div > a.list_tit.nclicks\(\'rig\.renws2\'\)')['href']
        top_article_url = naver + top_article_url_incomplete
        top_article_logo = tr.select_one(r'div > div > div > a.list_press.nclicks\(\'rig\.renws2pname\'\) > span > img')['src']
        top_article_link_incomplete = tr.select_one(r'div > div > div > a.list_press.nclicks\(\'rig\.renws2pname\'\)')['href']
        top_article_link = naver + top_article_link_incomplete

        top_article_title = top_article_title.replace('"', '').replace('…', '')

        doc = {
            "top_article_title": top_article_title,
            "top_article_src": top_article_src,
            "top_article_img": top_article_img,
            "top_article_url": top_article_url,
            "top_article_logo": top_article_logo,
            "top_article_link": top_article_link
        }
        db.finalPrac.insert_one(doc)


    news_show = list(db.finalPrac.find({}, {'_id': False}))
    return jsonify({'news_give': news_show})



@app.route('/api2/list', methods=['GET'])
def show_news2():
    db.finalPrac2.remove({ });

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36'}
    data = requests.get('https://news.daum.net/', headers=headers)

    soup = BeautifulSoup(data.text, 'html.parser')

    trs = soup.select("#cSub > div > ul > li")
    # cSub > div > ul > li:nth-child(1) > div.item_issue > div > strong > a
    # cSub > div > ul > li:nth-child(1) > div.item_issue > a > img
    # cSub > div > ul > li:nth-child(1) > div.item_issue > div > span
    # cSub > div > ul > li:nth-child(1) > div.item_issue > div > strong > a

    for tr in trs:
        title = tr.select_one(r'div.item_issue > div > strong > a').text
        url = tr.select_one(r'div.item_issue > div > strong > a')['href']
        img = tr.select_one('div.item_issue > a > img')['src']
        newspaper = tr.select_one('div.item_issue > div > span').text

        title = title.replace('"', '').replace('…', '')

        doc = {
            "title": title,
            "img":img,
            "url": url,
            "newspaper": newspaper,
        }
        db.finalPrac2.insert_one(doc)


    news_show2 = list(db.finalPrac2.find({}, {'_id': False}))
    return jsonify({'news_give2': news_show2})


@app.route('/save', methods=['POST'])
def save():
    url_receive = request.form['url_give']
    img_receive = request.form['img_give']
    title_receive = request.form['title_give']
    newspaper_receive = request.form['newspaper_give']

    doc = {
        'title': title_receive,
        'img': img_receive,
        'url' : url_receive,
        'newspaper' : newspaper_receive,
        "like_counts": 0,
        "review_counts" : 0
    }

    db.saveNews.insert_one(doc)

    return jsonify({'msg': '저장 완료!'})

@app.route('/showSaveNews', methods=['GET'])
def showSaveNews():
    showSave = list(db.saveNews.find({}, {'_id': False}))
    return jsonify({'list_saveBox': showSave})

@app.route('/showSaveNews/like_sort', methods=['GET'])
def showSaveNews_likesort():
    sort_like = list(db.saveNews.find({}, {'_id': False}).sort('like_counts', -1))
    return jsonify({'list_saveBox': sort_like})

@app.route('/showSaveNews/recent', methods=['GET'])
def showSaveNews_recent():
    sort_recent = list(db.saveNews.find({}, {'_id': False}))
    return jsonify({'list_saveBox': sort_recent})

@app.route('/showSaveNews/review', methods=['GET'])
def showSaveNews_review():
    sort_review = list(db.saveNews.find({}, {'_id': False}).sort('review_counts', 1))
    return jsonify({'list_saveBox': sort_review})

@app.route('/showSaveNews/like', methods=['POST'])
def like_news():
    url_receive = request.form['url_give']
    existing_value = db.saveNews.find_one({"url": url_receive})['like_counts']
    db.saveNews.update_one({"url": url_receive}, {"$set": { 'like_counts': existing_value+1 }})
    #incremented_value = db.mystar.find_one({"name": title_receive})['like']
    return jsonify({'msg': "🔥 추가 완료!"})


# 리뷰 받아 오기
@app.route('/review', methods=['POST'])
def write_review():
    review_receive = request.form['review_give']
    url_receive = request.form['url_give']

    target_url = db.saveNews.find_one({'url': url_receive})
    current_like = target_url['review_counts']

    new_like = current_like + 1

    doc = {'review': review_receive, 'url': url_receive}
    db.newsReview.insert_one(doc)

    db.saveNews.update_one({'url': url_receive}, {'$set': { 'review_counts': new_like}})

    return jsonify({'msg': '작성 완료!'})

# 리뷰 보여 주기
@app.route('/reviews', methods=['POST'])
def read_reviews():
    url_receive = request.form['url_give']
    reviews = list(db.newsReview.find({'url' : url_receive}, {'_id': False}))
    return jsonify({'all_reviews': reviews})


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)