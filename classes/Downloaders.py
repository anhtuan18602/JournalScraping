import multiprocessing as mp
import requests
import os
import time
import csv
import shutil
import undetected_chromedriver as uc
from selenium.webdriver.chrome.options import Options
from .Utils import get_user_agent, make_download_target
import random
from concurrent.futures import ProcessPoolExecutor

class WileyArticleDownloader:
    def __init__(self, download_targets, open_access_only=False, limit=1400,
                 delay=5, retries=2, processes=4 , output_results=False):
        self.download_targets = download_targets
        self.limit = limit
        self.delay = delay
        self.open_access_only = open_access_only
        self.max_retries = retries
        self.processes = processes
        self.output_results = output_results
        self.results = []
        self.queue = self._populate_download_queue()

    def _populate_download_queue(self):
        return self.download_targets[:self.limit]

    def _download_worker(self, job):
        #time.sleep(random.uniform(1,5)) 
        #time.sleep(random.uniform(0.5, 2.5))
        job_result = job.copy()

        path, _ = os.path.split(job['target'])
        os.makedirs(path, exist_ok=True)
        if os.path.isfile(job['target']):
            job_result.update({'downloaded': False, 'message': 'file exists','code':''})
            print(job['target'], 'exists')
            return job_result

        print('downloading', job['url'], 'to', job['target'])

        options = uc.ChromeOptions()
        options.headless = False
        options.add_argument(f"user-agent={get_user_agent()}")
        options.add_argument("--window-size=1280,800")
        options.add_argument("lang=en-US,en;q=0.9")
        profile_path = f"/tmp/selenium_profile_{os.getpid()}"
        options.add_argument(f"--user-data-dir={profile_path}")
        prefs = {
            "download.default_directory": os.path.abspath(path),
            "plugins.always_open_pdf_externally": True,  # Disable Chrome PDF viewer, force download
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True,
        }
        options.add_experimental_option("prefs", prefs)

        driver = None
        try:
            driver = uc.Chrome(options=options)

            trial = 0
            while trial < self.max_retries:
                trial += 1
                try:
                    driver.get(job['url'])
                    time.sleep(self.delay)
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(random.uniform(1.5, 4.0))
                    page_source = driver.page_source
                    size = len(page_source.encode('utf-8')) / 1024 # in KB
                    # Save fallback as HTML
                    if size > 100:
                        with open(job['target'], 'w', encoding='utf-8') as f:
                            f.write(page_source)
                        job_result.update({'downloaded': True, 'message': 'saved html', 'code': 200})
                        break  # Exit retry loop on success
                    else:
                        time.sleep(self.delay)

                except Exception as e:
                    print(f"Download attempt {trial} failed for {job['url']}: {e}")
                    time.sleep(self.delay)

        except Exception as e:
            print(f"Driver init failed: {e}")
            job_result.update({'downloaded': False, 'message': 'driver init failed', 'code': None})
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass

        if not job_result.get('downloaded', False):
            job_result.update({'downloaded': False, 'message': 'too many retries', 'code': None})

        return job_result
        """
        trial = 0
        
        while trial < self.max_retries:
            trial += 1

            download_result = requests.get(job['url'], headers=get_user_agent())
            if download_result.status_code != requests.codes.ok:
                time.sleep(self.delay)
                continue

            if "text/html" in download_result.headers['content-type']:
                with open(job['target'], 'w', encoding="utf-8") as f:
                    f.write(download_result.text)
            else:
                with open(job['target'], 'wb') as f:
                    f.write(download_result.content)

            job_result.update({'downloaded': True, 'message': '','code':download_result.status_code})
            time.sleep(self.delay)
            return job_result

        job_result.update({'downloaded': False, 'message': 'too many retries','code':download_result.status_code})
        return job_result
        """

    def download(self):
        """
        pool = mp.Pool(self.processes)
        self.results = pool.map(self._download_worker, self.queue)
        pool.close()
        pool.join()
        """
        with ProcessPoolExecutor(max_workers=2) as executor:
            self.results = list(executor.map(self._download_worker, self.queue))

        if self.output_results:
            time_string = time.strftime("%Y%m%d_%H%M", time.localtime()) + "_" + str(int(time.time()))
            logdir = 'logs'
            filename = f'downloads_{time_string}.csv'
            os.makedirs(logdir,exist_ok=True)
            with open(os.path.join(logdir, filename), 'w') as f:
                writer = csv.DictWriter(f, self.results[0].keys())
                writer.writeheader()
                writer.writerows(self.results)

class ArticleDownloader:
    def __init__(self, download_targets, open_access_only=False, limit=1400,
                 delay=1, retries=2, processes=4 , output_results=False):
        self.download_targets = download_targets
        self.limit = limit
        self.delay = delay
        self.open_access_only = open_access_only
        self.max_retries = retries
        self.processes = processes
        self.output_results = output_results
        self.results = []
        self.queue = self._populate_download_queue()

    def _populate_download_queue(self):
        return self.download_targets[:self.limit]

    def _download_worker(self, job):
        #time.sleep(random.uniform(0.5, 2.5))
        job_result = job.copy()

        path, _ = os.path.split(job['target'])
        os.makedirs(path, exist_ok=True)
        if os.path.isfile(job['target']):
            job_result.update({'downloaded': False, 'message': 'file exists','code':''})
            print(job['target'], 'exists')
            return job_result

        print('downloading', job['url'], 'to', job['target'])

        
        trial = 0
        
        while trial < self.max_retries:
            trial += 1

            download_result = requests.get(job['url'], headers=get_user_agent())
            if download_result.status_code != requests.codes.ok:
                time.sleep(self.delay)
                continue

            if "text/html" in download_result.headers['content-type']:
                with open(job['target'], 'w', encoding="utf-8") as f:
                    f.write(download_result.text)
            else:
                with open(job['target'], 'wb') as f:
                    f.write(download_result.content)

            job_result.update({'downloaded': True, 'message': '','code':download_result.status_code})
            time.sleep(self.delay)
            return job_result

        job_result.update({'downloaded': False, 'message': 'too many retries','code':download_result.status_code})
        return job_result

    def download(self):
        pool = mp.Pool(self.processes)
        self.results = pool.map(self._download_worker, self.queue)
        pool.close()

        if self.output_results:
            time_string = time.strftime("%Y%m%d_%H%M", time.localtime()) + "_" + str(int(time.time()))
            logdir = 'logs'
            filename = f'downloads_{time_string}.csv'
            os.makedirs(logdir,exist_ok=True)
            with open(os.path.join(logdir, filename), 'w') as f:
                writer = csv.DictWriter(f, self.results[0].keys())
                writer.writeheader()
                writer.writerows(self.results)
