import re
import ssl
import asyncio
import json
from OpenSSL import crypto
import aiohttp
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup, SoupStrainer


class TLSHTTPScanner:
    def __init__(
        self,
        mass_scan_results_file="masscanResults.txt",
        ssl_port=443,
        timeout=5,
        chunkSize=10000,
        MAX_CONCURRENT=100,
        semaphore_limit=90,
        ports=[80],
        protocols=["http://", "https://"],
        server_url="http://127.0.0.1:5000/insert",
    ):
        self.mass_scan_results_file = mass_scan_results_file
        self.ssl_port = ssl_port
        self.timeout = timeout
        self.chunkSize = chunkSize
        self.protocols = protocols
        self.server_url = server_url
        self.ports = ports
        self.semaphore = asyncio.Semaphore(semaphore_limit)
        self.MAX_CONCURRENT = MAX_CONCURRENT

    def is_valid_domain(self, common_name):
        return re.match(r"^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", common_name) is not None

    async def fetch_certificate(self, ip):
        try:
            cert = await asyncio.to_thread(ssl.get_server_certificate, (ip, self.ssl_port), timeout=self.timeout)
            x509 = crypto.load_certificate(crypto.FILETYPE_PEM, cert)
            return ip, x509.get_subject().CN
        except:
            return ip, ""

    async def makeGetRequest(self, session, protocol, ip, common_name, makeRequestByIP=True):
        port = "80" if protocol == "http://" else self.ssl_port
        target = ip if makeRequestByIP else common_name
        url = f"{protocol}{target}:{port}"

        try:
            async with session.get(url, allow_redirects=True, timeout=self.timeout, ssl=False) as res:
                text = await res.text(errors="ignore")
                title = ""
                try:
                    soup = BeautifulSoup(text, "html.parser")
                    if soup.title:
                        title = soup.title.string or ""
                except:
                    pass

                return {
                    "title": title,
                    "request": url,
                    "ip": ip,
                    "domain": common_name,
                    "response_text": text[:300]
                }
        except:
            return None

    async def check_site(self, session, ip, cn):
        results = {}
        if "*" in cn or not self.is_valid_domain(cn):
            for p in self.protocols:
                results[p] = await self.makeGetRequest(session, p, ip, cn, True)
        else:
            for p in self.protocols:
                results[p+"_domain"] = await self.makeGetRequest(session, p, ip, cn, False)
                results[p+"_ip"] = await self.makeGetRequest(session, p, ip, cn, True)

        results = {k:v for k,v in results.items() if v}
        return results if results else None

    async def extract_and_scan(self):
        with open(self.mass_scan_results_file) as f:
            content = f.read()

        ips = re.findall(r"\d+\.\d+\.\d+\.\d+", content)

        for i in range(0, len(ips), self.chunkSize):
            async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit=self.MAX_CONCURRENT, ssl=False)) as session:
                chunk = ips[i:i+self.chunkSize]
                certs = await asyncio.gather(*[self.fetch_certificate(ip) for ip in chunk])
                results = await asyncio.gather(*[self.check_site(session, ip, cn) for ip, cn in certs])
                results = [r for r in results if r]

                async with session.post(self.server_url, json=results, ssl=False) as res:
                    print("Mongo:", res.status)
