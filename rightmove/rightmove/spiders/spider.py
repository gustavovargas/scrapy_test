import scrapy
from scrapy.spiders import Spider
from rightmove.items import RightItem
import json


class RightMoveSpider(Spider):
    name = "rightmove"
    item_count = 0
    allowed_domain = ["https://www.rightmove.co.uk/"]
    base_url = 'https://www.rightmove.co.uk/house-prices/manchester.html?propertyType=DETACHED&soldIn=2&page='

    def start_requests(self):
        print("begin start request...")
        yield scrapy.Request(
            url='https://www.rightmove.co.uk/house-prices/manchester.html?propertyType=DETACHED&soldIn=2&page=1'
        )
        return super().start_requests()

    def parse(self, response):
        print("parse foo - starting")
        print(f"parse foo - response.url: {response.url}")

        self.url_page = response.url
        self.name_area = response.xpath("/html/head/title/text()").get().split("Prices in")[-1].strip()

        scripts = response.css('script::text')
        pattern = "__PRELOADED_STATE__ = "
        for script in scripts:
            if pattern in script.extract():
                json_data = script.extract().split(pattern)[-1].strip()
                try:
                    parsed_script = json.loads(json_data)
                except:
                    raise ValueError(f"bad json data identification in {response.url}")
                break
        else:
            raise ValueError(f"No PRELOADED STATE founded at {response.url}")

        pagination = parsed_script.get("pagination")
        current_page = int(pagination.get("current"))
        last_page = int(pagination.get("last"))
        print(f"current page: {current_page}\nlast_page: {last_page}")

        properties = parsed_script.get("results").get("properties")

        for property in properties:
            if property.get("detailUrl"):
                yield scrapy.Request(url=property.get("detailUrl"), callback=self.parse_item)

        if current_page < last_page:
            next_page = current_page + 1
            next_page_url = f"{self.base_url}{next_page}"
            print("going to next page")
            yield scrapy.Request(url=next_page_url, callback=self.parse)

    def parse_item(self, response):
        print("parse item foo - starting")
        print(f"parse item foo - response.url: {response.url}")
        scripts_page = response.css('script::text')
        pattern = "PAGE_MODEL = "

        for script in scripts_page:
            if pattern in script.extract():
                json_data = script.extract().split(pattern)[-1].strip()
                try:
                    parsed_script = json.loads(json_data).get("soldPropertyData")
                except:
                    raise ValueError(f"bad json data identification in {response.url}")
                break
        else:
            raise ValueError(f"No PAGE MODEL founded at {response.url}")

        transactions = parsed_script.get("transactions")

        for transaction in transactions:
            ml_item = RightItem()
            ml_item['sale_date'] = transaction.get("deedDate")
            ml_item['price_paid'] = transaction.get("price")
            ml_item['property'] = f'{parsed_script.get("propertyType")}, {transaction.get("tenure")}'
            ml_item['url'] = response.url
            ml_item['source_url'] = self.url_page
            ml_item['number_rooms'] = parsed_script.get("property").get("bedrooms")
            ml_item['id'] = transaction.get("id")
            ml_item['latitude'] = parsed_script.get("property").get("location").get("latitude")
            ml_item['longitude'] = parsed_script.get("property").get("location").get("longitude")
            ml_item['date_added'] = parsed_script.get("lastListed")
            ml_item['number_imgs'] = len(parsed_script.get("property").get("images"))
            ml_item['name_area'] = self.name_area

            # self.item_count += 1
            # print('\n\n\n' + '*' * 10)
            # print(self.item_count)
            # print('*' * 10 + '\n')
            # if self.item_count > 40:
            #     raise CloseSpider('item_exceeded')
            yield ml_item
