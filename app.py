# import need packages
import os
import requests
from bs4 import BeautifulSoup
import urllib3

import re
import time
import random
import datetime
from imgurpython import ImgurClient

# linebot-sdk packages
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import *


app = Flask(__name__)

# Line Messenger API for your channels
Channel_Access_Token = "Line developers 的 Channel_Access_Token"
line_bot_api = LineBotApi(Channel_Access_Token)

# Channel Secret
Channel_Secret = "Line developers 的 Channel_Secret"
handler = WebhookHandler(Channel_Secret)

# Imgur 圖片網站 api
client_id = 'imgur 帳號 client_id'
client_secret = 'imgur 帳號 client_secret'
access_token = 'postman get access_token'
refresh_token = 'postman get refresh_token'
album_id = 'album網址/a/後方英文'

# requests.get 偽裝器
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.63 Safari/537.36"}

@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    # print("body:",body)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'ok'

# 處理 title 文字
def del_re(string):
    import re
    if re.search(r'^Re.\s*',string) != None:
        count = re.search(r'^Re.\s*',string).span()[1]
        return string[count:]
    else:
        return string

# 今日時間
def today_date():
    today = datetime.date.today()
    today_format = today.strftime(("%m/%d"))[1:]
    return today_format

# 昨日時間
def yesterday_date():
    yesterday = datetime.date.today() + datetime.timedelta(-1)
    yesterday_format = yesterday.strftime("%m/%d")[1:]
    return yesterday_format

# 抓取上一頁的 url
def upper_url(url,times=3):
    url_list = [url]
    for i in range(times):
        res = requests.get(url)
        soup = BeautifulSoup(res.text,"html.parser")
        up_page_href = soup.select('div.btn-group a')[3]['href']
        up_page_url = 'https://www.ptt.cc' + up_page_href
        url_list.append(up_page_url)
        url = up_page_url
    return url_list


# ptt_nba版 文章
# ================================================
def ptt_nba():
    articles = []
    curr_url = 'https://www.ptt.cc/bbs/NBA/index.html'
    url_list = upper_url(curr_url)
    for url in url_list:
        rs = requests.sessions.Session()
        res = rs.get(url,headers=headers)
        soup = BeautifulSoup(res.text,'html.parser')
        for r_ent in soup.select('div.r-ent'):
            try:
                href_ = r_ent.select_one('a')
                if href_ != None:
                    link = 'https://www.ptt.cc' + href_['href']    # 每篇文章的連結
                    title = href_.text.strip()                     # 每篇文章的標題
                    rate = r_ent.select_one('div.nrec').text       # 每篇文章的留言數
                    date = r_ent.select_one('.date').text.strip()  # 每篇文章的日期
                    if rate != None:
                        if rate.isnumeric() and int(rate) >= 50:
                            rate = '推{}'.format(rate)
                            articles.append({'date':date ,'rate':rate,'title':del_re(title) ,'link':link})
                        else:
                            if rate.startswith('X'):
                                rate = '噓🤫'
                                articles.append({'date':date ,'rate':rate ,'title':del_re(title) ,'link':link})
                            if rate == '爆':
                                rate = '爆🔥'
                                articles.append({'date':date ,'rate':rate ,'title':del_re(title) ,'link':link})
            except Exception as e:
                print('文章已被刪除', e)

    random.shuffle(articles)
    content = '<籃球版 0{}>\n{}\n\n'.format(today_date(),'='*13)
    for index ,article in enumerate(articles,1):
        if index == 6 :
            return content
        data = '<{}>{}\n{}\n\n'.format(article.get('rate'),article.get('title'), article.get('link'))
        content += data

    return content


