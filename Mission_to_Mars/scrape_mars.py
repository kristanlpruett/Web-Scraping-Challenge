from splinter import Browser
from bs4 import BeautifulSoup
import numpy as np
from flask import Flask, render_template, redirect
from flask_pymongo import PyMongo
import time
import pandas as pd

app = Flask(__name__)

app.config["MONGO_URI"] = "mongodb://localhost:27017/articles"
mongo = PyMongo(app)


def init_browser():
    executable_path = {"executable_path": "C:/chromedriver/chromedriver.exe"}
    return Browser("chrome", **executable_path, headless=False)

site_data = {}

def scrape():
    #Scrape articles & paragraph
    browser = init_browser()
    url = "https://mars.nasa.gov/news/?page=0&per_page=40&order=publish_date+desc%2Ccreated_at+desc&search=&category=19%2C165%2C184%2C204&blank_scope=Latest"
    browser.visit(url)
    html = browser.html
    soup = BeautifulSoup(html, "html.parser")
    articles_data = soup.find_all(class_='list_text')

    for ea in range(0,1):
        site_data['news'] = {'news_title': articles_data[ea].find(class_='content_title').text, 'news_p': articles_data[ea].find(class_='article_teaser_body').text} 
    browser.quit()

    #Get featured image url
    browser = init_browser()
    url = "https://www.jpl.nasa.gov/spaceimages/?search=&category=Mars"
    browser.visit(url)
    html = browser.html
    soup = BeautifulSoup(html, "html.parser")
    featured_image = soup.find('a',class_="button fancybox")
    browser.links.find_by_partial_text('FULL IMAGE').click()
    time.sleep(1)
    html = browser.html
    soup = BeautifulSoup(html, "html.parser")
    img = soup.find(class_='fancybox-inner').img
    img = str(img['src'])
    featured_image_url = "https://www.jpl.nasa.gov"+img
    site_data['featured_image'] = featured_image_url
    browser.quit()

    #Scrape mars facts
    browser = init_browser()
    url = "https://space-facts.com/mars/"
    browser.visit(url)
    html = browser.html
    soup = BeautifulSoup(html, "html.parser")
    facts_table = pd.read_html('https://space-facts.com/mars/')
    facts_table = facts_table[0]

    site_data['facts'] = {}

    for key in facts_table:
        values = []
        for value in facts_table[key]:
            values.append(value)
        site_data['facts'][str(key)] = {'values':values}

    browser.quit()

    #Scrape hemosphere images
    browser = init_browser()

    url = "https://astrogeology.usgs.gov/search/results?q=hemisphere+enhanced&k1=target&v1=Mars"
    browser.visit(url)

    html = browser.html
    soup = BeautifulSoup(html, "html.parser")
    descs = soup.find_all(class_="description")
    links = []
    for ea in descs:
        links.append(f"https://astrogeology.usgs.gov{ea.find('a')['href']}")

    hemosphere_images = []

    for ea in links:
        hemosphere_image = {}
        browser = init_browser()
        url = ea
        browser.visit(url)
        html = browser.html
        soup = BeautifulSoup(html, "html.parser")
        hemosphere_image['title'] = soup.find('title').text.split(' Enhanced')[0]
        hemosphere_image['url'] = soup.find('li').find('a')['href']
        hemosphere_images.append(hemosphere_image)
        browser.quit()

    browser.quit()

    site_data['hemosphere_images'] = hemosphere_images


    #Send to Mongo
    articles_db = mongo.db.articles
    articles_db.update(site_data, site_data, upsert=True)

    # return site_data