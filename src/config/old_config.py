# Google 搜索配置
GOOGLE_SEARCH_URL = "https://www.google.com/search"
GOOGLE_DOMAINS = {
    'us': 'google.com',
    'uk': 'google.co.uk',
    'in': 'google.co.in',
    'au': 'google.com.au',
    'gh': 'google.com.gh',
}

# 监控关键词列表
KEYWORDS = [
    "online jobs",
    "work from home",
    "online work",
    "make money online",
    "earn money online",
    "remote jobs",
    "work at home",
    "online earning",
    "earn money now",
    "money earning websites",
    "make money today",
    "how to free money online",
    "how to make cash online",
    "how can i get money online for free",
    "work from anywhere jobs hiring",
    "remotejobs",
    "remote career opportunities",
    "no experience work at home jobs",
    "ways to make money at home",
    "online jobs in India",
    "remote jobs worldwide"
]

# 要监控的市场（国家/地区）
MARKETS = ['in', 'gh']

# 排除的域名列表
EXCLUDED_DOMAINS = {
    'in3.tinrh.com',
    'tinrh.com',
    # 在这里添加更多要排除的域名
}

# 截图设置
SCREENSHOT_DIR = "screenshots"
SCREENSHOT_WIDTH = 1920
SCREENSHOT_HEIGHT = 1080

# 结果设置
RESULTS_DIR = "results"

# 浏览器设置
BROWSER_ARGS = [
    '--no-sandbox',
    '--disable-setuid-sandbox',
    '--disable-dev-shm-usage',
    '--disable-accelerated-2d-canvas',
    '--disable-gpu',
    '--lang=en-US,en'
]

# 延迟设置（秒）
MIN_DELAY = 2
MAX_DELAY = 5

# 重试设置
MAX_RETRIES = 3
RETRY_DELAY = 5 