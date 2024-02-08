from selenium import webdriver
from selenium.webdriver.common.by import By


class HumanVerificationMiddleware:
    def process_response(self,request, response, spider):
        print(f"response headers righthere: {response.headers}")
        request.user_agent = 'Mozilla/5.0'

        # if response.xpath('//head/title/text()').extract_first() == 'Human Verification':
        #     print("HEEEEEEEEEEEEY")
        return response
