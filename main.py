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
    
    def parse(self, response, bucket):
        now = datetime.datetime.now()
        date_time = now.strftime("%m%d%YT%H%M%S")
        page = response.url.replace('/','-')


        filename = f'{date_time}/{page}.html'
        blob = bucket.blob(filename)
        blob.upload_from_file(response.body)
        #Path(filename).write_bytes(response.body)
        self.log(f'Saved file {filename}')
  
        yield from response.follow_all(css='li.pagination-item a',
                                       callback=self.parse)

def set_up_bucket():
    client = storage.Client()
    bucket = client.get_bucket('scraper23')
    return bucket

def main(request):
    def script(queue):
        try:
            process = CrawlerProcess(settings={
                #"FEEDS": {

                }
                    )
            process.crawl(SparefootSpider)
            process.start()
            queue.put(None)
        except Exception as e:
            queue.put(e)

    try:

        print("I was called !", uuid.uuid4())
        bucket = set_up_bucket()

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


