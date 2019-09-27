# import need packages
import os
import requests
import configparser
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

# API Config.ini
config = configparser.ConfigParser()
config.read("config.ini")

# Line Messenger API
line_bot_api = LineBotApi(config['line_bot']['Channel_Access_Token'])
handler = WebhookHandler(config['line_bot']['Channel_Secret'])
# Imgur image API
client_id = config['imgur_api']['Client_ID']
client_secret = config['imgur_api']['Client_Secret']
access_token = config['imgur_api']['Access_token']
refresh_token = config['imgur_api']['Refresh_token']
album_id = config['imgur_api']['Album_ID']

# requests.get 偽裝器
headers = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36'}

@app.route("/callback", methods=["POST"])
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
    today_format = today.strftime(("%m/%d"))
    if today_format.startswith("0"):
        return today_format[1:]
    else:
        return today_format

# 昨日時間
def yesterday_date():
    yesterday = datetime.date.today() + datetime.timedelta(-1)
    yesterday_format = yesterday.strftime("%m/%d")
    if yesterday_format.startswith("0"):
        return yesterday_format[1:]
    else:
        return yesterday_format

# 抓取上一頁的 url
def ptt_upper_url(ptt_board_url,pages=5):
    url_list = [ptt_board_url]
    res = requests.get(ptt_board_url)
    soup = BeautifulSoup(res.text,"html.parser")

    pre_href = soup.select('div.btn-group a')[3]['href']
    board = pre_href.split('/')[2]
    pre_index = re.search('\d+',pre_href).group()
    index = int(pre_index)
    domain = 'https://www.ptt.cc/bbs/'
    for page in range(pages-1):
        index_url = domain + board + "/index" + str(index) + ".html"
        index -= 1
        url_list.append(index_url)

    return url_list

# ptt_over_18 href
def ptt_over18_href(href, pages=5):
    href_list = [href]
    urllib3.disable_warnings()
    rs = requests.sessions.Session()
    # 需跳轉 18 禁登入頁面
    payload = {'from': href,'yes': 'yes'}
    res = rs.post('https://www.ptt.cc/ask/over18', verify=False, data=payload)
    soup = BeautifulSoup(res.text, 'html.parser')

    pre_href = soup.select('div.btn-group a')[3]['href']
    board = pre_href.split('/')[2]
    pre_index = re.search('\d+', pre_href).group()
    index = int(pre_index)
    up_href = "/bbs/{}/index".format(board)

    for page in range(pages - 1):
        whole_href = up_href + str(index) + ".html"
        index -= 1
        href_list.append(whole_href)

    return href_list

# ptt articles
def ptt_article(ptt_board_url, over_rate):
    """
    ptt_board_url:str :please input ptt board url
    over_rate:int :please input a number which is rate threshold

    return ptt articles which > rate
    """
    articles = []
    url_list = ptt_upper_url(ptt_board_url, 5)
    for url in url_list:
        rs = requests.sessions.Session()
        res = rs.get(url,headers=headers)
        soup = BeautifulSoup(res.text, 'html.parser')

        for r_ent in soup.select('div.r-ent'):
            try:
                href_ = r_ent.select_one('a')
                if href_ != None:
                    link = 'https://www.ptt.cc' + href_['href']  # 每篇文章的連結
                    title = href_.text.strip()  # 每篇文章的標題
                    title = del_re(title)
                    if len(title)>20:
                        title = title[:20]+"..."
                    else:
                        title=title
                    rate = r_ent.select_one('div.nrec').text  # 每篇文章的留言數
                    date = r_ent.select_one('.date').text.strip()  # 每篇文章的日期
                    if rate != None:
                        if rate.isnumeric() and int(rate) >= over_rate:
                            rate = '推{}'.format(rate)
                            articles.append({'date': date, 'rate': rate, 'title': title, 'link': link})
                        else:
                            if rate.startswith('X'):
                                rate = '噓🖕'
                                articles.append({'date': date, 'rate': rate, 'title': title, 'link': link})
                            if rate == '爆':
                                rate = '爆🔥'
                                articles.append({'date': date, 'rate': rate, 'title': title, 'link': link})
            except Exception as e:
                print('文章已刪除', e)

    return articles

# ptt over18 articles
def ptt_over18_article(href, over_rate):
    """
    href:str :please input href, Ex:"/bbs/sex/index.html", "/bbs/Gossiping/index.html"
    over_rate:int :please input a number which is rate threshold

    return ptt articles which > rate
    """
    articles = []
    href_list = ptt_over18_href(href, 10)
    for _href in href_list:
        urllib3.disable_warnings()
        rs = requests.sessions.Session()
        # 需跳轉 18 禁登入頁面
        payload = {'from': _href, 'yes': 'yes'}
        res = rs.post('https://www.ptt.cc/ask/over18', verify=False, data=payload)
        soup = BeautifulSoup(res.text, 'html.parser')

        for r_ent in soup.select('div.r-ent'):
            try:
                href_ = r_ent.select_one('a')
                if href_ != None:
                    link = 'https://www.ptt.cc' + href_['href']  # 每篇文章的連結
                    title = href_.text.strip()  # 每篇文章的標題
                    title = del_re(title)
                    if len(title)>20:
                        title = title[:20]+"..."
                    else:
                        title=title
                    rate = r_ent.select_one('div.nrec').text  # 每篇文章的留言數
                    date = r_ent.select_one('.date').text.strip()  # 每篇文章的日期
                    if rate != None:
                        if rate.isnumeric() and int(rate) >= over_rate:
                            rate = '推{}'.format(rate)
                            articles.append({'date': date, 'rate': rate, 'title': title, 'link': link})
                        else:
                            if rate.startswith('X'):
                                rate = '噓🖕'
                                articles.append({'date': date, 'rate': rate, 'title': title, 'link': link})
                            if rate == '爆':
                                rate = '爆🔥'
                                articles.append({'date': date, 'rate': rate, 'title': title, 'link': link})
            except Exception as e:
                print('文章已刪除', e)

    return articles



