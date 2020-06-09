#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# Created Date: Monday, June 8th 2020, 1:32:58 am
# Author: Charlene Leong charleneleong84@gmail.com
# Last Modified: Friday, June 12th 2020, 11:21:20 pm
###

import os
import argparse
import json
import scrapy
from scrapy.crawler import CrawlerProcess
import html2text


class DiscourseForumSpider(scrapy.Spider):
    name = 'discourse_forum_spider'
    def __init__(self, forum_name, base_url, *args, **kwargs):
        super(DiscourseForumSpider, self).__init__(*args, **kwargs)
        self.page_base_url = f"{base_url}/latest.json?no_definitions=true&page=%s" # eg. {base_url}/latest.json?no_definitions=true&page={page_num}
        self.post_url = f"{base_url}/t/%s.json?track_visit=true&forceLoad=true"  # eg. {base_url}/t/{post_id}.json?track_visit=true&forceLoad=true
        # self.post_html_url = f"{base_url}/t/%s/%s"  # eg. https://{base_url}/t/{topic_slug}/{topic_id}

        self.start_page = 0
        self.start_urls = [self.page_base_url % self.start_page]
        self.download_delay = 1.5
        self.forum_name = forum_name


    def parse(self, response):
        data = json.loads(response.body)

        for post_topic in data['topic_list']['topics']:
            yield scrapy.Request(self.post_url % post_topic.get('id'), callback=self.parse_post)    # Requesting post_url with post ID
        # if self.start_page == 2:
        #     return
        if 'more_topics_url' in data['topic_list'].keys():
            self.start_page = self.start_page + 1
            yield scrapy.Request(self.page_base_url % self.start_page, callback=self.parse)


    def parse_post(self, response):
        data = json.loads(response.body)
        for post in data['post_stream']['posts']:
            h = html2text.HTML2Text()
            h.unicode_snob = True
            item = {'post_text': h.handle(post.get('cooked')).replace('\n', ' ').replace('  ', ' '), 
                    'post_id': post.get('id'),
                    'user_id': post.get('user_id'),
                    'username': post.get('username'),
                    'reply_to_post_num': post.get('reply_to_post_number'),
                    'topic_id': post.get('topic_id'),
                    'post_num' : post.get('post_number'),
                    'reply_count' : post.get('reply_count'),
                    'created_at' : post.get('created_at'),
                    'updated_at' : post.get('updated_at'),
                    'num_reads' : post.get('reads'),
                    'topic_slug': post.get('topic_slug'),
                    'forum_name': self.forum_name
            }
            yield item

            # print(type(category))
            # print(item)
            # print(self.post_html_url % (post.get('topic_slug'), post.get('topic_id')))
            # yield scrapy.Request(self.post_html_url % (post.get('topic_slug'), post.get('topic_id')), 
            #                         callback=self.parse_html_post,
            #                         meta={'item': item})
            
    
    # def parse_html_post(self, response):
    #     data = json.loads(response)
    #     h = html2text.HTML2Text()
    #     h.unicode_snob = True
    #     item = response.meta['item']
    #     print(item)
    #     item['category'] = h.handle(response.xpath('//span[@class="category-name').get()).replace('\n', ' ').replace('  ', ' ')
    #     yield item


def main(args):
    forum_name = args.forum_name
    filename = f'{forum_name}_forum_posts'
    base_url = args.base_url
    
    OUTPUT_FOLDER = os.path.join(os.getcwd(), 'output')
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)

    process = CrawlerProcess(settings={
        "FEEDS": {
            os.path.join(OUTPUT_FOLDER, f'{filename}.csv') : {"format": "csv"},
        },
    })

    process.crawl(DiscourseForumSpider, forum_name, base_url)
    process.start()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Scrapes Discourse forum and outputs to file')
    parser.add_argument('-f', '--forum_name', help='Discourse Forum Name') 
    parser.add_argument('-url', '--base_url',  help='Discourse Forum Base URL') 
    args = parser.parse_args()
    main(args)
