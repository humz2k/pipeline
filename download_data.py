import wget
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

url = 'https://stars.uchicago.edu/images/StoneEdge/0.5meter/2022/2022-05-12/ruoyang/dark_h-alpha_1.0s_bin1H_220512_203147_ruoyang_seo_0_RAW.fits'
filename = wget.download(url)