# C_Chat 討論版 文章
# ================================================
def ptt_C_Chat():
    articles = []
    curr_url = 'https://www.ptt.cc/bbs/C_Chat/index.html'
    url_list = upper_url(curr_url,5)
    for url in url_list:
        rs = requests.sessions.Session()
        res = rs.get(url,headers=headers)
        soup = BeautifulSoup(res.text,'html.parser')
        for r_ent in soup.select('div.r-ent'):
            try:
                href_ = r_ent.select_one('a')
                if href_ != None:
                    link = 'https://www.ptt.cc' + href_['href']    # 每篇文章的連結
                    title = href_.text.strip()                     # 每篇文章的標題
                    rate = r_ent.select_one('div.nrec').text       # 每篇文章的留言數
                    date = r_ent.select_one('.date').text.strip()  # 每篇文章的日期
                    if rate != None:
                        if rate.isnumeric() and int(rate) >= 15:
                            rate = '推{}'.format(rate)
                            articles.append({'date':date ,'rate':rate,'title':del_re(title) ,'link':link})
                        else:
                            if rate.startswith('X'):
                                rate = '噓🤫'
                                articles.append({'date':date ,'rate':rate ,'title':del_re(title) ,'link':link})
                            if rate == '爆':
                                rate = '爆🔥'
                                articles.append({'date':date ,'rate':rate ,'title':del_re(title) ,'link':link})
            except Exception as e:
                print('文章已被刪除', e)

    random.shuffle(articles)
    content = '閒談版 <0{}>\n{}\n\n'.format(today_date(),'='*13)
    for index ,article in enumerate(articles,1):
        if article.get('date') == today_date():
            if index == 6:
                return content
            data = '<{}>{}\n{}\n\n'.format(article.get('rate'),article.get('title'), article.get('link'))
            content += data

    return content

# HatePolitics 黑特政治版 文章
# ================================================
def ptt_HatePolitics():
    articles = []
    curr_url = 'https://www.ptt.cc/bbs/HatePolitics/index.html'
    url_list = upper_url(curr_url,5)
    for url in url_list:
        rs = requests.sessions.Session()
        res = rs.get(url, headers=headers)
        soup = BeautifulSoup(res.text, 'html.parser')
        for r_ent in soup.select('div.r-ent'):
            try:
                href_ = r_ent.select_one('a')
                if href_ != None:
                    link = 'https://www.ptt.cc' + href_['href']  # 每篇文章的連結
                    title = href_.text.strip()  # 每篇文章的標題
                    rate = r_ent.select_one('div.nrec').text  # 每篇文章的留言數
                    date = r_ent.select_one('.date').text.strip()  # 每篇文章的日期
                    if rate != None:
                        if rate.isnumeric() and int(rate) >= 15:
                            rate = '推{}'.format(rate)
                            articles.append({'date': date, 'rate': rate, 'title': del_re(title), 'link': link})
                        else:
                            if rate.startswith('X'):
                                rate = '噓🤫'
                                articles.append({'date': date, 'rate': rate, 'title': del_re(title), 'link': link})
                            if rate == '爆':
                                rate = '爆🔥'
                                articles.append({'date': date, 'rate': rate, 'title': del_re(title), 'link': link})
            except Exception as e:
                print('文章已被刪除', e)

    content = '黑政版 <0{}>\n{}\n\n'.format(today_date(), '=' * 13)
    for index, article in enumerate(articles, 1):
        if article.get('date') == today_date():
            if index == 10:
                return content
            data = '<{}>{}\n{}\n\n'.format(article.get('rate'), article.get('title'), article.get('link'))
            content += data

    return content


# Sex 西斯版 文章
# ================================================
def ptt_sex():
    urllib3.disable_warnings()
    rs = requests.sessions.Session()
    # 需跳轉 18 禁登入頁面
    load = {
        'from': '/bbs/sex/index.html',
        'yes': 'yes'
    }
    res = rs.post('https://www.ptt.cc/ask/over18', verify=False, data=load)
    soup = BeautifulSoup(res.text,'html.parser')
    article_dict = []
    for r_ent in soup.select('div.r-ent'):
        try:
            href_ = r_ent.select_one('a')
            if href_ != None:
                title = href_.text.strip()
                rate = r_ent.select_one('div.nrec').text
                url = 'https://www.ptt.cc' + href_['href']
                if rate != None:
                    if rate.isnumeric():
                        rate = '推{}'.format(rate)
                    elif rate.startswith('X'):
                        rate = '噓🤫'
                    else:
                        rate = '🈲'+rate
                    article_dict.append({'title':title,'url':url,'rate':rate})
        except Exception as e:
            print('本文已被刪除', e)

    random.shuffle(article_dict)
    content = '西斯版 <0{}>\n{}\n\n'.format(today_date(), '=' * 13)
    for index, article in enumerate(article_dict, 0):
        if index == 10:
            return content
        data = '<{}>{}\n{}\n\n'.format(article.get('rate'),article.get('title'), article.get('url'))
        content += data

    return content


