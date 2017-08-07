#!/usr/bin/env python
#
# A library that provides a Python interface to the Telegram Bot API
# Copyright (C) 2015-2017
# Leandro Toledo de Souza <devs@python-telegram-bot.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see [http://www.gnu.org/licenses/].
import json

import pytest

from telegram import KeyboardButton


@pytest.fixture(scope='class')
def keyboard_button():
    return KeyboardButton(TestKeyboardButton.text,
                          request_location=TestKeyboardButton.request_location,
                          request_contact=TestKeyboardButton.request_contact)


class TestKeyboardButton:
    text = 'text'
    request_location = True
    request_contact = True

    def test_expected_values(self, keyboard_button):
        assert keyboard_button.text == self.text
        assert keyboard_button.request_location == self.request_location
        assert keyboard_button.request_contact == self.request_contact

    def test_de_list(self, bot, keyboard_button):
        keyboard_json = [keyboard_button.to_dict(), keyboard_button.to_dict()]
        inline_keyboard_buttons = KeyboardButton.de_list(keyboard_json, bot)

        assert inline_keyboard_buttons == [keyboard_button, keyboard_button]

    def test_to_json(self, keyboard_button):
        json.loads(keyboard_button.to_json())

    def test_to_dict(self, keyboard_button):
        keyboard_button_dict = keyboard_button.to_dict()

        assert isinstance(keyboard_button_dict, dict)
        assert keyboard_button_dict['text'] == keyboard_button.text
        assert keyboard_button_dict['request_location'] == keyboard_button.request_location
        assert keyboard_button_dict['request_contact'] == keyboard_button.request_contact
