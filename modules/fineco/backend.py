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

from .browser import FinecoBrowser
from decimal import Decimal
import string

from weboob.capabilities.bank import CapBank, AccountNotFound, Recipient, Account
from weboob.tools.backend import Module, BackendConfig
from weboob.tools.value import ValueBackendPassword

__all__ = ['FinecoModule']


class FinecoModule(Module, CapBank):
    NAME = 'fineco'
    DESCRIPTION = u'Fineco banking (Italy)'
    MAINTAINER = u'Roberto Migli'
    EMAIL = 'robertomigli@gmail.com'
    LICENSE = 'AGPLv3+'
    VERSION = '1.0'
    CONFIG = BackendConfig(ValueBackendPassword('login',    label='Identifiant', regexp='^\d{1,13}\w$', masked=False),
                           ValueBackendPassword('password', label='Mot de passe'))

    BROWSER = FinecoBrowser

    def create_default_browser(self):
        return self.create_browser(self.config['login'].get(), self.config['password'].get())

    def iter_accounts(self):
        for account in self.browser.get_accounts_list():
            yield account

    def get_account(self, _id):
        """
        Get an account from its ID.

        :param id: ID of the account
        :type id: :class:`str`
        :rtype: :class:`Account`
        :raises: :class:`AccountNotFound`
        """
        account = self.browser.get_account(_id)
        if account:
            return account
        else:
            raise AccountNotFound()

    def iter_coming(self, account):
        """
        Iter coming transactions on a specific account.

        :param account: account to get coming transactions
        :type account: :class:`Account`
        :rtype: iter[:class:`Transaction`]
        :raises: :class:`AccountNotFound`
        """
        raise NotImplementedError()

    def iter_history(self, account):
        """
        Iter history of transactions on a specific account.

        :param account: account to get history
        :type account: :class:`Account`
        :rtype: iter[:class:`Transaction`]
        :raises: :class:`AccountNotFound`
        """
        with self.browser:
            for tr in self.browser.get_history(account):
                yield tr

    def transfer(self, account, recipient, amount, reason):
        """
        Make a transfer from an account to a recipient.

        :param account: account to take money
        :type account: :class:`Account`
        :param recipient: account to send money
        :type recipient: :class:`Recipient`
        :param amount: amount
        :type amount: :class:`decimal.Decimal`
        :param reason: reason of transfer
        :type reason: :class:`unicode`
        :rtype: :class:`Transfer`
        :raises: :class:`AccountNotFound`, :class:`TransferError`
        """
        raise NotImplementedError()