##*新聞News
# 狂新聞
# ================================================
def news_crazy_new():
    urllib3.disable_warnings()
    target_url = 'https://ck101.com/'
    rs = requests.session()
    res = rs.get(target_url, headers=headers, verify=False)
    soup = BeautifulSoup(res.text, 'html.parser')
    articles = []
    upper = soup.select('div.newPosts__upper h4 a')
    for unews in upper:
        title = unews.text.strip()
        link = unews.get('href')
        articles.append({'title': title, 'link': link})
    time.sleep(1)
    bottom = soup.select('div.newPosts__bottom h4 a')
    for bnews in bottom:
        title = bnews.text.strip()
        link = bnews.get('href')
        articles.append({'title': title, 'link': link})

    random.shuffle(articles)
    content = '<卡提諾狂新聞>\n{}\n'.format('========')
    for index, article in enumerate(articles, 1):
        if index == 6:
            return content
        content += '[狂] {}\n{}\n\n'.format(article.get('title'), article.get('link'))

    return content

# 最新狂影片
def news_crazy_video():
    urllib3.disable_warnings()
    target_url = "https://ck101.com/forum.php?mod=forumdisplay&fid=3731"
    rs = requests.session()
    res = rs.get(target_url ,headers=headers ,verify=False)
    soup = BeautifulSoup(res.text, 'html.parser')

    time.sleep(1)
    articles = []
    for video in soup.select('h3 a'):
        string = video.get('onclick')
        if string != None:
            title = video.get('title').strip()
            link = re.findall(r'http://ck101.com/.*.html',string).pop()
            articles.append({'title':title,'link':link})

    content = '<卡提諾狂影集>\n{}\n'.format('========')
    for index ,article in enumerate(articles,1):
        if index == 5:
            return content
        content += '[狂] {}\n{}\n\n'.format(article.get('title'), article.get('link'))

    return content

# 狂惡搞 kuso
def news_crazy_kuso():
    urllib3.disable_warnings()
    target_url = 'https://ck101.com/forum.php?mod=forumdisplay&fid=3607&page=1'
    rs = requests.session()
    res = rs.get(target_url, headers=headers, verify=False)
    soup = BeautifulSoup(res.text, 'html.parser')

    time.sleep(1)
    articles = []
    for kuso in soup.select('div.blockTitle a'):
        string = kuso.get('onclick')
        if string != None:
            title = kuso.get('title').strip()
            link = re.findall(r'http://ck101.com/.*.html', string).pop()
            articles.append({'title': title, 'link': link})

    # 第一則為版規
    articles = articles[1:]
    random.shuffle(articles)
    content = '<卡提諾狂Kuso>\n{}\n'.format('========')
    for index, article in enumerate(articles, 1):
        if index == 8:
            return content
        content += '[狂] {}\n{}\n\n'.format(article.get('title'), article.get('link'))

    return content

# ETtoday新聞 熱門
# ================================================
def news_ETtoday():
    target_url = 'https://www.ettoday.net/news/hot-news.htm'
    rs = requests.session()
    res = rs.get(target_url ,headers=headers ,verify=False)
    soup = BeautifulSoup(res.text, 'html.parser')

    time.sleep(1)
    articles = []
    for news in soup.select('div.part_pictxt_3 h3'):
        title = news.text.strip()
        link = 'https://www.ettoday.net/' + news.select_one('a')['href']
        articles.append({'title':title,'link':link})

    random.shuffle(articles)
    content = 'ETtoday <0{}>\n{}\n\n'.format(today_date(), '=' * 13)
    for index ,article in enumerate(articles,1):
        if index == 6:
            return content
        content += '[ET] {}\n{}\n\n'.format(article.get('title'), article.get('link'))

    return content

