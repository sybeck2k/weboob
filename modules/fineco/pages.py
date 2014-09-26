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


import urllib
from urlparse import urlparse, parse_qs
from decimal import Decimal
import re
from dateutil.relativedelta import relativedelta
from datetime import datetime
import datetime
from lxml import etree
import inspect

from weboob.tools.browser import BasePage, BrowserIncorrectPassword, BrokenPageError
from weboob.tools.ordereddict import OrderedDict
from weboob.capabilities.bank import Account
from weboob.tools.capabilities.bank.transactions import FrenchTransaction
from weboob.tools.date import parse_french_date


class LoginPage(BasePage):
    def login(self, login, passwd):
    	formcount=0
    	for frm in self.browser.forms():  
    	  if str(frm.attrs["id"])=="loginForm":
    	    break
    	  formcount=formcount+1
    	self.browser.select_form(nr=formcount)

        self.browser['LOGIN'] = login.encode(self.browser.ENCODING)
        self.browser['PASSWD'] = passwd.encode(self.browser.ENCODING)
        self.browser.submit(nologin=True)


class LoginErrorPage(BasePage):
    pass


class ChangePasswordPage(BasePage):
    def on_loaded(self):
        raise BrowserIncorrectPassword('Please change your password')

class VerifCodePage(BasePage):
    def on_loaded(self):
        raise BrowserIncorrectPassword('Unable to login: website asks a code from a card')

class InfoPage(BasePage):
    pass


class EmptyPage(BasePage):
    pass


class TransfertPage(BasePage):
    pass


class UserSpacePage(BasePage):
    pass

class EmptyPage(BasePage):
    pass

class AccountsPage(BasePage):
    TYPES = {'C/C':             Account.TYPE_CHECKING,
             'Livret':          Account.TYPE_SAVINGS,
             'Pret':            Account.TYPE_LOAN,
             'Compte Courant':  Account.TYPE_CHECKING,
             'Compte Cheque':   Account.TYPE_CHECKING,
             'Compte Epargne':  Account.TYPE_SAVINGS,
            }

    def get_list(self):
        accounts = OrderedDict()
        accounts_container = self.document.xpath('//div[@id="accounts-container"]')[0]
        
        for el in self.document.getroot().cssselect('select#account-select option'):
            account_data = [x.strip() for x in el.text.split(u"\u2014")]
            account = Account()
            account.id = account_data[0]
            account.label = account_data[1]
            account.balance = Decimal(FrenchTransaction.clean_amount(account_data[2]))
            yield account


class Transaction(FrenchTransaction):
    PATTERNS = [(re.compile('^(Bonifico|Giroconto) .*'), FrenchTransaction.TYPE_TRANSFER),
                (re.compile('^(Pagamento|Utenza|FastPay) .*'),        FrenchTransaction.TYPE_ORDER),
                (re.compile('^(Utilizzo carta di credito|Pagobancomat) .*'),
                                                          FrenchTransaction.TYPE_CARD),
                (re.compile('^Prelievo .*'),
                                                          FrenchTransaction.TYPE_WITHDRAWAL),
                (re.compile('^Addebitp Assegno .*'),  FrenchTransaction.TYPE_CHECK),
                (re.compile('^(Addebito canone|Addebito costo|Interessi) .*'),FrenchTransaction.TYPE_BANK),
                (re.compile('^Versamento .*'),FrenchTransaction.TYPE_DEPOSIT),
               ]

class OperationsPage(BasePage):
    def get_history(self):
        p = re.compile(".*movimenti-conto$")
        if p.match(self.browser.geturl()):
            formcount=0
            for frm in self.browser.forms():  
              if str(frm.attrs["id"])=="frmRicerca":
                break
              formcount=formcount+1
            self.browser.select_form(nr=formcount)

            today = datetime.date.today()
            self.browser.form['dataDal'] = today.replace(year = today.year - 2).strftime("%d/%m/%Y").encode(self.browser.ENCODING)
            self.browser.form['dataAl'] = today.strftime("%d/%m/%Y").encode(self.browser.ENCODING)

            self.browser.submit(nologin=True)
        
        index = 0
        trs = self.browser.page.document.getroot().cssselect('table#FormID tbody tr')

        for tr,tr_detail in zip(trs[0::2], trs[1::2]):
            operation = Transaction(index)
            index += 1
            
            operation_data = []
            for td in tr.iterdescendants():
                innerText = td.text
                if not ((innerText is None) or (len(innerText) == 0)):
                   operation_data.append(innerText.strip())
            
            # fix for operations with a link in the description
            if operation_data[2] == '':
                del operation_data[2]

            self.logger.debug('Found transaction:' % operation_data)

            raw = u' '.join(operation_data[2:-1])
            print raw
            

            operation.parse(date=operation_data[0], vdate=operation_data[1], raw=raw)

            #raise Error()
            operator = operation_data[6][0]
            operation_amount = operation_data[6][1:]

            if  operator== "+":
                operation.set_amount(operation_amount)
            else:
                operation.set_amount("",operation_amount)
            yield operation

    def go_next(self):
        next_link = self.document.getroot().cssselect('form.frm_pagination a.pag_next')

        if len(next_link) == 0:
            return False

        next_link = next_link[0]

        self.browser.location(next_link.get('href'))

        return True

    def get_coming_link(self):
        try:
            a = self.parser.select(self.document, u'//a[contains(text(), "Opérations à venir")]', 1, 'xpath')
        except BrokenPageError:
            return None
        else:
            return a.attrib['href']

class NoOperationsPage(OperationsPage):
    def get_history(self):
        return iter([])
