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
                url = property.get("detailUrl")
                if "Matching" in url:
                    yield scrapy.Request(url=url, callback=self.parse_item_matching)
                else:
                    yield scrapy.Request(url=url, callback=self.parse_item)
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
            ml_item['sale_date'] = transaction.get("displayDeedDate")
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

    def parse_item_matching(self, response):
        print("parse item matching foo - starting")
        print(f"parse item foo - response.url: {response.url}")
        table_response = response.xpath("//table[@id='soldrecord']/tbody//tr")

        url_maps_str = response.xpath("//*[@id='minimapwrapper']/img/@src").extract_first()
        latitude = url_maps_str.split("?center=")[-1].split("&zoom=")[0].split(",")[0]
        latitude = float(latitude)
        longitude = url_maps_str.split("?center=")[-1].split("&zoom=")[0].split(",")[1]
        longitude = float(longitude)

        line_date_added = response.xpath("//*[@id='propertyDetailsHeader']//text()").extract_first()
        date_added = line_date_added.split("on Rightmove on")[-1].strip()

        line_imgs = response.xpath("//*[@id='tabs-images']/a//text()").extract_first()
        num_imgs = line_imgs.split("(")[-1].split(")")[0]
        num_imgs = int(num_imgs)

        num_bedrooms = response.xpath("//h1[@id='propertyDetailsHeader']/following-sibling::h2//text()").extract_first()
        if "bedroom" in num_bedrooms:
            num_bedrooms = num_bedrooms.split("bedrooms")[0].strip()
            num_bedrooms = int(num_bedrooms)
        else:
            num_bedrooms = 0

        for transaction in table_response:
            price_paid = transaction.xpath('td[3]//text()').extract_first()
            price_paid = price_paid.replace("£", "").replace(",", "")
            price_paid = int(price_paid)

            ml_item = RightItem()
            ml_item['sale_date'] = transaction.xpath('td[1]//text()').extract_first()
            ml_item['price_paid'] = price_paid
            ml_item['property'] = transaction.xpath('td[2]//text()').extract_first()
            ml_item['url'] = response.url
            ml_item['source_url'] = self.url_page
            ml_item['number_rooms'] = num_bedrooms
            ml_item['id'] = response.url.split("prop=")[-1].split("&")[0]
            ml_item['latitude'] = latitude
            ml_item['longitude'] = longitude
            ml_item['date_added'] = date_added
            ml_item['number_imgs'] = num_imgs
            ml_item['name_area'] = self.name_area

            # self.item_count += 1
            # print('\n\n\n' + '*' * 10)
            # print(self.item_count)
            # print('*' * 10 + '\n')
            # if self.item_count > 40:
            #     raise CloseSpider('item_exceeded')
            yield ml_item