# 蘋果即時新聞
# ================================================
def news_Apple():
    target_url = 'https://tw.appledaily.com/new/realtime'
    rs = requests.session()
    res = rs.get(target_url, headers=headers, verify=False)
    soup = BeautifulSoup(res.text, 'html.parser')

    time.sleep(1)
    articles = []
    for news in soup.select('li a')[3:-6]:
        title = news.select_one('h1').text.strip()
        link = news.get('href')
        articles.append({'title': title, 'link': link})

    random.shuffle(articles)
    content = 'AppleNews <0{}>\n{}\n\n'.format(today_date(), '=' * 13)
    for index, article in enumerate(articles, 1):
        if index == 6:
            return content
        content += '[Apple] {}\n{}\n\n'.format(article.get('title'), article.get('link'))

    return content

# 科技新聞 tech
# ================================================
def technews():
    target_url = 'https://technews.tw/'
    print('Start parsing movie ...')
    rs = requests.session()
    res = rs.get(target_url, verify=False)
    res.encoding = 'utf-8'
    soup = BeautifulSoup(res.text, 'html.parser')

    content = 'technews <0{}>\n{}\n\n'.format(today_date(), '=' * 13)
    for index, data in enumerate(soup.select('article div h1.entry-title a')):
        if index == 6:
            return content
        title = data.text
        link = data['href']
        content += '[tech]{}\n{}\n\n'.format(title, link)

    return content

def panx():
    target_url = "https://panx.asia/"
    print('Start parsing ptt hot....')
    rs = requests.session()
    res = rs.get(target_url, verify=False)
    soup = BeautifulSoup(res.text, 'html.parser')

    content = 'PanX泛科技 <0{}>\n{}\n\n'.format(today_date(), '=' * 13)
    for data in soup.select('div.container div.row div.desc_wrap h2 a'):
        title = data.text
        link = data['href']
        content += '[泛]{}\n{}\n\n'.format(title, link)

    return content




