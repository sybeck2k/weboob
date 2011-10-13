# -*- coding: utf-8 -*-

# Copyright(C) 2010-2011  Romain Bignon, Pierre Mazière
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


from datetime import date
from weboob.capabilities.bank import Operation
from weboob.capabilities.bank import Account
from weboob.tools.browser import BasePage, BrowserUnavailable

class LoginPage(BasePage):
    def login(self, agency, login, passwd):
        self.browser.select_form(nr=0)
        self.browser['agenceId'] = agency
        self.browser['compteId'] = login
        self.browser['CodeId'] = passwd
        try:
            self.browser.submit()
        except BrowserUnavailable:
            # Login is not valid
            return False
        return True

class LoginResultPage(BasePage):
    def is_error(self):
        for text in self.document.find('body').itertext():
            text=text.strip()
            # Login seems valid, but password does not
            needle='Les données saisies sont incorrectes'
            if text.startswith(needle.decode('utf-8')):
                return True

        return False

class FramePage(BasePage):
    pass


class AccountsPage(BasePage):
    def get_list(self):
        l = []
        for div in self.document.getiterator('div'):
            if div.attrib.get('class')=="unCompte-CA" or\
            div.attrib.get('class')=="unCompte-CC" or\
            div.attrib.get('class')=="unCompte-CD" or\
            div.attrib.get('class')=="unCompte-CE":
                #CA=> ? maybe Assurance-vie
                #CC=> Compte Courant
                #CD=> Compte Dépôt
                #CE=> Compte d'Epargne
                account = Account()
                account.type=div.attrib.get('class')[-2:]
                account.id = div.attrib.get('id').replace('-','')
                for td in div.getiterator('td'):
                    if td.find("div") is not None and td.find("div").attrib.get('class') == 'libelleCompte':
                        account.label = td.find("div").text
                    elif td.find('a') is not None and td.find('a').attrib.get('class') is None:
                        balance = td.find('a').text.replace(u"\u00A0",'').replace('.','').replace('+','').replace(',','.')
                        account.balance = float(balance)
                        account.link_id = td.find('a').attrib.get('href')

                l.append(account)

        return l

class AccountHistoryPage(BasePage):
    def get_specific_operations(self,tableHeaderPrefixes,debitColumns,creditColumns):
        operations = []
        for td in self.document.iter('td'):
            text=td.findtext("b")
            if text is None:
                continue
            for i in range(len(tableHeaderPrefixes)):
                if text.startswith(tableHeaderPrefixes[i].decode('utf-8')):
                    tbody=td.getparent().getparent()
                    for tr in tbody.iter('tr'):
                        tr_class=tr.attrib.get('class')
                        if tr_class == 'tbl1' or tr_class=='tbl2':
                            tds=tr.findall('td')
                            d=date(*reversed([int(x) for x in tds[0].text.split('/')]))
                            label=u''+tds[1].find('a').text.strip()
                            if tds[debitColumns[i]].text.strip() != u"":
                                amount = - float(tds[debitColumns[i]].text.strip().replace('.','').replace(',','.').replace(u"\u00A0",'').replace(' ',''))
                            else:
                                amount= float(tds[creditColumns[i]].text.strip().replace('.','').replace(',','.').replace(u"\u00A0",'').replace(' ',''))
                            operation=Operation(len(operations))
                            operation.date=d
                            operation.label=label
                            operation.amount=amount
                            operations.append(operation)
        return operations

    def get_operations(self,account):
        if account.type=="CA":
            return [] # Not supported: page example required
        elif account.type=="CC":
            return self.get_specific_operations(['Opérations effectuées'],[3],[4])
        elif account.type=="CD":
            return self.get_specific_operations(['Solde au'],[2],[3])
        elif account.type=="CE":
            return self.get_specific_operations(['Solde au'],[2],[3])


