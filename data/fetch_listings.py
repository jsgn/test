__author__ = 'shivnarayan'
import os
import sys
paths = ['/home/ubuntu/projects/','/home/ubuntu/projects/test/']
for path in paths:
    if path not in sys.path:
        sys.path.append(path)
os.environ['DJANGO_SETTINGS_MODULE'] = 'test.settings'

from lxml.html import document_fromstring
from data.base import clean,html
import xlwt
from string import ascii_lowercase

def scraper_category(alphabet):
    c=0
    f=open('apparel.csv','w')
    book = xlwt.Workbook()
    sh = book.add_sheet('sheet1')
    url='http://fashion-apparel.exportersindia.com/'+alphabet+'.htm'
    print 'Starting for url :',url,'\n\n'
    doc1=html(url)
    atags=doc1.xpath(".//ul[@class='fo uo dul hig-anchors ac-fl ac-w25 ac-pt3px ac-pb3px ac-bc-raquo-b']//li//a")
    for i in atags:
        page_url=i.attrib['href']
        doc2=document_fromstring(urllib.urlopen(page_url).read())
        for i in doc2.xpath(".//h3[@class='xxxlarge fwn ml5px']//a"):
            company_page= i.attrib['href']
            company_name=i.text_content()
            doc3=html(company_page)
            about=clean(doc3.xpath(".//nav[@class='comPro']//p")[0].text_content())
            doc4=doc3.xpath(".//section[@class='box2']")[1]
            contact_name=doc4.xpath(".//nav//b")[0].text_content()
            details=doc4.xpath(".//p")
            try:
                address=details[0].text_cotent()
            except:
                address=''
            try:
                if 'Telephone :' in details[1].text_content():
                    phone=details[2].text_content().split(':')[1]
            except:
                phone=''

            try:
                if 'Fax No :' in details[2].text_content():
                    fax=details[2].text_content().split(':')[1]
            except:
                fax=''
            print '\n',company_page
            print about,'\nname:',contact_name,'address: ',address,'phone: ', phone,'fax: ', fax
            # f.write(company_name+','+contact_name+','+ str(phone)+','+str(fax)+','+address+','+about+'\n')
            sh.write(c,0,str(unidecode(company_page)))
            sh.write(c,1,str(unidecode(contact_name)))
            sh.write(c,2,str(unidecode(phone)))
            sh.write(c,3,str(unidecode(fax)))
            sh.write(c,4,str(unidecode(address)))
            sh.write(c,5,str(unidecode(about)))
            c+=1
    book.save('test_ap.xls')

    f.close()
if __name__=='__main__':
    for i in ascii_lowercase:
        scraper_category(i)