# 如果 user 傳什麼{＿＿}，回傳到 MessageEvent
# ================================================
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    print("event.reply_token:", event.reply_token)
    print("event.message.text:", event.message.text)

    # NBA文章
    # ============================================
    if event.message.text in ['Nba','nba','NBA','籃球']:
        content = ptt_nba()
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=content))
        return 0

    # Chat 文章
    # ============================================
    if event.message.text in ['chat','Chat','C_Chat']:
        content = ptt_C_Chat()
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=content))
        return 0

    # Haters 文章
    # ============================================
    if event.message.text in ['hater', 'haters', 'Haters', '黑特政客']:
        content = ptt_HatePolitics()
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=content))
        return 0

    # Sex 文章
    # ============================================
    if event.message.text in ['sex','Sex','SEX','西斯']:
        content = ptt_sex()
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=content))
        return 0


    # 新聞News
    # ============================================
    if event.message.text == "狂新聞":
        content = news_crazy_new()
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=content))
        return 0

    if event.message.text == "狂影片":
        content = news_crazy_video()
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=content))
        return 0

    if event.message.text == "狂kuso":
        content = news_crazy_kuso()
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=content))
        return 0

    if event.message.text == "ETtoday":
        content = news_ETtoday()
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=content))
        return 0

    if event.message.text == "蘋果新聞":
        content = news_Apple()
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=content))
        return 0

    if event.message.text == "PanX泛科技":
        content = panx()
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=content))
        return 0

    if event.message.text == "科技新報":
        content = technews()
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=content))
        return 0

    # 圖片訊息處理
    # ============================================
    if event.message.text == "正妹圖":
        client = ImgurClient(client_id, client_secret, access_token, refresh_token)
        images = client.get_album_images(album_id)
        index = random.randint(0, len(images) - 1)
        url = images[index].link
        image_message = ImageSendMessage(
            original_content_url=url,
            preview_image_url=url
        )
        line_bot_api.reply_message(
            event.reply_token, image_message)
        return 0


    # 圖文訊息
    # ============================================
    if event.message.text == '開始':
        buttons_template = TemplateSendMessage(
            alt_text='Buttons template',
            template=ButtonsTemplate(
                thumbnail_image_url='https://i.imgur.com/1imVDpJ.png',
                title='我是鄉民30CM',
                text='請選擇內容',
                actions=[
                    MessageTemplateAction(
                        label='來當個鄉民',
                        text='ptt'
                    ),
                    MessageTemplateAction(
                        label='來看個新聞',
                        text='新聞'
                    ),
                    MessageTemplateAction(
                        label='來點正妹圖',
                        text='正妹圖'
                    )
                ]
            )
        )
        line_bot_api.reply_message(event.reply_token, buttons_template)
        return 0

    if event.message.text == '新聞':
        buttons_template = TemplateSendMessage(
            alt_text='Buttons template',
            template=ButtonsTemplate(
                thumbnail_image_url='https://365psd.com/images/previews/1d0/psd-news-icon-53281.jpg',
                title='新聞進行式',
                text='請選擇內容',
                actions=[
                    MessageTemplateAction(
                        label='卡提諾狂新聞',
                        text='卡提諾'
                    ),
                    MessageTemplateAction(
                        label='ETtoday新聞',
                        text='ETtoday'
                    ),
                    MessageTemplateAction(
                        label='蘋果動新聞',
                        text='蘋果新聞'
                    ),
                    MessageTemplateAction(
                        '科技新聞',
                        text='科技新聞'
                    )
                ]
            )
        )
        line_bot_api.reply_message(event.reply_token, buttons_template)
        return 0

    if event.message.text == '卡提諾':
        buttons_template = TemplateSendMessage(
            alt_text='Buttons template',
            template=ButtonsTemplate(
                thumbnail_image_url='https://img.ltn.com.tw/Upload/liveNews/BigPic/600_phpg6IvSl.jpg',
                title='卡提諾狂新聞',
                text='請選擇內容',
                actions=[
                    MessageTemplateAction(
                        label='熱門狂新聞',
                        text='狂新聞'
                    ),
                    MessageTemplateAction(
                        label='卡提諾狂影集',
                        text='狂影片'
                    ),
                    MessageTemplateAction(
                        label='卡提諾KUSO',
                        text='狂kuso'
                    )
                ]
            )
        )
        line_bot_api.reply_message(event.reply_token, buttons_template)
        return 0

    if event.message.text == '科技新聞':
        buttons_template = TemplateSendMessage(
            alt_text='Buttons template',
            template=ButtonsTemplate(
                thumbnail_image_url='https://geospatialmedia.s3.amazonaws.com/wp-content/uploads/2019/02/Techcircle.jpg',
                title='Technology News',
                text='請選擇內容',
                actions=[
                    MessageTemplateAction(
                        label='PanX 泛科技',
                        text='PanX泛科技'
                    ),
                    MessageTemplateAction(
                        label='TechNews',
                        text='科技新報'
                    )
                ]
            )
        )
        line_bot_api.reply_message(event.reply_token, buttons_template)
        return 0

    if event.message.text == 'ptt':
        buttons_template = TemplateSendMessage(
            alt_text='Buttons template',
            template=ButtonsTemplate(
                thumbnail_image_url='https://photo.sofun.tw/2015/06/Aotter-PTT-Logo.png',
                title='Menu',
                text='請選擇任一版',
                actions=[
                    MessageTemplateAction(
                        label='NBA(籃球版)',
                        text='nba'
                    ),
                    MessageTemplateAction(
                        label='Sex(西斯版)',
                        text='sex'
                    ),
                    MessageTemplateAction(
                        label='C_Chat(閒談版)',
                        text='chat'
                    ),
                    MessageTemplateAction(
                        label='HatesPoli(政黑版)',
                        text='hater'
                    )
                ]
            )
        )
        line_bot_api.reply_message(event.reply_token, buttons_template)
        return 0

# 最後上傳 Heroku
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
