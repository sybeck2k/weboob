# -*- coding: utf-8 -*-

# Copyright(C) 2014      Roberto Migli
#
# This file is part of weboob.
#
# weboob is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# weboob is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with weboob. If not, see <http://www.gnu.org/licenses/>.


from urlparse import urlsplit, parse_qsl, urlparse
from datetime import datetime, timedelta

from weboob.tools.browser import BaseBrowser, BrowserIncorrectPassword
from weboob.capabilities.bank import Transfer, TransferError

from .pages import LoginPage, LoginErrorPage, AccountsPage, EmptyPage, OperationsPage


class FinecoBrowser(BaseBrowser):
    BASEURL = 'https://nuovosito.fineco.it'

    PROTOCOL = 'https'
    DOMAIN = 'nuovosito.fineco.it'
    ENCODING = 'utf-8'
    USER_AGENT = BaseBrowser.USER_AGENTS['wget']
    PAGES = {'https://www.fineco.it/it/public':   LoginPage,
             'https://www.fineco.it/public/error': LoginErrorPage,
             'https://nuovosito.fineco.it/conto-e-carte': AccountsPage,
             'https://nuovosito.fineco.it/conto-e-carte/movimenti/movimenti-conto': OperationsPage,
             'https://nuovosito.fineco.it/conto-e-carte/movimenti/movimenti-conto/ricerca': OperationsPage,
             'https://nuovosito.fineco.it/conto-e-carte/movimenti/movimenti-conto/page/(\d+)$': OperationsPage,
             'https://nuovosito.fineco.it/home/myfineco': EmptyPage,
            }

    def is_logged(self):
        return not self.is_on_page(LoginPage) and not self.is_on_page(LoginErrorPage)

    def home(self):
        return self.location('https://www.fineco.it/it/public')

    def login(self):
        assert isinstance(self.username, basestring)
        assert isinstance(self.password, basestring)

        if not self.is_on_page(LoginPage):
            self.location('https://www.fineco.it/', no_login=True)

        self.page.login(self.username, self.password)

        if not self.is_logged() or self.is_on_page(LoginErrorPage):
            raise BrowserIncorrectPassword()

    def get_accounts_list(self):
        if not self.is_on_page(AccountsPage):
            self.location('https://nuovosito.fineco.it/conto-e-carte')
        return self.page.get_list()

    def get_account(self, id):
        assert isinstance(id, basestring)

        l = self.get_accounts_list()
        for a in l:
            if a.id == id:
                return a

        return None

    def list_operations(self):
        go_next = True
        while go_next:
            if not self.is_on_page(OperationsPage):
                return

            for op in self.page.get_history():
                yield op

            go_next = self.page.go_next()

    def get_history(self, account):
        transactions = []
        last_debit = None
        self.location('https://nuovosito.fineco.it/conto-e-carte/movimenti/movimenti-conto')
        
        for tr in self.list_operations():
            # to prevent redundancy with card transactions, we do not
            # store 'RELEVE CARTE' transaction.
            if tr.raw != 'RELEVE CARTE':
                transactions.append(tr)
            elif last_debit is None:
                last_debit = (tr.date - timedelta(days=10)).month

        coming_link = self.page.get_coming_link() if self.is_on_page(OperationsPage) else None
        if coming_link is not None:
            for tr in self.list_operations(coming_link):
                transactions.append(tr)

        month = 0

        transactions.sort(key=lambda tr: tr.rdate, reverse=True)
        return transactions
