from flask import Response
from multiprocessing import Process, Queue
import uuid
import scrapy
from scrapy.crawler import CrawlerProcess
from pathlib import Path
import datetime
from google.cloud import storage


class Spider(scrapy.Spider):
    name = ""
    
    def start_requests(self):
        allowed_domains = ["www.yourwebsite.com"]
        urls = ["https://www.yourwebsite.com/some-subpage.html"]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)
    
    def parse(self, response):
        now = datetime.datetime.now()
        date_time = now.strftime("%m%d%YT%H%M")
        page = response.url.replace('/','-')


        ## Prepare blob for upload
        filename = f'{date_time}/{page}.html'
        blob = self.bucket.blob(filename)
        blob.upload_from_string(response.body)

        #Path(filename).write_bytes(response.body)
        self.log(f'Saved file {filename}')
  
        #follow pagination links
        yield from response.follow_all(css='li.pagination-item a',
                                       callback=self.parse)
#
def set_up_bucket():
    client = storage.Client('project-name')
    bucket = client.get_bucket('bucket-name')
    return bucket

def main(data, context):#Entry point for Cloud Function
    def script(queue):
        try:
            bucket = set_up_bucket()
            process = CrawlerProcess(settings={
                #"FEEDS": {

                }
                    )
            process.crawl(Spider,
                          bucket=bucket)
            process.start()
            queue.put(None)
        except Exception as e:
            queue.put(e) #Exception object add to queue


    queue = Queue()
    #define main process that runs script and stores Exceptions in Queue
    main_process = Process(target=script, args=(queue,))
    main_process.start()
    main_process.join() #wait for Spider to complete

    result = queue.get()
    if result is not None:
        raise result

    return Response(response = 'ok', status = 200)
            