# ptt_nba版 文章
def ptt_nba():
    articles = ptt_article('https://www.ptt.cc/bbs/NBA/index.html',50)
    random.shuffle(articles)

    content = '<籃球版 0{}>\n{}\n\n'.format(today_date(),'='*13)
    for index ,article in enumerate(articles,1):
        if index == 5 :
            return content
        data = '<{}> {}\n{}\n\n'.format(article.get('rate'),article.get('title'), article.get('link'))
        content += data

    return content

# C_Chat 討論版 文章
def ptt_C_Chat():
    articles = ptt_article('https://www.ptt.cc/bbs/C_Chat/index.html', 40)
    random.shuffle(articles)

    content = '閒談版 <0{}>\n{}\n\n'.format(today_date(),'='*13)
    for index ,article in enumerate(articles,1):
        if article.get('date') == today_date():
            if index == 5:
                return content
            data = '<{}> {}\n{}\n\n'.format(article.get('rate'),article.get('title'), article.get('link'))
            content += data

    return content

# Sex 西斯版 文章
def ptt_sex():
    articles = ptt_over18_article('/bbs/sex/index.html', 50)
    random.shuffle(articles)

    content = '西斯版 <0{}>\n{}\n\n'.format(today_date(), '=' * 13)
    for index, article in enumerate(articles, 1):
        if index == 5:
            return content
        data = '<{}> {}\n{}\n\n'.format(article.get('rate'), article.get('title'), article.get('link'))
        content += data

    return content

# HatePolitics 黑特政治版 文章
def ptt_HatePolitics():
    articles = ptt_over18_article('/bbs/HatePolitics/index.html',30)
    random.shuffle(articles)

    content = '黑政版 <0{}>\n{}\n\n'.format(today_date(), '=' * 13)
    for index, article in enumerate(articles, 1):
        if article.get('date') == today_date():
            if index == 5:
                return content
            data = '<{}> {}\n{}\n\n'.format(article.get('rate'), article.get('title'), article.get('link'))
            content += data

    return content

# Stock 股票版 文章
def ptt_stock():
    articles = ptt_article('https://www.ptt.cc/bbs/Stock/index.html',40)
    random.shuffle(articles)

    content = '股票版 <0{}>\n{}\n\n'.format(today_date(), '=' * 13)
    for index, article in enumerate(articles, 1):
        if article.get('date') == today_date():
            if index == 5:
                return content
            data = '<{}> {}\n{}\n\n'.format(article.get('rate'), article.get('title'), article.get('link'))
            content += data

    return content

# Beauty 表特版 文章
def ptt_beauty_crawl(href):
    urllib3.disable_warnings()
    pay_load = {'from': href, 'yes': 'yes'}

    rs = requests.sessions.Session()
    res = rs.post('https://www.ptt.cc/ask/over18', verify=False, data=pay_load)
    soup = BeautifulSoup(res.text, 'html.parser')

    return soup

def ptt_beauty():
    rate_filter = []

    while len(rate_filter) <= 0:
        index = str(random.randint(2000, 3050))

        hot_soup = ptt_beauty_crawl('/bbs/Beauty/index{}.html'.format(index))
        hot = hot_soup.select('div.r-ent')

        for i in hot:
            if i.select_one('span'):
                if i.select_one('span').text.isnumeric():
                    if int(i.select_one('span').text) > 50:
                        rate_filter.append(i.select_one('a').get('href'))

    article = random.choice(rate_filter)
    soup_imgur = ptt_beauty_crawl(article)
    imgur_link = [href['href'] for href in soup_imgur.select('div a') if ".jpg" in href['href']]

    return imgur_link[0]


### 新聞News
# 狂新聞
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
def technews():
    target_url = 'https://technews.tw/'
    print('Start parsing movie ...')
    rs = requests.session()
    res = rs.get(target_url, verify=False)
    res.encoding = 'utf-8'
    soup = BeautifulSoup(res.text, 'html.parser')

    content = 'Technews <0{}>\n{}\n\n'.format(today_date(), '=' * 13)
    for index, data in enumerate(soup.select('article div h1.entry-title a')):
        if index == 6:
            return content
        title = data.text
        link = data['href']
        content += '[Tech] {}\n{}\n\n'.format(title, link)

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
        content += '[泛] {}\n{}\n\n'.format(title, link)

    return content



# 如果 user 傳什麼{＿＿}，回傳到 MessageEvent
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
    if event.message.text in ['chat','Chat','CHAT','C_Chat']:
        content = ptt_C_Chat()
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=content))
        return 0

    # Stock 文章
    # ============================================
    if event.message.text in ['stock', '股票', 'Stock', 'STOCK']:
        content = ptt_stock()
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=content))
        return 0

    # Haters 文章
    # ============================================
    if event.message.text in ['hater','haters','Hater','Haters']:
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

    # Beauty 文章
    # ============================================
    if event.message.text in ["表特正妹","表特","Beauty","beauty"]:
        imgur_url = ptt_beauty()
        image_message = ImageSendMessage(
            original_content_url=imgur_url,
            preview_image_url=imgur_url
        )
        line_bot_api.reply_message(
            event.reply_token, image_message)
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

    # 圖片訊息
    if event.message.text in ["正妹","正妹圖"]:
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
        time.sleep(1)
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
                        label='表特正妹圖',
                        text='Beauty'
                    ),
                    MessageTemplateAction(
                        label='來點正妹圖',
                        text='正妹'
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
                        label='HatePoli(政黑版)',
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
