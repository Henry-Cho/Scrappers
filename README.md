# Scrappers

팀 미니프로젝트

https://www.youtube.com/watch?v=RM29QBPca90&t=1s

![image](https://user-images.githubusercontent.com/78591345/113448341-98f0e100-9436-11eb-847d-af3c819bd772.jpg)



## 목차
1. 구현한 기능
2. API
3. 코드 리뷰
4. 느낀점


<br />
<br />

## 1. 내가 구현한 기능
- 로그인 & 회원가입

- 네이버 및 다음 기사 1~4위 크롤링

- 기사 저장

- 댓글 & 좋아요

- AWS 배포

<br />
<br />
팀이 구현한 기능

- 프론트단 화면
- CSS 효과
- 카드 양식

레이아웃 & 노션 작업
<details> <summary> </summary> <div markdown="1">
![image](https://user-images.githubusercontent.com/78591345/113448337-97bfb400-9436-11eb-886a-dc99cbd0a248.jpeg)
![image](https://user-images.githubusercontent.com/78591345/113448335-97bfb400-9436-11eb-8f68-f7831c61c6ad.PNG)
    </div>
</details>


<br />
<br />

## 2. API

<details> <summary> </summary> <div markdown="1">

| **메인 페이지**      |                  |                        |                           |
| -------------------- | ---------------- | ---------------------- | ------------------------- |
| **기능**             | **Method**       | **url**                | **request & reponse**     |
| 로그인 & 회원가입    | POST             | /api/login             | ID/PW                     |
| GET                  | /user/<username> |                        |                           |
| POST                 | /sign_in         | mytoken                |                           |
| POST                 | /sign_up/save    |                        |                           |
| 네이버 실시간 크롤링 | GET              | /api/list              | news_give:news_show       |
| 다음 실시간 크롤링   | GET              | /api2/list             | news_give2:news_show2     |
| 뉴스 저장            | POST             | /save                  | msg : 저장 완료!          |
|                      |                  |                        |                           |
| **SaveBox**          |                  |                        |                           |
| **기능**             | **Method**       | **url**                | **request & reponse**     |
| 페이지이동           | GET              | /saveBox               |                           |
| 저장한 뉴스 보여주기 | GET              | /showSaveNews          | list_saveBox:showSave     |
| 좋아요순 정렬        | GET              | /showSaveNews_likesort | list_saveBox:sort_like    |
| 최신순 정렬          | GET              | /showSaveNews/recent   | /list_saveBox:sort_recent |
| 리뷰순 정렬          | GET              | /showSaveNews          | list_saveBox:sort_review  |
| 좋아요 클릭          | POST             | /showSavenews/like     | msg: 좋아요 추가 완료!    |
| 리뷰 저장            | POST             | /review                | msg : 저장완료            |
| 리뷰 보여주기        | POST             | /reviews               | all_reviews:reviews       |

</div>
</details>

<br />
<br />

## 3 . 코드 리뷰


로그인 & 회원가입

<details> <summary> </summary> <div markdown="1">
    
![image](https://user-images.githubusercontent.com/78591345/113448339-98584a80-9436-11eb-8242-2a6f5b9a1d06.jpg)

```python
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
```

JWT토큰을 이용해서 로컬스토리지에 토큰을 넣는 방식으로 로그인을 진행했다.

비밀번호는 파이썬 Hash를 이용하여 암호화하여 db에 저장했다.
</div>
</details>



</br>

크롤링 및 기사저장

<details> <summary> </summary> <div markdown="1">
    
    
 ![image](https://user-images.githubusercontent.com/78591345/113448341-98f0e100-9436-11eb-847d-af3c819bd772.jpg)

```python
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
        if top_article_img == None:
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
```

네이버와 다음의 실시간 랭킹을 크롤링해왔다.

해당 부분은 네이버며 다음도 비슷하다.

다만 동적URL을 크롤링하는게 어려워서, 조금 꼼수를 부렸다.

일단 1~4위 기사를 DB에 저장해서 넣고, /home에 뿌려준다.

그리고 다시 넣을 때는 기존의 DB를 전부 삭제하고 넣어주는 방식으로  DB엔 기사가 안 쌓이고, 이용자들에겐 시간표시와 함께 크롤링 되어 마치 실시간으로 긁어오는 것처럼 보이게 했다.



기사저장

![image](https://user-images.githubusercontent.com/78591345/113448332-95f5f080-9436-11eb-937b-30a2061e3011.jpg)

```python
@app.route('/save', methods=['POST'])
def save():
    url_receive = request.form['url_give']
    img_receive = request.form['img_give']
    title_receive = request.form['title_give']
    newspaper_receive = request.form['newspaper_give']

    today = datetime.now()
    mytime = today.strftime('%Y-%m-%d')

    doc = {
        'title': title_receive,
        'img': img_receive,
        'url' : url_receive,
        'newspaper' : newspaper_receive,
        "like_counts": 0,
        "review_counts" : 0,
        'mytime' : mytime
    }

    db.saveNews.insert_one(doc)

    return jsonify({'msg': '저장 완료!'})
```

기사 저장은 평범하게 req로 받아와서 db에 넣고 /save에서 뿌려주는 걸로 구현했다.
</div>
</details>


</br>

댓글 남기기

<details> <summary> </summary> <div markdown="1">

![image](https://user-images.githubusercontent.com/78591345/113448340-98584a80-9436-11eb-9cff-147016a11038.jpg)

```python
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
    return jsonify({'all_reviews': reviews})뷰
```

로그인 안 한 사람도 리뷰를 남길 수 있게 했다.

지금은 할 수 있지만, 당시엔 파이썬 쓰는게 너무 어렵고 이해가 잘 안가서 로그인한 사람만 본인의 닉네임과 함께 댓글남기는걸 할 수가 없었다.

요새 Node를 쓸 땐 로컬스토리지에 있는 토큰을 서버로 보낸 뒤에 jwt토큰을 다시 풀어낸 후 닉네임을 찾고 그 닉네임을 클라이언트에 내려줘서 잘 쓰고 있다.
</div>
</details>



<br />
<br />

# 4 . 느낀점

<details> <summary> </summary> <div markdown="1">
    
2021.02.10에 코딩을 시작했으니 거의 2주간? 공부 열심히 하고, 처음으로 팀 프로젝트를 진행해본건데, 생각보다 너무 재밌었고 압박감이 상당했다.

노션도 직접 만들어 팀과 공유해서 작업했는데, 서로의 작업을 명료하게 볼 수 있고, 필요한 부분을 찾아갈 수 있어서 편했다.

제한 시간 내에 프로젝트를 완수해야한다는 압박감과 부담감이 어떤 즐거움으로 다가왔다. 팀원들도 모두 잘 협조해서 모든 조 중에서 제일 일찍 끝내고 다른 부분들을 공부했던 것 같다.

코드 자체에 대한 이해가 있는게 아니라, 이 코드를 여기다 넣으면 이렇게 되겠지? 변수를 이렇게 바꿔야겠지? 등 Make의 의미를 두고 만든 것 같다. 사실 이해를 할 만한 실력도 아니고, 그냥 적당한 곳에 적당한 것을 붙여넣거나, 또 검색해서 넣어보거나 하는 식으로 만들어갔던 것 같다.

요새는 이해하려고 많이 노력하여 저때보단 나아진 것 같다.
</div>
</details>
