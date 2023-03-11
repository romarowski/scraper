from flask import Response
from multiprocessing import Process, Queue
import uuid
import scrapy
from scrapy.crawler import CrawlerProcess
from pathlib import Path
import datetime
from google.cloud import storage


class SparefootSpider(scrapy.Spider):
    name = "sparefoot"

    

    
    def start_requests(self):
        allowed_domains = ["www.sparefoot.com"]
        urls = ["https://www.sparefoot.com/Brooklyn-NY-self-storage.html"]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)
    
    def parse(self, response):
        now = datetime.datetime.now()
        date_time = now.strftime("%m%d%YT%H%M")
        page = response.url.replace('/','-')

        #client = storage.Client('scraper-29')
        #bucket = client.get_bucket('scraper23')

        filename = f'{date_time}/{page}.html'
        blob = self.bucket.blob(filename)
        blob.upload_from_string(response.body)
        #Path(filename).write_bytes(response.body)
        self.log(f'Saved file {filename}')
  
        yield from response.follow_all(css='li.pagination-item a',
                                       callback=self.parse)
#
def set_up_bucket():
    client = storage.Client('scraper-29')
    bucket = client.get_bucket('scraper23')
    return bucket

def main(data,contest):
    def script(queue):
        try:
            bucket = set_up_bucket()
            process = CrawlerProcess(settings={
                #"FEEDS": {

                }
                    )
            process.crawl(SparefootSpider,
                          bucket=bucket)
            process.start()
            queue.put(None)
        except Exception as e:
            queue.put(e)

    try:

        print("I was called !", uuid.uuid4())
        #bucket = set_up_bucket()

        queue = Queue()
        main_process = Process(target=script, args=(queue,))
        main_process.start()
        main_process.join()

        result = queue.get()
        if result is not None:
            raise result

        return Response(response = 'ok', status = 200)
                
    except Exception as e:
        print("ERROR ", e)
        return Response(response = 'AN ERROR OCCURED', status = 400)


