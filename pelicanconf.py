#!/usr/bin/env python
# -*- coding: utf-8 -*- #

AUTHOR = u'Henrik Olsson'
SITENAME = u'fixme.se'

#SITEURL="http://localhost:8000"
SITEURL="https://fixme.se"

RELATIVE_URLS = False

TIMEZONE = 'Europe/Stockholm'

DEFAULT_LANG = u'en'

# Blogroll
LINKS =  (('bitbucket', 'https://bitbucket.org/henrik/'),
          ('github', 'https://github.com/henrikolsson'))

MENUITEMS = (('bitbucket', 'https://bitbucket.org/henrik/'),
             ('github', 'https://github.com/henrikolsson'))
             
# Social widget
SOCIAL = ()

DEFAULT_PAGINATION = 10

ARTICLE_URL = '/{date:%Y}/{date:%m}/{date:%d}/{slug}.html'
ARTICLE_LANG_URL = '/{date:%Y}/{date:%m}/{date:%d}/{slug}-{lang}.html'
PAGE_URL = '{date:%Y}/{date:%m}/{date:%d}/pages/{slug}.html'
PAGE_LANG_URL = '{date:%Y}/{date:%m}/{date:%d}/pages/{slug}-{lang}.html'
ARTICLE_SAVE_AS = '{date:%Y}/{date:%m}/{date:%d}/{slug}.html'
ARTICLE_LANG_SAVE_AS = '{date:%Y}/{date:%m}/{date:%d}/{slug}-{lang}.html'
PAGE_SAVE_AS = '{date:%Y}/{date:%m}/{date:%d}/pages/{slug}.html'
PAGE_LANG_SAVE_AS = '{date:%Y}/{date:%m}/{date:%d}/pages/{slug}-{lang}.html'

THEME="themes/default"

MD_EXTENSIONS = ['codehilite(css_class=highlight,guess_lang=False)']

