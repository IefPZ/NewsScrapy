# -*- coding:utf-8 -*-
"""
@author: zhang.pengfei5
@contact: zhang.pengfei5@iwhalecloud.com
@time: 2019/8/4 22:28
@description:
    澎湃网站文章爬取
"""
import re
import redis
import datetime
import scrapy
from scrapy.http import Request
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor

from myScrapy.items import SiteUser, Article, Comment


class ThePaperSpider(CrawlSpider):
    name = 'thepaper'
    allowed_domains = []
    start_urls = ['https://www.thepaper.cn/']

    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate, sdch',
        'Accept-Language': 'zh-CN,zh;q=0.8',
        'Cache-Control': 'max-age=0',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36',
        'Cookie': ''
    }

    rules = (
        Rule(LinkExtractor(allow=(r'https://www.thepaper.cn/newsDetail_forward_\d+',)), callback='parse_article', follow=True),
    )

    r = redis.Redis(host='10.45.10.201', port=6379)

    def _build_request(self, rule, link):
        """
        继承自 CrawlSpider，排除已抓取的url
        :param rule:
        :param link:
        :return:
        """
        if not self.r.sismember('urls', link.url):
            r = Request(url=link.url, callback=self._response_downloaded)
            r.meta.update(rule=rule, link_text=link.text)
            return r

    def _article_title(self, response, item):
        """
        解析文章标题
        :param response:
        :param item:
        :return:
        """
        title_pattern = [
            'h1',
            'h2',
        ]
        for pattern in title_pattern:
            title = response.xpath(f'//{pattern}/text()').extract_first()
            if title:
                title = title.strip()
                item['title'] = title
                break

    def _article_author(self, response, item):
        """
        解析文章作者
        :param response:
        :param item:
        :return:
        """
        author_pattern = [
            '//div[@class="news_about"]/p/text()',
        ]
        for pattern in author_pattern:
            author_name = response.xpath(f'{pattern}').extract_first()
            if author_name:
                item['author'] = author_name.strip()
                break

    def _article_keyword(self, response, item):
        """
        解析文章关键词
        :param response:
        :param item:
        :return:
        """
        author_pattern = [
            '//meta[@name="Keywords"]/@content',
        ]
        for pattern in author_pattern:
            xpath = response.xpath(
                f'{pattern}').extract_first()
            if xpath:
                item['keywords'] = xpath
                break

    def _article_timestamp(self, response, item):
        """
        解析文章发布时间
        :param response:
        :param item:
        :return:
        """
        xpath_pattern = [
            '//div[@class="news_about"]/p/text()',
            '//div[@class="video_info_left"]/span/text()',
        ]
        for pattern in xpath_pattern:
            xpath = response.xpath(f'{pattern}').extract()
            if xpath:
                for each in xpath:
                    if re.search(r'\d+[:-]\d+', each):
                        item['timestamp'] = each.strip()
                        break

    def _article_description(self, response, item):
        """
        解析文章描述信息
        :param response:
        :param item:
        :return:
        """
        xpath_pattern = [
            '//meta[@name="Description"]/@content',
        ]
        for pattern in xpath_pattern:
            xpath = response.xpath(f'{pattern}').extract_first()
            if xpath:
                item['description'] = xpath
                break

    def _article_collect(self, response, item):
        """
        解析文章收藏数
        :param response:
        :param item:
        :return:
        """
        xpath_pattern = [
            # '//a[@title="收藏本文"]/span/text()',
        ]
        for pattern in xpath_pattern:
            xpath = response.xpath(f'{pattern}').extract_first()
            if xpath:
                item['collect'] = xpath
                break

    def _article_like(self, response, item):
        """
        解析文章点赞数
        :param response:
        :param item:
        :return:
        """
        xpath_pattern = [
            '//div[@class="news_love"]/div/a/text()',
        ]
        for pattern in xpath_pattern:
            xpath = response.xpath(f'{pattern}').extract_first()
            if xpath:
                item['like'] = xpath.strip()
                break

    def _article_comment(self, response, item):
        """
        解析文章评论数
        :param response:
        :param item:
        :return:
        """
        xpath_pattern = [
            '//h2[@id="comm_span"]/span/text()',
        ]
        for pattern in xpath_pattern:
            xpath = response.xpath(f'{pattern}').extract_first()
            if xpath:
                xpath = xpath.strip().replace('（', '').replace('）', '')
                if 'k' in xpath:
                    xpath = xpath.replace('k', '')
                    xpath = float(xpath) * 1000
                item['comment'] = xpath
                break

    def _article_content(self, response, item):
        """
        解析文章内容
        :param response:
        :param item:
        :return:
        """
        content_pattern = [
            '//div[@class="news_txt"]/text()',
            '//div[@class="video_txt_l"]/p/text()',
        ]

        for pattern in content_pattern:
            xpath = response.xpath(pattern).extract()
            if xpath:
                item['content'] = '\r\n'.join(xpath)
                break

    def parse_article(self, response):
        """
        评论获取 https://www.thepaper.cn/newDetail_commt.jsp?contid=4143977
        :param response:
        :return:
        """
        cont_id = response.url.split('_')[-1]
        yield Request(
            url=f'https://www.thepaper.cn/newDetail_commt.jsp?contid={cont_id}',
            callback=self.parse_comment,
            cb_kwargs={'article_url': response.url})

        item = Article()
        item['url'] = response.url
        item['site'] = self.name

        for func in (
                self._article_title,
                self._article_author,
                self._article_keyword,
                self._article_timestamp,
                self._article_description,
                self._article_collect,
                self._article_like,
                self._article_comment,
                self._article_content,
        ):
            func(response, item)

        yield item

    def parse_comment(self, response, article_url):
        """
        解析评论
        :param response:
        :return:
        """
        comment_que = response.xpath('//div[@class="comment_que"]')
        for xpath in comment_que:
            item = Comment(site=self.name, url=article_url, content_type='Artical')
            username = xpath.xpath('div/div[@class="aqwright"]/h3/a/text()').extract_first()
            if username:
                item['author'] = username
            timestamp = xpath.xpath('div/div[@class="aqwright"]/h3/span/text()').extract_first()
            if timestamp:
                desc = {
                    '分钟前': 1,
                    '小时前': 60,
                    '天前': 60 * 24,
                    '月前': 60 * 24 * 30,
                    '年前': 60 * 24 * 365
                }
                for key, value in desc.items():
                    if key in timestamp:
                        timestamp = timestamp.replace(key, '')
                        if timestamp.isdigit():
                            item['timestamp'] = datetime.datetime.now() - datetime.timedelta(minutes=int(timestamp) * value)
                        else:
                            item['timestamp'] = timestamp
                        break

            content = xpath.xpath('div/div[@class="aqwright"]/div[@class="ansright_cont"]/a/text()').extract_first()
            if content:
                item['content'] = content
            like = xpath.xpath('div/div[@class="aqwright"]/div[@class="ansright_time"]/a/text()').extract_first()
            if like:
                if 'k' in like:
                    like = like.replace('k', '')
                    like = float(like) * 1000
                item['like'] = like

            yield item

    def parse_user(self, response):
        """
        解析用户信息
        :param response:
        :return:
        """
        nickname = response.xpath('//div[@class="user-nick"]/text()').extract_first().strip()
        item = SiteUser(site=self.name, nickname=nickname, url=response.url)

        user_fields = {
            '公司': 'company',
            '邮箱': 'email',
            '微博': 'weibo',
            '微信': 'weichat',
            '真实姓名': 'username',
            '手机': 'telephone',
            '性别': 'gender',
            '所在地址': 'address',
            '所在城市': 'address',
            '注册时间': 'regtime',
            '生日': 'birthday',
            '职业': 'occupation',
            '教育背景': 'edubg',

        }

        match = response.xpath('//ul[@class="main_info"]/li')
        for each in match:
            key = each.xpath('text()').extract_first()
            value = each.xpath('span/text()').extract_first()
            if not key:
                continue
            if '：' in key:
                key = key.replace('：', '')
            key = key.strip()
            if key in user_fields:
                item[user_fields[key]] = value

        yield item
