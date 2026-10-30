#!/usr/bin/env python3
"""Browser acceptance checks for the three price-analysis pages."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
from playwright.sync_api import sync_playwright, expect
from openpyxl import load_workbook

TITLE='Analisis Tren dan Perbandingan Harga Pangan Antarprovinsi'
MENUS=[('Ringkasan','ringkasan'),('Tren & fluktuasi','tren'),('Perbandingan wilayah','wilayah')]

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url',default='http://127.0.0.1:8501')
    parser.add_argument('--chromium',default='/usr/bin/chromium')
    parser.add_argument('--output-dir',type=Path,default=Path('/tmp/analyst-browser'))
    opt=parser.parse_args();out=opt.output_dir;out.mkdir(parents=True,exist_ok=True)
    report={'target':opt.url,'scope':'local browser checks; public deployment not verified','checks':[],'screenshots':[]}
    errors=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=opt.chromium,headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
        def settle(page):
            page.wait_for_timeout(700)
            assert page.get_by_test_id('stException').count()==0
        def ready(page):
            page.goto(opt.url);page.get_by_role('heading',name=TITLE,exact=True).wait_for(timeout=45000);settle(page)
        def menu(page,name):
            page.get_by_test_id('stSidebar').get_by_text(name,exact=True).click();settle(page)
        def select(page,label,value):
            box=page.get_by_role('combobox',name=re.compile(re.escape(label)))
            box.click();box.fill(value);page.get_by_role('option',name=value,exact=True).click();settle(page)
        def screenshot(page,name,width,height):
            page.set_viewport_size({'width':width,'height':height});settle(page)
            main=page.get_by_test_id('stMain');h=main.evaluate('(e)=>e.scrollHeight')
            page.set_viewport_size({'width':width,'height':max(height,min(5500,h+60))});settle(page)
            main.evaluate('(e)=>e.scrollTop=0')
            assert page.evaluate('document.body.scrollWidth<=innerWidth'),name
            page.screenshot(path=str(out/(name+'.png')),full_page=True);report['screenshots'].append(name+'.png')
            page.set_viewport_size({'width':width,'height':height})
        page=browser.new_page(viewport={'width':1440,'height':950});page.on('pageerror',lambda e:errors.append(str(e)));ready(page)
        expect(page.get_by_test_id('stMetricValue').first).to_have_text('25 / 25')
        assert page.get_by_test_id('stMetric').count()==3
        assert 'Cabai Merah Keriting' in page.get_by_test_id('stMetric').nth(2).inner_text()
        assert page.get_by_role('tab').count()==0
        assert 'Simulator anggaran' not in page.get_by_test_id('stSidebar').inner_text()
        page.screenshot(path=str(out/'ringkasan-first-screen.png'));report['screenshots'].append('ringkasan-first-screen.png')
        for label,name in MENUS:
            menu(page,label);screenshot(page,name,1440,950)
        menu(page,'Tren & fluktuasi');select(page,'Bahan pilihan','Cabai Rawit Merah')
        screenshot(page,'tren-bahan-pilihan',1440,950)
        select(page,'Bulan referensi','Januari 2021');screenshot(page,'tren-riwayat-terbatas',1440,950)
        menu(page,'Ringkasan');expect(page.get_by_test_id('stMetricValue').nth(1)).to_have_text('—')
        screenshot(page,'ringkasan-riwayat-terbatas',1440,950)
        select(page,'Bulan referensi','Oktober 2025');select(page,'Wilayah acuan','Papua Pegunungan')
        expect(page.get_by_test_id('stMetricValue').first).to_have_text('0 / 25')
        screenshot(page,'ringkasan-tanpa-harga',1440,950)
        select(page,'Wilayah acuan','Jawa Barat');menu(page,'Perbandingan wilayah')
        page.get_by_text('Lihat seluruh wilayah',exact=True).click();settle(page)
        screenshot(page,'wilayah-lengkap',1440,950)
        page.get_by_text('Sumber & cara menghitung',exact=True).click();settle(page)
        screenshot(page,'sumber-metode',1440,950)
        page.get_by_role('button',name='Siapkan laporan Excel',exact=True).click()
        download_button=page.get_by_role('button',name='Unduh laporan Excel',exact=True);download_button.wait_for(timeout=60000)
        with page.expect_download() as result:download_button.click()
        result.value.save_as(out/'browser-laporan.xlsx')
        book=load_workbook(out/'browser-laporan.xlsx')
        assert book['Harga Bersih'].max_row==32481
        assert not any(x in book.sheetnames for x in ['Sensitivitas latihan','Simulasi Anggaran','Ringkasan Skenario'])
        assert 'Satuan asumsi' not in [c.value for c in book['Harga Bersih'][1]]
        summary={r[0]:r[1] for r in book['Ringkasan'].iter_rows(min_row=2,values_only=True)}
        assert summary['Judul']==TITLE
        report['checks']+=['three menus and default findings; no budget controls or tabs','commodity trend, exact-month missing comparisons, and empty province','all-region toggle and expandable source panel','Excel download: 32,480 observations and no budget or assumed-unit sheets']
        for label,name in MENUS:
            mobile=browser.new_page(viewport={'width':390,'height':844},is_mobile=True,has_touch=True)
            mobile.on('pageerror',lambda e:errors.append(str(e)));ready(mobile)
            if label!='Ringkasan':
                mobile.get_by_test_id('stExpandSidebarButton').click();settle(mobile);menu(mobile,label)
                mobile.get_by_test_id('stSidebar').get_by_role('button').filter(has_text='keyboard_double_arrow_left').click();settle(mobile)
            screenshot(mobile,name+'-mobile',390,844);mobile.close()
        report['checks'].append('desktop and 390px mobile: all three menus without page exceptions or body overflow')
        assert not errors,errors
        report['javascript_page_errors']=errors;report['status']='passed';browser.close()
    (out/'browser-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('Browser acceptance passed')

if __name__=='__main__':main()
