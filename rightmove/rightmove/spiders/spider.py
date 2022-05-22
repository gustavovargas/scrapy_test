import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.exceptions import CloseSpider
from rightmove.items import RightItem
from scrapy_playwright.page import PageMethod


def set_pw_next(request, response):
    request.meta["playwright"] = True
    request.meta["playwright_include_page"] = True
    request.meta["playwright_page_methods"] = [
        PageMethod("wait_for_load_state", "domcontentloaded"),
        PageMethod("evaluate", "document.querySelectorAll('.pagination-next')[0].click()"),
    ]
    return request


def set_pw_item(request, response):
    request.meta["playwright"] = True
    request.meta["playwright_include_page"] = True
    request.meta["playwright_page_methods"] = {
        PageMethod("wait_for_load_state", "domcontentloaded")
    }
    return request


class RightMoveSpider(CrawlSpider):
    name = "rightmove"
    item_count = 0
    allowed_domain = ["https://www.rightmove.co.uk/"]

    def start_requests(self):
        yield scrapy.Request(
            url='https://www.rightmove.co.uk/house-prices/manchester.html?propertyType=DETACHED&soldIn=2&page=1',
            meta={"playwright": True,
                  "playwright_include_page": True,
                  "playwright_page_methods": {
                      PageMethod("wait_for_load_state", "domcontentloaded")
                  }
            }
        )
        return super().start_requests()
    # start_urls = ["https://www.rightmove.co.uk/house-prices/manchester.html?propertyType=DETACHED&soldIn=2&page=1"]

    rules = {
        Rule(
            LinkExtractor(
                allow=(),
                restrict_xpaths=("//div[@class='pagination pagination-next ']")
            ),
            process_request=set_pw_next
        ),
        Rule(
            LinkExtractor(
                allow=(),
                restrict_xpaths=("//a[@class='title clickable']")
            ),
            callback="parse_item",
            follow=False,
            process_request=set_pw_item
        ),
    }

    def parse_item(self, response):
        table_response = response.xpath("//table[@id='soldrecord']/tbody//tr")

        url_maps_str = response.xpath("//*[@id='minimapwrapper']/img/@src").extract_first()
        latitude = url_maps_str.split("?center=")[-1].split("&zoom=")[0].split(",")[0]
        print(f"latitude: {latitude}")
        longitude = url_maps_str.split("?center=")[-1].split("&zoom=")[0].split(",")[1]

        line_date_added = response.xpath("//*[@id='propertyDetailsHeader']//text()").extract_first()
        date_added = line_date_added.split("on Rightmove on")[-1]
        print(f"date_added: {date_added}")

        line_imgs = response.xpath("//*[@id='tabs-images']/a//text()").extract_first()
        num_imgs = line_imgs.split("(")[-1].split(")")[0]

        for tr in table_response:
            ml_item = RightItem()
            ml_item['sale_date'] = tr.xpath('td[1]//text()').extract_first()
            print(f"sale_date: {ml_item['sale_date']}")
            ml_item['price_paid'] = tr.xpath('td[3]//text()').extract_first()
            ml_item['property'] = tr.xpath('td[2]//text()').extract_first()
            ml_item['url'] = response.url
            ml_item['source_url'] = response.request.url
            ml_item['number_rooms'] = response.xpath("//h1[@id='propertyDetailsHeader']/following-sibling::h2//text()").extract_first()
            ml_item['id'] = response.url.split("prop=")[-1].split("&")[0]
            ml_item['latitude'] = latitude
            ml_item['longitude'] = longitude
            ml_item['date_added'] = date_added
            # ml_item['area'] = response.xpath('//td[1]').get()
            ml_item['number_imgs'] = num_imgs
            ml_item['name_area'] = response.xpath('//*[@id="propertyAddress"]/h2//text()').extract_first()
            # print(f"ml_item: {ml_item}")
            self.item_count += 1
            print('*' * 10)
            print(self.item_count)
            print('*'*10 + '\n\n\n\n')
            if self.item_count > 40:
                raise CloseSpider('item_exceeded')
            yield ml_item

