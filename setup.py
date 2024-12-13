from setuptools import setup, find_packages

setup(
    name="google_ads_monitor",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        'flask',
        'flask-cors',
        'playwright',
        'beautifulsoup4',
        'requests',
        'urllib3'
    ],
    python_requires='>=3.9',
) 