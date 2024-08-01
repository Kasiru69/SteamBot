import requests
import flask
import http
import time
from bs4 import BeautifulSoup
from pymongo import MongoClient
from datetime import date
import google.generativeai as genai

API_KEY='AIzaSyB6cFuBa9ETtO-VGQFO7DvJsv6KCu9o42s'
app=flask.Flask(__name__)
url = 'https://store.steampowered.com/search/?filter=topsellers'
connectionString="mongodb+srv://saptaswadas:Sha_dow%401_23@cluster0.ffdduia.mongodb.net/"
client=MongoClient(connectionString)
db=client['steam']
post=db.posts
def Date():
    DATE=date.today()
    d,m,y=DATE.day,DATE.month,DATE.year
    prevDate=post.find_one({'_id':'Date'})
    pd,pm,py=prevDate['day'],prevDate['month'],prevDate['year']
    print(pd,pm,py,sep=' ')
    print(d, m, y, sep=' ')
    flag=False
    if(py<y):
        flag=True
    if(pm<m):
        flag=True
    if(pd<d):
        flag=True
    if(flag):
        print('hello')
        post.update_one({'_id':'Date'},{'$set':{
            'day':d,
            'month':m,
            'year':y
                                                }})
    return flag
    #x=post.find_one('DATE')
    #print(type(x['day']))
    #post.update_one({'_id':'DATE'},{'$set':{'day':x['day']+1}})

def Scrap():
    proxies={
        'http':'130.61.120.213',
        'https':'130.61.120.213'
    }
    response = requests.get(url)
    #print(response.json())
    page_content = response.text
    page_content
    doc = BeautifulSoup(page_content, 'html.parser')
    games = doc.find_all('div', {'class': 'responsive_search_name_combined'})
    links = doc.find_all('a', {'class': "search_result_row ds_collapse_flag"})
    images = doc.find_all('div', {'class': "col search_capsule"})
    length = len(games)
    arr = []
    for _ in range(length):
        game = games[_]
        link = links[_]
        name = game.find('span', {'class': 'title'}).text
        published_date = game.find('div', {'class': 'col search_released responsive_secondrow'}).text.strip()
        original_price_elem = game.find('div', {'class': 'discount_original_price'})
        original_price = original_price_elem.text.strip() if original_price_elem else 'FREE'
        arr.append({
            'image': str(images[_].find('img').get('src')),
            'name': name,
            'published_date': published_date,
            'price': original_price,
            'link': link.get('href')
        })
    Post=post
    for _ in range(length):
        flag=False
        it=Post.find_one({'name':arr[_]['name']})
        #print(arr[_])
        if(it is not None):
            prevprice=it['price']
            currprice=arr[_]['price']
            if(prevprice=='FREE'):
                prevprice=0
            if (currprice == 'FREE'):
                currprice = 0
            if(prevprice!=0):
                prevprice=convert_string_tointeger(prevprice)
            if (currprice != 0):
                currprice = convert_string_tointeger(currprice)
            if(prevprice>currprice):
                flag=True
        post.update_one({'_id':_},
                        {"$set":{
                            'image': arr[_]['image'],
                            'name': arr[_]['name'],
                            'published_date': arr[_]['published_date'],
                            'price': arr[_]['price'],
                            'link': arr[_]['link'],
                            'discount':flag
                        }}
                        )
    return arr
def convert_string_tointeger(price):
    price = price.replace('₹', '').replace(',', '')
    price = price.split('.')[0]
    price_int = int(price)
    return price_int
#@app.route('/')
def get():
    lis=[]
    if(Date()==True):
        #print("Hello")
        lis=Scrap()
        #print(lis)
    else:
        arr = post.find()
        c = 0
        for _ in arr:
            if (c == 0):
                c += 1
                continue
            lis.append(_)
            c += 1
    #print(lis)
    return lis
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')
chat = model.start_chat(history=[])
def getAnswer(string):
    response = chat.send_message(string)
    return response.text
@app.route('/Chatbot=<arr>')
def ChatBot(arr):
    s = ""
    c = 0
    list=get()
    for _ in post.find():
        if c == 0:
            c += 1
            continue
        s = (s + "This is game " + str(c) + " and this are the details : " + "name: " + _['name'] +
             " price: " + _['price'] + " publisheddate: " + _['published_date'] + " link: " +
             _['link'] + " discount: " + str(_['discount']) + '\n')
        c += 1
    response = chat.send_message(s)
    #string = input("Enter ur question\n")
    string=getAnswer(arr+"place slash n instead of going to next line")
    print(string.split('\n'))
    return string.split('\n')
if __name__ == '__main__':
    app.run(debug=True)