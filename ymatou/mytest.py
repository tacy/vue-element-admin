import hashlib
import requests

# PaymentMethod: 02-支付宝, 13-微信
user_code = 'ubay_test'
password = '123456'
key = '0000'
xml = '''<Message>
        <Body>
                <SourcePlatform>UBAY</SourcePlatform>
                <SourceDealerShop>21444</SourceDealerShop>
                <SaleOrderCode>100110101</SaleOrderCode>
                <BuyerAccount>test</BuyerAccount>
                <BuyerNickName>test</BuyerNickName>
                <Province>上海市</Province>
                <City>上海市</City>
                <District>黄浦区</District>
                <Address>1-11号</Address>
                <ReceiverName>李硅谷</ReceiverName>
                <ReceiverPhone>15822748192</ReceiverPhone>
                <ZipCode>201101</ZipCode>
                <OrderPayment>100</OrderPayment>
                <PostFee>0</PostFee>
                <BuyerPayment>100</BuyerPayment>
                <InsuranceFee>0</InsuranceFee>
                <TaxAmount>0</TaxAmount>
                <TariffAmount>0</TariffAmount>
                <AddedValueTaxAmount>0</AddedValueTaxAmount>
                <ConsumptionDutyAmount>0</ConsumptionDutyAmount>
                <PaymentMethod>02</PaymentMethod>
                <PaymentCode>1111</PaymentCode>
                <PaymentOrderSeq>122</PaymentOrderSeq>
                <CreateTime>2017-10-11 12:11:11</CreateTime>
                <PayTime>2017-10-11 12:11:11</PayTime>
                <DistributionCode>100</DistributionCode>
                <Details>
                        <Detail>
                                <ProductNumberCode>4901330742270</ProductNumberCode>
                                <SaleGoodsName>卡乐比</SaleGoodsName>
                                <SaleGoodsPrice>100</SaleGoodsPrice>
                                <SaleNumber>1</SaleNumber>
                                <SaleSubTotal>100</SaleSubTotal>
                        </Detail>
                </Details>
        </Body>
</Message>'''

xml2 = '''
<Message>
        <Body>
            <SaleOrderCode>100110101</SaleOrderCode>
        </Body>
</Message>
'''
url1 = 'http://open.nxubay.com/API/OrderInfo/createOrder.html'
url2 = 'http://open.nxubay.com/API/OrderInfo/getOrderStatus.html'
s = hashlib.md5(
    (user_code + password + xml2 + key).encode('utf-8')).hexdigest()
print(s)

data = {
    'user_code': user_code,
    'password': password,
    'xml': xml,
    'sign': s,
}

result = requests.post(url1, data=data)
print(result.content.decode('utf-8'))
