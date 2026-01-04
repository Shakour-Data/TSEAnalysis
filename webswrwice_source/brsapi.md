تمام وب‌سرویس‌های معرفی‌شده BrsApi در یک صفحه جمع شده‌اند و برای هرکدام یک صفحه راهنما (دیتیل) جداگانه هم وجود دارد. در ادامه لینک مستقیم هر سرویس + توضیح کوتاه آمده است.[1][2][3]

> **توجه مهم:** برای دسترسی به **کلید لایسنس (License Key)** و **تنظیمات سرور** جهت استفاده از این سرویس‌ها، به فایل محرمانه `docs/deployment/server_setup.md` مراجعه کنید. رعایت نکات مربوط به `User-Agent` در آن فایل الزامی است.

## لینک فهرست همه وب‌سرویس‌ها

- صفحه معرفی و فهرست تمام APIها (بورس، شاخص، ETF، آپشن، معاملات، تاریخچه، کندل، سهامداران، کدال، طلا/ارز، رمزارز، کامودیتی):  
  https://brsapi.ir/about-tsetmc-stock-exchange-free-bourse-api/  (بخش «APIهای موجود در BrsApi.ir»)[3]

## وب‌سرویس‌های بورس و فرابورس

- API دیتای همه نمادهای بورس (تابلوی لحظه‌ای همه نمادها، شبیه خروجی AllSymbols):  
  https://brsapi.ir/  – تابلوی لحظه‌ای تمام نمادهای بورس/فرابورس با جزئیات قیمت، معاملات، حقیقی–حقوقی و عرضه/تقاضا در قالب JSON.[1]
- API شاخص بورس و فرابورس:  
  https://brsapi.ir/bourse-api-index-webservice/  – دریافت لحظه‌ای شاخص کل، هم‌وزن، شاخص‌های منتخب، شاخص‌های فرابورس و متغیرهایی مثل مقدار شاخص، تغییر، درصد تغییر، مین/مکس، ارزش بازار و حجم معاملات.[2]
- API دیتای جامع نماد بورسی:  
  https://brsapi.ir/bourse-api-symbol-webservice/  – جزئیات کامل یک نماد خاص (ترکیب اطلاعات قیمتی، معاملاتی، بنیادی/تابلویی) برای تحلیل عمیق یک نماد.[3]
- API صندوق‌های ETF بورس (NAV و داده‌های صندوق‌ها):  
  https://brsapi.ir/bourse-api-etf-funds-nav-webservice/  – اطلاعات اختصاصی صندوق‌های ETF شامل NAV و وضعیت معاملاتی.[3]
- API بازار آپشن بورس:  
  https://brsapi.ir/bourse-api-option-webservice/  – اطلاعات قراردادهای اختیار معامله (آپشن) شامل قیمت، سررسید، نوع قرارداد و سایر پارامترهای مرتبط.[3]
- API ریزمعاملات بورس:  
  https://brsapi.ir/bourse-api-transaction-webservice/  – لاگ تریدهای انجام‌شده (Tick/Trade by Trade) برای نمادها جهت تحلیل ریزساختار بازار.[3]
- API تاریخچه معاملات بورس:  
  https://brsapi.ir/bourse-api-history-webservice/  – داده‌های تاریخی روزانه معاملات (OHLC و حجم/ارزش) برای استفاده در بک‌تست و تحلیل زمانی.[3]
- API کندل‌استیک بورس:  
  https://brsapi.ir/bourse-api-candlestick-webservice/  – تولید کندل در تایم‌فریم‌های مختلف (مثلاً روزانه/ساعتی) بر اساس دیتای معاملات.[3]
- API سهامداران بورس:  
  https://brsapi.ir/bourse-api-shareholder-webservice/  – اطلاعات سهامداران عمده/اصلی نمادها و تغییرات مالکیت آنها.[3]
- API اطلاعیه‌های کدال:  
  https://brsapi.ir/bourse-api-codal-webservice/  – دریافت اطلاعیه‌های کدال مرتبط با ناشران، برای اتصال رویدادهای بنیادی به سیستم تحلیلی.[3]

## سایر وب‌سرویس‌های بازار مالی

- API رایگان کامودیتی:  
  https://brsapi.ir/free-api-commodity-webservice/  – داده انواع کامودیتی‌ها (کالاهای پایه) جهت رصد بازارهای جهانی مرتبط.[3]
- API رایگان طلا، ارز و سکه:  
  https://brsapi.ir/free-api-gold-currency-webservice/  – نرخ لحظه‌ای طلا، انواع ارز و سکه برای اتصال به پنل مانیتورینگ یا استراتژی‌های آربیتراژی.[3]
- API رایگان رمزارز:  
  https://brsapi.ir/free-api-cryptocurrency-webservice/  – قیمت و مشخصات رمزارزها جهت نمایش یا تحلیل در کنار سایر بازارها.[3]

اگر خواستی، می‌توان برای هر وب‌سرویس، پارامترهای ورودی/خروجی مهم و ساختار JSON را هم جدول‌وار درآورد تا سریع در کد از آن استفاده کنی.

[1](https://brsapi.ir/)
[2](https://www.api.ir/web-service/%D8%A2%D8%B4%D9%86%D8%A7%DB%8C%DB%8C-%D8%A8%D8%A7-%D9%88%D8%A8-%D8%B3%D8%B1%D9%88%DB%8C%D8%B3%D9%87%D8%A7/)
[3](https://7learn.com/blog/what-is-web-service)
[4](https://iranhost.com/blog/%D9%88%D8%A8-%D8%B3%D8%B1%D9%88%DB%8C%D8%B3-%DA%86%DB%8C%D8%B3%D8%AA%D8%9F-%D9%88-%D9%87%D8%B1-%D8%A2%D9%86%DA%86%D9%87-%D8%A8%D8%A7%DB%8C%D8%B3%D8%AA%DB%8C-%D8%AF%D8%B1-%D9%85%D9%88%D8%B1%D8%AF/)
[5](https://mizbancloud.com/blog/What-is-a-web-service)
[6](https://www.portal.ir/how-to-build-a-website)
[7](https://brsapi.ir)
[8](https://sarvdata.com/blog/instructions-for-using-the-rest-api-web-service/)
[9](https://brsapi.ir/about-tsetmc-stock-exchange-free-bourse-api/)
[10](https://webshahr.site/%D9%88%D8%A8-%D8%B3%D8%B1%D9%88%DB%8C%D8%B3-%DA%86%DB%8C%D8%B3%D8%AA/)
[11](https://brsapi.ir/bourse-api-index-webservice/)