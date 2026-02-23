from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from django.utils.translation import override

class StaticViewSitemap(Sitemap):
    priority = 0.8
    changefreq = "weekly"

    def items(self):
        return ["home", "about", "contacts", "past-events"]

    def get_urls(self, page=1, site=None, protocol=None):
        urls = []
        for lang in ("bg", "en"):
            with override(lang):
                urls.extend(super().get_urls(page=page, site=site, protocol=protocol))
        return urls