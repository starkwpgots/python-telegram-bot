#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=E0611,E0213,E1102,C0103,E1101,W0613,R0913,R0904
#
# A library that provides a Python interface to the Telegram Bot API
# Copyright (C) 2015-2017
# Leandro Toledo de Souza <devs@python-telegram-bot.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser Public License for more details.
#
# You should have received a copy of the GNU Lesser Public License
# along with this program.  If not, see [http://www.gnu.org/licenses/].
"""This module contains an object that represents a Telegram Bot."""

import functools
import logging
import warnings
from datetime import datetime

from telegram import (User, Message, Update, Chat, ChatMember, UserProfilePhotos, File,
                      ReplyMarkup, TelegramObject, WebhookInfo, GameHighScore)
from telegram.error import InvalidToken, TelegramError
from telegram.utils.helpers import to_timestamp
from telegram.utils.request import Request

logging.getLogger(__name__).addHandler(logging.NullHandler())


def info(func):
    @functools.wraps(func)
    def decorator(self, *args, **kwargs):
        if not self.bot:
            self.get_me()

        result = func(self, *args, **kwargs)
        return result

    return decorator


def log(func):
    logger = logging.getLogger(func.__module__)

    @functools.wraps(func)
    def decorator(self, *args, **kwargs):
        logger.debug('Entering: %s', func.__name__)
        result = func(self, *args, **kwargs)
        logger.debug(result)
        logger.debug('Exiting: %s', func.__name__)
        return result

    return decorator


def message(func):
    @functools.wraps(func)
    def decorator(self, *args, **kwargs):
        url, data = func(self, *args, **kwargs)
        return self._message_wrapper(url, data, *args, **kwargs)

    return decorator


class Bot(TelegramObject):
    """This object represents a Telegram Bot.

    Properties:
        id (int): Unique identifier for this bot.
        first_name (str): Bot's first name.
        last_name (str): Optional. Bot's last name.
        username (str): Bot's username.
        name (str): Bot's @username.

    Args:
        token (str): Bot's unique authentication.
        base_url (Optional[str]): Telegram Bot API service URL.
        base_file_url (Optional[str]): Telegram Bot API file URL.
        request (Optional[Request]): Pre initialized :class:`telegram.utils.Request`.

    """

    def __init__(self, token, base_url=None, base_file_url=None, request=None):
        self.token = self._validate_token(token)

        if base_url is None:
            base_url = 'https://api.telegram.org/bot'

        if base_file_url is None:
            base_file_url = 'https://api.telegram.org/file/bot'

        self.base_url = str(base_url) + str(self.token)
        self.base_file_url = str(base_file_url) + str(self.token)
        self.bot = None
        self._request = request or Request()
        self.logger = logging.getLogger(__name__)

    @property
    def request(self):
        return self._request

    @staticmethod
    def _validate_token(token):
        """a very basic validation on token"""
        if any(x.isspace() for x in token):
            raise InvalidToken()

        left, sep, _right = token.partition(':')
        if (not sep) or (not left.isdigit()) or (len(left) < 3):
            raise InvalidToken()

        return token

    @property
    @info
    def id(self):
        return self.bot.id

    @property
    @info
    def first_name(self):
        return self.bot.first_name

    @property
    @info
    def last_name(self):
        return self.bot.last_name

    @property
    @info
    def username(self):
        return self.bot.username

    @property
    def name(self):
        return '@{0}'.format(self.username)

    def _message_wrapper(self, url, data, *args, **kwargs):
        if kwargs.get('reply_to_message_id'):
            data['reply_to_message_id'] = kwargs.get('reply_to_message_id')

        if kwargs.get('disable_notification'):
            data['disable_notification'] = kwargs.get('disable_notification')

        if kwargs.get('reply_markup'):
            reply_markup = kwargs.get('reply_markup')
            if isinstance(reply_markup, ReplyMarkup):
                data['reply_markup'] = reply_markup.to_json()
            else:
                data['reply_markup'] = reply_markup

        result = self._request.post(url, data, timeout=kwargs.get('timeout'))

        if result is True:
            return result

        return Message.de_json(result, self)

    @log
    def get_me(self, timeout=None, **kwargs):
        """
        A simple method for testing your bot's auth token. Requires no parameters.

        Args:
            timeout (Optional[int|float]): If this value is specified, use it as the read timeout
                from the server (instead of the one specified during creation of the connection
                pool).

        Returns:
            :class:`telegram.User`: A :class:`telegram.User` instance representing that bot if the
                credentials are valid, `None` otherwise.

        Raises:
            :class:`telegram.TelegramError`
        """

        url = '{0}/getMe'.format(self.base_url)

        result = self._request.get(url, timeout=timeout)

        self.bot = User.de_json(result, self)

        return self.bot

    @log
    @message
    def send_message(self,
                     chat_id,
                     text,
                     parse_mode=None,
                     disable_web_page_preview=None,
                     disable_notification=False,
                     reply_to_message_id=None,
                     reply_markup=None,
                     timeout=None,
                     **kwargs):
        """
        Use this method to send text messages.

        Args:
            chat_id (int|str): Unique identifier for the target chat or
                    username of the target channel (in the format
                    @channelusername).
            text (str): Text of the message to be sent. Max 4096 characters. Also found as
                    ``telegram.constants.MAX_MESSAGE_LENGTH``.
            parse_mode (Optional[str]): Send Markdown or HTML, if you want
                    Telegram apps to show bold, italic, fixed-width text or inline
                    URLs in your bot's message.
            disable_web_page_preview (Optional[bool]): Disables link previews
                    for links in this message.
            disable_notification (Optional[bool]): Sends the message silently. Users will
                    receive a notification with no sound.
            reply_to_message_id (Optional[int]): If the message is a reply,
                    ID of the original message.
            reply_markup (Optional[:class:`telegram.ReplyMarkup`]): Additional
                    interface options. A JSON-serialized object for an inline
                    keyboard, custom reply keyboard, instructions to remove reply
                    keyboard or to force a reply from the user.
            timeout (Optional[int|float]): If this value is specified, use it as the read timeout
                    from the server (instead of the one specified during creation of the connection
                    pool).
            **kwargs (dict): Arbitrary keyword arguments.

        Returns:
            :class:`telegram.Message`: On success, the sent message is returned.

        Raises:
            :class:`telegram.TelegramError`
        """

        url = '{0}/sendMessage'.format(self.base_url)

        data = {'chat_id': chat_id, 'text': text}

        if parse_mode:
            data['parse_mode'] = parse_mode
        if disable_web_page_preview:
            data['disable_web_page_preview'] = disable_web_page_preview

        return url, data

    @log
    def delete_message(self, chat_id, message_id, timeout=None, **kwargs):
        """
        Use this method to delete a message. A message can only be deleted if it was sent less
        than 48 hours ago. Any such recently sent outgoing message may be deleted. Additionally,
        if the bot is an administrator in a group chat, it can delete any message. If the bot is
        an administrator in a supergroup, it can delete messages from any other user and service
        messages about people joining or leaving the group (other types of service messages may
        only be removed by the group creator). In channels, bots can only remove their own
        messages.

        Args:
            chat_id (int|str): Unique identifier for the target chat or
                    username of the target channel (in the format
                    @channelusername).
            message_id (int): Identifier of the message to delete
            timeout (Optional[int|float]): If this value is specified, use it as the read timeout
                    from the server (instead of the one specified during creation of the connection
                    pool).
            **kwargs (dict): Arbitrary keyword arguments.

        Returns:
            bool: On success, `True` is returned.

        Raises:
            :class:`telegram.TelegramError`
        """

        url = '{0}/deleteMessage'.format(self.base_url)

        data = {'chat_id': chat_id, 'message_id': message_id}

        result = self._request.post(url, data, timeout=timeout)

        return result

    @log
    @message
    def forward_message(self,
                        chat_id,
                        from_chat_id,
                        message_id,
                        disable_notification=False,
                        timeout=None,
                        **kwargs):
        """
        Use this method to forward messages of any kind.

        Args:
            chat_id (int|str): Unique identifier for the target chat or username of the target
                    channel (in the format @channelusername).
            from_chat_id (int|str): Unique identifier for the chat where the original message was
                    sent (or channel username in the format @channelusername).
            disable_notification (Optional[bool]): Sends the message silently. Users will receive
                    a notification with no sound.
            message_id (int): Message identifier in the chat specified in from_chat_id.
            timeout (Optional[int|float]): If this value is specified, use it as the read timeout
                    from the server (instead of the one specified during creation of the connection
                    pool).
            **kwargs (dict): Arbitrary keyword arguments.

        Returns:
            :class:`telegram.Message`: On success, the sent Message is returned.

        Raises:
            :class:`telegram.TelegramError`
        """

        url = '{0}/forwardMessage'.format(self.base_url)

        data = {}

        if chat_id:
            data['chat_id'] = chat_id
        if from_chat_id:
            data['from_chat_id'] = from_chat_id
        if message_id:
            data['message_id'] = message_id

        return url, data

    @log
    @message
    def send_photo(self,
                   chat_id,
                   photo,
                   caption=None,
                   disable_notification=False,
                   reply_to_message_id=None,
                   reply_markup=None,
                   timeout=20.,
                   **kwargs):
        """
        Use this method to send photos.

        Note:
            The video argument can be either a file_id, an URL or a file from disk
            ``open(filename, 'rb')``

        Args:
            chat_id (int|str): Unique identifier for the target chat or username of the target
                    channel (in the format @channelusername).
            photo (str|filelike object): Photo to send. Pass a file_id as String to send a photo
                    that exists on the Telegram servers (recommended), pass an HTTP URL as a String
                    for Telegram to get a photo from the Internet, or upload a new photo using
                    multipart/form-data.
            caption (Optional[str]): Photo caption (may also be used when resending photos by
                    file_id), 0-200 characters
            disable_notification (Optional[bool]): Sends the message silently. Users will receive
                    a notification with no sound.
            reply_to_message_id (Optional[int]): If the message is a reply, ID of the
                    original message.
            reply_markup (Optional[:class:`telegram.ReplyMarkup`]): Additional interface options. A
                    JSON-serialized object for an inline keyboard, custom reply keyboard,
                    instructions to remove reply keyboard or to force a reply from the user.
            timeout (Optional[int|float]): Send file timeout (default: 20 seconds).
            **kwargs (dict): Arbitrary keyword arguments.

        Returns:
            :class:`telegram.Message`: On success, the sent Message is returned.

        Raises:
            :class:`telegram.TelegramError`
        """

        url = '{0}/sendPhoto'.format(self.base_url)

        data = {'chat_id': chat_id, 'photo': photo}

        if caption:
            data['caption'] = caption

        return url, data

    @log
    @message
    def send_audio(self,
                   chat_id,
                   audio,
                   duration=None,
                   performer=None,
                   title=None,
                   caption=None,
                   disable_notification=False,
                   reply_to_message_id=None,
                   reply_markup=None,
                   timeout=20.,
                   **kwargs):
        """
        Use this method to send audio files, if you want Telegram clients to display them in the
        music player. Your audio must be in the .mp3 format. On success, the sent Message is
        returned. Bots can currently send audio files of up to 50 MB in size, this limit may be
        changed in the future.

        For sending voice messages, use the sendVoice method instead.

        Note:
            The audio argument can be either a file_id, an URL or a file from disk
            ``open(filename, 'rb')``

        Args:
            chat_id (int|str): Unique identifier for the target chat or username of the target
                    channel (in the format @channelusername).
            audio (str|filelike object): Audio file to send. Pass a file_id as String to send an
                    audio file that exists on the Telegram servers (recommended), pass an HTTP URL
                    as a String for Telegram to get an audio file from the Internet, or upload a
                    new one using multipart/form-data.
            caption (Optional[str]): Audio caption, 0-200 characters.
            duration (Optional[int]): Duration of sent audio in seconds.
            performer (Optional[str]): Performer.
            title (Optional[str]): Track name.
            disable_notification (Optional[bool]): Sends the message silently. Users will receive
                    a notification with no sound.
            reply_to_message_id (Optional[int]): If the message is a reply, ID of the
                    original message.
            reply_markup (Optional[:class:`telegram.ReplyMarkup`]): Additional interface options. A
                    JSON-serialized object for an inline keyboard, custom reply keyboard,
                    instructions to remove reply keyboard or to force a reply from the user.
            timeout (Optional[int|float]): Send file timeout (default: 20 seconds).
            **kwargs (dict): Arbitrary keyword arguments.

        Returns:
            :class:`telegram.Message`: On success, the sent Message is returned.

        Raises:
            :class:`telegram.TelegramError`
        """

        url = '{0}/sendAudio'.format(self.base_url)

        data = {'chat_id': chat_id, 'audio': audio}

        if duration:
            data['duration'] = duration
        if performer:
            data['performer'] = performer
        if title:
            data['title'] = title
        if caption:
            data['caption'] = caption

        return url, data

    @log
    @message
    def send_document(self,
                      chat_id,
                      document,
                      filename=None,
                      caption=None,
                      disable_notification=False,
                      reply_to_message_id=None,
                      reply_markup=None,
                      timeout=20.,
                      **kwargs):
        """
        Use this method to send general files.

        Note:
            The document argument can be either a file_id, an URL or a file from disk
            ``open(filename, 'rb')``

        Args:
            chat_id (int|str): Unique identifier for the target chat or username of the target
                    channel (in the format @channelusername).
            document (str|filelike object): File to send. Pass a file_id as String to send a
                    file that exists on the Telegram servers (recommended), pass an HTTP URL
                    as a String for Telegram to get a file from the Internet, or upload a
                    new one using multipart/form-data.
            filename (Optional[str]): File name that shows in telegram message (it is useful when
                    you send file generated by temp module, for example). Undocumented.
            caption (Optional[str]): Document caption (may also be used when resending documents
                    by file_id), 0-200 characters
            disable_notification (Optional[bool]): Sends the message silently. Users will receive
                    a notification with no sound.
            reply_to_message_id (Optional[int]): If the message is a reply, ID of the
                    original message.
            reply_markup (Optional[:class:`telegram.ReplyMarkup`]): Additional interface options. A
                    JSON-serialized object for an inline keyboard, custom reply keyboard,
                    instructions to remove reply keyboard or to force a reply from the user.
            timeout (Optional[int|float]): Send file timeout (default: 20 seconds).
            **kwargs (dict): Arbitrary keyword arguments.

        Returns:
            :class:`telegram.Message`: On success, the sent Message is returned.

        Raises:
            :class:`telegram.TelegramError`
        """

        url = '{0}/sendDocument'.format(self.base_url)

        data = {'chat_id': chat_id, 'document': document}

        if filename:
            data['filename'] = filename
        if caption:
            data['caption'] = caption

        return url, data

    @log
    @message
    def send_sticker(self,
                     chat_id,
                     sticker,
                     disable_notification=False,
                     reply_to_message_id=None,
                     reply_markup=None,
                     timeout=None,
                     **kwargs):
        """
        Use this method to send .webp stickers.

        Note:
            The sticker argument can be either a file_id, an URL or a file from disk
            ``open(filename, 'rb')``

        Args:
            chat_id (int|str): Unique identifier for the target chat or username of the target
                    channel (in the format @channelusername).
            sticker (str|filelike object): Sticker to send. Pass a file_id as String to send a file
                    that exists on the Telegram servers (recommended), pass an HTTP URL as a String
                    for Telegram to get a .webp file from the Internet, or upload a new one using
                    multipart/form-data.
            disable_notification (Optional[bool]): Sends the message silently. Users will receive
                    a notification with no sound.
            reply_to_message_id (Optional[int]): If the message is a reply, ID of the
                    original message.
            reply_markup (Optional[:class:`telegram.ReplyMarkup`]): Additional interface options. A
                    JSON-serialized object for an inline keyboard, custom reply keyboard,
                    instructions to remove reply keyboard or to force a reply from the user.
            timeout (Optional[int|float]): Send file timeout (default: 20 seconds).
            **kwargs (dict): Arbitrary keyword arguments.

        Returns:
            :class:`telegram.Message`: On success, the sent Message is returned.

        Raises:
            :class:`telegram.TelegramError`
        """

        url = '{0}/sendSticker'.format(self.base_url)

        data = {'chat_id': chat_id, 'sticker': sticker}

        return url, data

    @log
    @message
    def send_video(self,
                   chat_id,
                   video,
                   duration=None,
                   caption=None,
                   disable_notification=False,
                   reply_to_message_id=None,
                   reply_markup=None,
                   timeout=20.,
                   width=None,
                   height=None,
                   **kwargs):
        """
        Use this method to send video files, Telegram clients support mp4 videos
        (other formats may be sent as Document).

        Note:
            The video argument can be either a file_id, an URL or a file from disk
            ``open(filename, 'rb')``

        Args:
            chat_id (int|str): Unique identifier for the target chat or username of the target
                    channel (in the format @channelusername).
            video (str|filelike object): Video file to send. Pass a file_id as String to send an
                    video file that exists on the Telegram servers (recommended), pass an HTTP URL
                    as a String for Telegram to get an video file from the Internet, or upload a
                    new one using multipart/form-data.
            duration (Optional[int]): Duration of sent video in seconds.
            width (Optional[int)): Video width.
            height (Optional[int]): Video height.
            caption (Optional[str]): Video caption (may also be used when resending videos by
                    file_id), 0-200 characters.
            disable_notification (Optional[bool]): Sends the message silently. Users will receive
                    a notification with no sound.
            reply_to_message_id (Optional[int]): If the message is a reply, ID of the
                    original message.
            reply_markup (Optional[:class:`telegram.ReplyMarkup`]): Additional interface options. A
                    JSON-serialized object for an inline keyboard, custom reply keyboard,
                    instructions to remove reply keyboard or to force a reply from the user.
            timeout (Optional[int|float]): Send file timeout (default: 20 seconds).
            **kwargs (dict): Arbitrary keyword arguments.

        Returns:
            :class:`telegram.Message`: On success, the sent Message is returned.

        Raises:
            :class:`telegram.TelegramError`
        """

        url = '{0}/sendVideo'.format(self.base_url)

        data = {'chat_id': chat_id, 'video': video}

        if duration:
            data['duration'] = duration
        if caption:
            data['caption'] = caption
        if width:
            data['width'] = width
        if height:
            data['height'] = height

        return url, data

    @log
    @message
    def send_voice(self,
                   chat_id,
                   voice,
                   duration=None,
                   caption=None,
                   disable_notification=False,
                   reply_to_message_id=None,
                   reply_markup=None,
                   timeout=20.,
                   **kwargs):
        """
        Use this method to send audio files, if you want Telegram clients to display the file
        as a playable voice message. For this to work, your audio must be in an .ogg file
        encoded with OPUS (other formats may be sent as Audio or Document).

        Note:
            The voice argument can be either a file_id, an URL or a file from disk
            ``open(filename, 'rb')``

        Args:
            chat_id (int|str): Unique identifier for the target chat or username of the target
                    channel (in the format @channelusername).
            voice (str|filelike object): Voice file to send. Pass a file_id as String to send an
                    voice file that exists on the Telegram servers (recommended), pass an HTTP URL
                    as a String for Telegram to get an voice file from the Internet, or upload a
                    new one using multipart/form-data.
            caption (Optional[str]): Voice message caption, 0-200 characters.
            duration (Optional[int]): Duration of the voice message in seconds.
            disable_notification (Optional[bool]): Sends the message silently. Users will receive
                    a notification with no sound.
            reply_to_message_id (Optional[int]): If the message is a reply, ID of the
                    original message.
            reply_markup (Optional[:class:`telegram.ReplyMarkup`]): Additional interface options. A
                    JSON-serialized object for an inline keyboard, custom reply keyboard,
                    instructions to remove reply keyboard or to force a reply from the user.
            timeout (Optional[int|float]): Send file timeout (default: 20 seconds).
            **kwargs (dict): Arbitrary keyword arguments.

        Returns:
            :class:`telegram.Message`: On success, the sent Message is returned.

        Raises:
            :class:`telegram.TelegramError`
        """

        url = '{0}/sendVoice'.format(self.base_url)

        data = {'chat_id': chat_id, 'voice': voice}

        if duration:
            data['duration'] = duration
        if caption:
            data['caption'] = caption

        return url, data

    @log
    @message
    def send_video_note(self,
                        chat_id,
                        video_note,
                        duration=None,
                        length=None,
                        disable_notification=False,
                        reply_to_message_id=None,
                        reply_markup=None,
                        timeout=20.,
                        **kwargs):
        """
        As of v.4.0, Telegram clients support rounded square mp4 videos of up to 1 minute long.
        Use this method to send video messages.

        Note:
            The video_note argument can be either a file_id or a file from disk
            ``open(filename, 'rb')``

        Args:
            chat_id (int|str): Unique identifier for the target chat or username of the target
                    channel (in the format @channelusername).
            video_note (str|filelike object): Video note to send. Pass a file_id as String to send
                    a video note that exists on the Telegram servers (recommended) or upload a new
                    video using multipart/form-data.
                    Sending video notes by a URL is currently unsupported.
            duration (Optional[int]): Duration of sent video in seconds
            length (Optional[int]): Video width and height
            disable_notification (Optional[bool]): Sends the message silently. Users will receive
                    a notification with no sound.
            reply_to_message_id (Optional[int]): If the message is a reply, ID of the
                    original message.
            reply_markup (Optional[:class:`telegram.ReplyMarkup`]): Additional interface options. A
                    JSON-serialized object for an inline keyboard, custom reply keyboard,
                    instructions to remove reply keyboard or to force a reply from the user.
            timeout (Optional[int|float]): Send file timeout (default: 20 seconds).
            **kwargs (dict): Arbitrary keyword arguments.

        Returns:
            :class:`telegram.Message`: On success, the sent Message is returned.

        Raises:
            :class:`telegram.TelegramError`
        """

        url = '{0}/sendVideoNote'.format(self.base_url)

        data = {'chat_id': chat_id, 'video_note': video_note}

        if duration is not None:
            data['duration'] = duration
        if length is not None:
            data['length'] = length

        return url, data

    @log
    @message
    def send_location(self,
                      chat_id,
                      latitude,
                      longitude,
                      disable_notification=False,
                      reply_to_message_id=None,
                      reply_markup=None,
                      timeout=None,
                      **kwargs):
        """
        Use this method to send point on the map.

        Args:
            chat_id (int|str): Unique identifier for the target chat or username of the target
                    channel (in the format @channelusername).
            latitude (float): Latitude of location.
            longitude (float): Longitude of location.
            disable_notification (Optional[bool]): Sends the message silently. Users will receive
                    a notification with no sound.
            reply_to_message_id (Optional[int]): If the message is a reply, ID of the
                    original message.
            reply_markup (Optional[:class:`telegram.ReplyMarkup`]): Additional interface options. A
                    JSON-serialized object for an inline keyboard, custom reply keyboard,
                    instructions to remove reply keyboard or to force a reply from the user.
            timeout (Optional[int|float]): If this value is specified, use it as the read timeout
                    from the server (instead of the one specified during creation of the connection
                    pool).
            **kwargs (dict): Arbitrary keyword arguments.

        Returns:
            :class:`telegram.Message`: On success, the sent Message is returned.

        Raises:
            :class:`telegram.TelegramError`
        """

        url = '{0}/sendLocation'.format(self.base_url)

        data = {'chat_id': chat_id, 'latitude': latitude, 'longitude': longitude}

        return url, data

    @log
    @message
    def send_venue(self,
                   chat_id,
                   latitude,
                   longitude,
                   title,
                   address,
                   foursquare_id=None,
                   disable_notification=False,
                   reply_to_message_id=None,
                   reply_markup=None,
                   timeout=None,
                   **kwargs):
        """
        Use this method to send information about a venue.

        Args:
            chat_id (int|str): Unique identifier for the target chat or username of the target
                    channel (in the format @channelusername).
            latitude (float): Latitude of venue.
            longitude (float): Longitude of venue.
            title (str): Name of the venue.
            address (str): Address of the venue.
            foursquare_id (Optional[str]): Foursquare identifier of the venue.
            disable_notification (Optional[bool]): Sends the message silently. Users will receive
                    a notification with no sound.
            reply_to_message_id (Optional[int]): If the message is a reply, ID of the
                    original message.
            reply_markup (Optional[:class:`telegram.ReplyMarkup`]): Additional interface options. A
                    JSON-serialized object for an inline keyboard, custom reply keyboard,
                    instructions to remove reply keyboard or to force a reply from the user.
            timeout (Optional[int|float]): If this value is specified, use it as the read timeout
                    from the server (instead of the one specified during creation of the connection
                    pool).
            **kwargs (dict): Arbitrary keyword arguments.

        Returns:
            :class:`telegram.Message`: On success, the sent Message is returned.

        Raises:
            :class:`telegram.TelegramError`
        """

        url = '{0}/sendVenue'.format(self.base_url)

        data = {
            'chat_id': chat_id,
            'latitude': latitude,
            'longitude': longitude,
            'address': address,
            'title': title
        }

        if foursquare_id:
            data['foursquare_id'] = foursquare_id

        return url, data

    @log
    @message
    def send_contact(self,
                     chat_id,
                     phone_number,
                     first_name,
                     last_name=None,
                     disable_notification=False,
                     reply_to_message_id=None,
                     reply_markup=None,
                     timeout=None,
                     **kwargs):
        """
        Use this method to send phone contacts.

        Args:
            chat_id (int|str): Unique identifier for the target chat or username of the target
                    channel (in the format @channelusername).
            phone_number (str): Contact's phone number.
            first_name (str): Contact's first name.
            last_name (Optional[str]): Contact's last name.
            disable_notification (Optional[bool]): Sends the message silently. Users will receive
                    a notification with no sound.
            reply_to_message_id (Optional[int]): If the message is a reply, ID of the
                    original message.
            reply_markup (Optional[:class:`telegram.ReplyMarkup`]): Additional interface options. A
                    JSON-serialized object for an inline keyboard, custom reply keyboard,
                    instructions to remove reply keyboard or to force a reply from the user.
            timeout (Optional[int|float]): If this value is specified, use it as the read timeout
                    from the server (instead of the one specified during creation of the connection
                    pool).
            **kwargs (dict): Arbitrary keyword arguments.

        Returns:
            :class:`telegram.Message`: On success, the sent Message is returned.

        Raises:
            :class:`telegram.TelegramError`
        """

        url = '{0}/sendContact'.format(self.base_url)

        data = {'chat_id': chat_id, 'phone_number': phone_number, 'first_name': first_name}

        if last_name:
            data['last_name'] = last_name

        return url, data

    @log
    @message
    def send_game(self,
                  chat_id,
                  game_short_name,
                  disable_notification=False,
                  reply_to_message_id=None,
                  reply_markup=None,
                  timeout=None,
                  **kwargs):
        """
        Use this method to send a game.

        Args:
            chat_id (int|str): Unique identifier for the target chat or username of the target
                    channel (in the format @channelusername).
            game_short_name (str): Short name of the game, serves as the unique identifier for the
                    game. Set up your games via Botfather.
            disable_notification (Optional[bool]): Sends the message silently. Users will receive
                    a notification with no sound.
            reply_to_message_id (Optional[int]): If the message is a reply, ID of the
                    original message.
            reply_markup (Optional[:class:`telegram.ReplyMarkup`]): Additional interface options. A
                    JSON-serialized object for an inline keyboard, custom reply keyboard,
                    instructions to remove reply keyboard or to force a reply from the user.
            timeout (Optional[int|float]): If this value is specified, use it as the read timeout
                    from the server (instead of the one specified during creation of the connection
                    pool).
            **kwargs (dict): Arbitrary keyword arguments.

        Returns:
            :class:`telegram.Message`: On success, the sent Message is returned.

        Raises:
            :class:`telegram.TelegramError`
        """

        url = '{0}/sendGame'.format(self.base_url)

        data = {'chat_id': chat_id, 'game_short_name': game_short_name}

        return url, data

    @log
    def send_chat_action(self, chat_id, action, timeout=None, **kwargs):
        """
        Use this method when you need to tell the user that something is happening on the bot's
        side. The status is set for 5 seconds or less (when a message arrives from your bot,
        Telegram clients clear its typing status).

        Args:
            chat_id (int|str): Unique identifier for the target chat or username of the target
                    channel (in the format @channelusername).
            action(:class:`telegram.ChatAction`|str): Type of action to broadcast. Choose one,
                    depending on what the user is about to receive:

                    - typing for text messages
                    - upload_photo for photos
                    - record_video or upload_video for videos
                    - record_audio or upload_audio for audio files
                    - upload_document for general files
                    - find_location for location data
                    - record_video_note or upload_video_note for video notes

            timeout (Optional[int|float]): If this value is specified, use it as the read timeout
                    from the server (instead of the one specified during creation of the connection
                    pool).
            **kwargs (dict): Arbitrary keyword arguments.

        Returns:
            bool: True on success.

        Raises:
            :class:`telegram.TelegramError`
        """

        url = '{0}/sendChatAction'.format(self.base_url)

        data = {'chat_id': chat_id, 'action': action}

        result = self._request.post(url, data, timeout=timeout)

        return result

    @log
    def answer_inline_query(self,
                            inline_query_id,
                            results,
                            cache_time=300,
                            is_personal=None,
                            next_offset=None,
                            switch_pm_text=None,
                            switch_pm_parameter=None,
                            timeout=None,
                            **kwargs):
        """
        Use this method to send answers to an inline query. On success, True is returned. No more
        than 50 results per query are allowed.

        Args:
            inline_query_id (str): Unique identifier for the answered query.
            results (list(:class:`telegram.InlineQueryResult`)): A list of results for the inline
                    query.
            cache_time (Optional[int]): The maximum amount of time in seconds that the result of
                    the inline query may be cached on the server. Defaults to 300.
            is_personal (Optional[bool]): Pass True, if results may be cached on the server side
                    only for the user that sent the query. By default, results may be returned to
                    any user who sends the same query.
            next_offset (Optional[str]): Pass the offset that a client should send in the next
                    query with the same text to receive more results. Pass an empty string if there
                    are no more results or if you don't support pagination. Offset length can't
                    exceed 64 bytes.
            switch_pm_text (Optional[str]): If passed, clients will display a button with specified
                    text that switches the user to a private chat with the bot and sends the bot
                    a start message with the parameter switch_pm_parameter.
            switch_pm_parameter (Optional[str]): Deep-linking parameter for the /start message sent
                    to the bot when user presses the switch button. 1-64 characters,
                    only A-Z, a-z, 0-9, _ and - are allowed.
            timeout (Optional[int|float]): If this value is specified, use it as the read timeout
                    from the server (instead of the one specified during creation of the connection
                    pool).
            **kwargs (dict): Arbitrary keyword arguments.

        Example:
            An inline bot that sends YouTube videos can ask the user to connect the bot to their
            YouTube account to adapt search results accordingly. To do this, it displays a
            'Connect your YouTube account' button above the results, or even before showing any.
            The user presses the button, switches to a private chat with the bot and, in doing so,
            passes a start parameter that instructs the bot to return an oauth link. Once done, the
            bot can offer a switch_inline button so that the user can easily return to the chat
            where they wanted to use the bot's inline capabilities.

        Returns:
            bool: On success, `True` is returned.

        Raises:
            :class:`telegram.TelegramError`
        """

        url = '{0}/answerInlineQuery'.format(self.base_url)

        results = [res.to_dict() for res in results]

        data = {'inline_query_id': inline_query_id, 'results': results}

        if cache_time or cache_time == 0:
            data['cache_time'] = cache_time
        if is_personal:
            data['is_personal'] = is_personal
        if next_offset is not None:
            data['next_offset'] = next_offset
        if switch_pm_text:
            data['switch_pm_text'] = switch_pm_text
        if switch_pm_parameter:
            data['switch_pm_parameter'] = switch_pm_parameter

        result = self._request.post(url, data, timeout=timeout)

        return result

    @log
    def get_user_profile_photos(self, user_id, offset=None, limit=100, timeout=None, **kwargs):
        """
        Use this method to get a list of profile pictures for a user.

        Args:
            user_id (int): Unique identifier of the target user.
            offset (Optional[int]): Sequential number of the first photo to be returned.
                    By default, all photos are returned.
            limit (Optional[int]): Limits the number of photos to be retrieved. Values between
                    1-100 are accepted. Defaults to 100.
            timeout (Optional[int|float]): If this value is specified, use it as the read timeout
                    from the server (instead of the one specified during creation of the connection
                    pool).
            **kwargs (dict): Arbitrary keyword arguments.

        Returns:
            :class:`telegram.UserProfilePhotos`

        Raises:
            :class:`telegram.TelegramError`
        """

        url = '{0}/getUserProfilePhotos'.format(self.base_url)

        data = {'user_id': user_id}

        if offset:
            data['offset'] = offset
        if limit:
            data['limit'] = limit

        result = self._request.post(url, data, timeout=timeout)

        return UserProfilePhotos.de_json(result, self)

    @log
    def get_file(self, file_id, timeout=None, **kwargs):
        """
        Use this method to get basic info about a file and prepare it for downloading. For the
        moment, bots can download files of up to 20MB in size. The file can then be downloaded
        with :attr:`telegram.File.download`. It is guaranteed that the link will be
        valid for at least 1 hour. When the link expires, a new one can be requested by
        calling getFile again.

        Args:
            file_id (str): File identifier to get info about.
            timeout (Optional[int|float]): If this value is specified, use it as the read timeout
                    from the server (instead of the one specified during creation of the connection
                    pool).
            **kwargs (dict): Arbitrary keyword arguments.

        Returns:
            :class:`telegram.File`

        Raises:
            :class:`telegram.TelegramError`
        """

        url = '{0}/getFile'.format(self.base_url)

        data = {'file_id': file_id}

        result = self._request.post(url, data, timeout=timeout)

        if result.get('file_path'):
            result['file_path'] = '%s/%s' % (self.base_file_url, result['file_path'])

        return File.de_json(result, self)

    @log
    def kick_chat_member(self, chat_id, user_id, timeout=None, until_date=None, **kwargs):
        """
        Use this method to kick a user from a group or a supergroup. In the case of supergroups,
        the user will not be able to return to the group on their own using invite links, etc.,
        unless unbanned first. The bot must be an administrator in the group for this to work.

        Args:
            chat_id (int|str): Unique identifier for the target chat or username of the target
                    channel (in the format @channelusername).
            user_id (int|str): Unique identifier of the target user.
            timeout (Optional[int|float]): If this value is specified, use it as the read timeout
                from the server (instead of the one specified during creation of the connection
                pool).
            until_date (Optional[int|datetime]): Date when the user will be unbanned,
                unix time. If user is banned for more than 366 days or less than 30 seconds from
                the current time they are considered to be banned forever
            **kwargs (dict): Arbitrary keyword arguments.

        Note:
            In regular groups (non-supergroups), this method will only work if the
            'All Members Are Admins' setting is off in the target group. Otherwise
            members may only be removed by the group's creator or by the member that added them.

        Returns:
            bool: On success, `True` is returned.

        Raises:
            :class:`telegram.TelegramError`
        """

        url = '{0}/kickChatMember'.format(self.base_url)

        data = {'chat_id': chat_id, 'user_id': user_id}

        if until_date is not None:
            if isinstance(until_date, datetime):
                until_date = to_timestamp(until_date)
            data['until_date'] = until_date

        result = self._request.post(url, data, timeout=timeout)

        return result

    @log
    def unban_chat_member(self, chat_id, user_id, timeout=None, **kwargs):
        """
        Use this method to unban a previously kicked user in a supergroup.
        The user will not return to the group automatically, but will be able to join via link,
        etc. The bot must be an administrator in the group for this to work.

        Args:
            chat_id (int|str): Unique identifier for the target chat or username of the target
                    channel (in the format @channelusername).
            user_id (int|str): Unique identifier of the target user.
            timeout (Optional[int|float]): If this value is specified, use it as the read timeout
                    from the server (instead of the one specified during creation of the connection
                    pool).
            **kwargs (dict): Arbitrary keyword arguments.

        Returns:
            bool: On success, `True` is returned.

        Raises:
            :class:`telegram.TelegramError`
        """

        url = '{0}/unbanChatMember'.format(self.base_url)

        data = {'chat_id': chat_id, 'user_id': user_id}

        result = self._request.post(url, data, timeout=timeout)

        return result

    @log
    def answer_callback_query(self,
                              callback_query_id,
                              text=None,
                              show_alert=False,
                              url=None,
                              cache_time=None,
                              timeout=None,
                              **kwargs):
        """
        Use this method to send answers to callback queries sent from inline keyboards. The answer
        will be displayed to the user as a notification at the top of the chat screen or as an
        alert.
        Alternatively, the user can be redirected to the specified Game URL. For this option to
        work, you must first create a game for your bot via BotFather and accept the terms.
        Otherwise, you may use links like t.me/your_bot?start=XXXX that open your bot with
        a parameter.

        Args:
            callback_query_id (str): Unique identifier for the query to be answered.
            text (Optional[str]): Text of the notification. If not specified, nothing will be
                    shown to the user, 0-200 characters.
            show_alert (Optional[bool]): If true, an alert will be shown by the client instead of
                    a notification at the top of the chat screen. Defaults to false.
            url (Optional[str]): URL that will be opened by the user's client. If you have created
                    a Game and accepted the conditions via @Botfather, specify the URL that opens
                    your game - note that this will only work if the query comes from a callback
                    game button. Otherwise, you may use links like t.me/your_bot?start=XXXX that
                    open your bot with a parameter.
            cache_time (Optional[int]): The maximum amount of time in seconds that the result of
                    the callback query may be cached client-side. Telegram apps will support
                    caching starting in version 3.14. Defaults to 0.
            timeout (Optional[int|float]): If this value is specified, use it as the read timeout
                    from the server (instead of the one specified during creation of the connection
                    pool).
            **kwargs (dict): Arbitrary keyword arguments.

        Returns:
            bool: On success, `True` is returned.

        Raises:
            :class:`telegram.TelegramError`
        """

        url_ = '{0}/answerCallbackQuery'.format(self.base_url)

        data = {'callback_query_id': callback_query_id}

        if text:
            data['text'] = text
        if show_alert:
            data['show_alert'] = show_alert
        if url:
            data['url'] = url
        if cache_time is not None:
            data['cache_time'] = cache_time

        result = self._request.post(url_, data, timeout=timeout)

        return result

    @log
    @message
    def edit_message_text(self,
                          text,
                          chat_id=None,
                          message_id=None,
                          inline_message_id=None,
                          parse_mode=None,
                          disable_web_page_preview=None,
                          reply_markup=None,
                          timeout=None,
                          **kwargs):
        """
        Use this method to edit text and game messages sent by the bot or via the bot (for inline
        bots).

        Args:
            chat_id (int|str): Unique identifier for the target chat or username of the target
                    channel (in the format @channelusername).
            message_id (Optional[int]): Required if inline_message_id is not specified. Identifier
                    of the sent message.
            inline_message_id (Optional[str]): Required if chat_id and message_id are not
                    specified. Identifier of the inline message.
            text (str): New text of the message.
            parse_mode (:class:`telegram.ParseMode`|str): Send Markdown or HTML, if you want
                    Telegram apps to show bold, italic, fixed-width text or inline URLs in
                    your bot's message.
            disable_notification (Optional[bool]): Sends the message silently. Users will receive
                    a notification with no sound.
            reply_markup (Optional[:class:`telegram.ReplyMarkup`]): Additional interface options. A
                    JSON-serialized object for an inline keyboard, custom reply keyboard,
                    instructions to remove reply keyboard or to force a reply from the user.
            timeout (Optional[int|float]): If this value is specified, use it as the read timeout
                    from the server (instead of the one specified during creation of the connection
                    pool).
            **kwargs (dict): Arbitrary keyword arguments.

        Returns:
            :class:`telegram.Message`|bool: On success, if edited message is sent by the bot, the
            editedMessage is returned, otherwise True is returned.

        Raises:
            :class:`telegram.TelegramError`
        """

        url = '{0}/editMessageText'.format(self.base_url)

        data = {'text': text}

        if chat_id:
            data['chat_id'] = chat_id
        if message_id:
            data['message_id'] = message_id
        if inline_message_id:
            data['inline_message_id'] = inline_message_id
        if parse_mode:
            data['parse_mode'] = parse_mode
        if disable_web_page_preview:
            data['disable_web_page_preview'] = disable_web_page_preview

        return url, data

    @log
    @message
    def edit_message_caption(self,
                             chat_id=None,
                             message_id=None,
                             inline_message_id=None,
                             caption=None,
                             reply_markup=None,
                             timeout=None,
                             **kwargs):
        """
        Use this method to edit captions of messages sent by the bot or via the bot
        (for inline bots).

        Args:
            chat_id (int|str): Unique identifier for the target chat or username of the target
                    channel (in the format @channelusername).
            message_id (Optional[int]): Required if inline_message_id is not specified. Identifier
                    of the sent message.
            inline_message_id (Optional[str]): Required if chat_id and message_id are not
                    specified. Identifier of the inline message.
            caption (Optional[str]): New caption of the message.
            reply_markup (Optional[:class:`telegram.ReplyMarkup`]): Additional interface options. A
                    JSON-serialized object for an inline keyboard, custom reply keyboard,
                    instructions to remove reply keyboard or to force a reply from the user.
            timeout (Optional[int|float]): If this value is specified, use it as the read timeout
                    from the server (instead of the one specified during creation of the connection
                    pool).
            **kwargs (dict): Arbitrary keyword arguments.

        Returns:
            :class:`telegram.Message`|bool: On success, if edited message is sent by the bot, the
            editedMessage is returned, otherwise True is returned.

        Raises:
            :class:`telegram.TelegramError`
        """

        if inline_message_id is None and (chat_id is None or message_id is None):
            raise TelegramError(
                'editMessageCaption: Both chat_id and message_id are required when '
                'inline_message_id is not specified')

        url = '{0}/editMessageCaption'.format(self.base_url)

        data = {}

        if caption:
            data['caption'] = caption
        if chat_id:
            data['chat_id'] = chat_id
        if message_id:
            data['message_id'] = message_id
        if inline_message_id:
            data['inline_message_id'] = inline_message_id

        return url, data

    @log
    @message
    def edit_message_reply_markup(self,
                                  chat_id=None,
                                  message_id=None,
                                  inline_message_id=None,
                                  reply_markup=None,
                                  timeout=None,
                                  **kwargs):
        """
        Use this method to edit only the reply markup of messages sent by the bot or via the bot
        (for inline bots).

        Args:
            chat_id (int|str): Unique identifier for the target chat or username of the target
                    channel (in the format @channelusername).
            message_id (Optional[int]): Required if inline_message_id is not specified. Identifier
                    of the sent message.
            inline_message_id (Optional[str]): Required if chat_id and message_id are not
                    specified. Identifier of the inline message.
            reply_markup (Optional[:class:`telegram.ReplyMarkup`]): Additional interface options. A
                    JSON-serialized object for an inline keyboard, custom reply keyboard,
                    instructions to remove reply keyboard or to force a reply from the user.
            timeout (Optional[int|float]): If this value is specified, use it as the read timeout
                    from the server (instead of the one specified during creation of the connection
                    pool).
            **kwargs (dict): Arbitrary keyword arguments.

        Returns:
            :class:`telegram.Message`|bool: On success, if edited message is sent by the bot, the
            editedMessage is returned, otherwise True is returned.

        Raises:
            :class:`telegram.TelegramError`
        """

        if inline_message_id is None and (chat_id is None or message_id is None):
            raise TelegramError(
                'editMessageCaption: Both chat_id and message_id are required when '
                'inline_message_id is not specified')

        url = '{0}/editMessageReplyMarkup'.format(self.base_url)

        data = {}

        if chat_id:
            data['chat_id'] = chat_id
        if message_id:
            data['message_id'] = message_id
        if inline_message_id:
            data['inline_message_id'] = inline_message_id

        return url, data

    @log
    def get_updates(self,
                    offset=None,
                    limit=100,
                    timeout=0,
                    network_delay=None,
                    read_latency=2.,
                    allowed_updates=None,
                    **kwargs):
        """
        Use this method to receive incoming updates using long polling.

        Args:
            offset (Optional[int]): Identifier of the first update to be returned. Must be greater
                    by one than the highest among the identifiers of previously received updates.
                    By default, updates starting with the earliest unconfirmed update are returned.
                    An update is considered confirmed as soon as getUpdates is called with an
                    offset higher than its update_id. The negative offset can be specified to
                    retrieve updates starting from -offset update from the end of the updates
                    queue. All previous updates will forgotten.
            limit (Optional[int]): Limits the number of updates to be retrieved. Values between
                    1-100 are accepted. Defaults to 100.
            timeout (Optional[int]): Timeout in seconds for long polling. Defaults to 0, i.e.
                    usual short polling. Should be positive, short polling should be used for
                    testing purposes only.
            allowed_updates (Optional[list(str)]): List the types of updates you want your bot to
                    receive. For example, specify ["message", "edited_channel_post",
                    "callback_query"] to only receive updates of these types. See
                    :class:`telegram.Update` for a complete list of available update types.
                    Specify an empty list to receive all updates regardless of type (default).
                    If not specified, the previous setting will be used. Please note that this
                    parameter doesn't affect updates created before the call to the getUpdates,
                    so unwanted updates may be received for a short period of time.
            **kwargs (dict): Arbitrary keyword arguments.

        Notes:
            1. This method will not work if an outgoing webhook is set up.
            2. In order to avoid getting duplicate updates, recalculate offset after each
               server response.

        Returns:
            list(:class:`telegram.Update`)

        Raises:
            :class:`telegram.TelegramError`
        """

        url = '{0}/getUpdates'.format(self.base_url)

        if network_delay is not None:
            warnings.warn('network_delay is deprecated, use read_latency instead')
            read_latency = network_delay

        data = {'timeout': timeout}

        if offset:
            data['offset'] = offset
        if limit:
            data['limit'] = limit
        if allowed_updates is not None:
            data['allowed_updates'] = allowed_updates

        # Ideally we'd use an aggressive read timeout for the polling. However,
        # * Short polling should return within 2 seconds.
        # * Long polling poses a different problem: the connection might have been dropped while
        #   waiting for the server to return and there's no way of knowing the connection had been
        #   dropped in real time.
        result = self._request.post(url, data, timeout=float(read_latency) + float(timeout))

        if result:
            self.logger.debug('Getting updates: %s', [u['update_id'] for u in result])
        else:
            self.logger.debug('No new updates found.')

        return [Update.de_json(u, self) for u in result]

    @log
    def set_webhook(self,
                    url=None,
                    certificate=None,
                    timeout=None,
                    max_connections=40,
                    allowed_updates=None,
                    **kwargs):
        """
        Use this method to specify a url and receive incoming updates via an outgoing webhook.
        Whenever there is an update for the bot, we will send an HTTPS POST request to the
        specified url, containing a JSON-serialized Update. In case of an unsuccessful request,
        we will give up after a reasonable amount of attempts.

        If you'd like to make sure that the Webhook request comes from Telegram, we recommend
        using a secret path in the URL, e.g. https://www.example.com/<token>. Since nobody else
        knows your bot's token, you can be pretty sure it's us.

        Args:
            url (str): HTTPS url to send updates to. Use an empty string to remove webhook
                    integration.
            certificate (file): Upload your public key certificate so that the root certificate
                    in use can be checked. See our self-signed guide for details.
            max_connections (Optional[int]): Maximum allowed number of simultaneous HTTPS
                    connections to the webhook for update delivery, 1-100. Defaults to 40. Use
                    lower values to limit the load on your bot's server, and higher values to
                    increase your bot's throughput.
            allowed_updates (Optional[list[str]]): List the types of updates you want your bot to
                    receive. For example, specify ["message", "edited_channel_post",
                    "callback_query"] to only receive updates of these types. See
                    :clas:`telegram.Update` for a complete list of available update types. Specify
                    an empty list to receive all updates regardless of type (default). If not
                    specified, the previous setting will be used. Please note that this parameter
                    doesn't affect updates created before the call to the setWebhook, so unwanted
                    updates may be received for a short period of time.
            timeout (Optional[int|float]): If this value is specified, use it as the read timeout
                    from the server (instead of the one specified during creation of the connection
                    pool).
            **kwargs (dict): Arbitrary keyword arguments.

        Note:
            1. You will not be able to receive updates using getUpdates for as long as an outgoing
               webhook is set up.
            2. To use a self-signed certificate, you need to upload your public key certificate
               using certificate parameter. Please upload as InputFile, sending a String will not
               work.
            3. Ports currently supported for Webhooks: 443, 80, 88, 8443.

        Returns:
            bool: On success, `True` is returned.

        Raises:
            :class:`telegram.TelegramError`
        """

        url_ = '{0}/setWebhook'.format(self.base_url)

        # Backwards-compatibility: 'url' used to be named 'webhook_url'
        if 'webhook_url' in kwargs:
            warnings.warn("The 'webhook_url' parameter has been renamed to 'url' in accordance "
                          "with the API")

            if url is not None:
                raise ValueError("The parameters 'url' and 'webhook_url' are mutually exclusive")

            url = kwargs['webhook_url']
            del kwargs['webhook_url']

        data = {}

        if url is not None:
            data['url'] = url
        if certificate:
            data['certificate'] = certificate
        if max_connections is not None:
            data['max_connections'] = max_connections
        if allowed_updates is not None:
            data['allowed_updates'] = allowed_updates

        result = self._request.post(url_, data, timeout=timeout)

        return result

    @log
    def delete_webhook(self, timeout=None, **kwargs):
        """
        Use this method to remove webhook integration if you decide to switch back to
        getUpdates. Requires no parameters.

        Args:
            timeout (Optional[int|float]): If this value is specified, use it as the read timeout
                    from the server (instead of the one specified during creation of the connection
                    pool).
            **kwargs (dict): Arbitrary keyword arguments.

        Returns:
            bool: On success, `True` is returned.

        Raises:
            :class:`telegram.TelegramError`
        """

        url = '{0}/deleteWebhook'.format(self.base_url)

        data = {}

        result = self._request.post(url, data, timeout=timeout)

        return result

    @log
    def leave_chat(self, chat_id, timeout=None, **kwargs):
        """
        Use this method for your bot to leave a group, supergroup or channel.

        Args:
            chat_id (int|str): Unique identifier for the target chat or username of the target
                    channel (in the format @channelusername).
            timeout (Optional[int|float]): If this value is specified, use it as the read timeout
                    from the server (instead of the one specified during creation of the connection
                    pool).
            **kwargs (dict): Arbitrary keyword arguments.

        Returns:
            bool: On success, `True` is returned.

        Raises:
            :class:`telegram.TelegramError`
        """

        url = '{0}/leaveChat'.format(self.base_url)

        data = {'chat_id': chat_id}

        result = self._request.post(url, data, timeout=timeout)

        return result

    @log
    def get_chat(self, chat_id, timeout=None, **kwargs):
        """
        Use this method to get up to date information about the chat (current name of the user for
        one-on-one conversations, current username of a user, group or channel, etc.).

        Args:
            chat_id (int|str): Unique identifier for the target chat or username of the target
                    channel (in the format @channelusername).
            timeout (Optional[int|float]): If this value is specified, use it as the read timeout
                    from the server (instead of the one specified during creation of the connection
                    pool).
            **kwargs (dict): Arbitrary keyword arguments.

        Returns:
            :class:`telegram.Chat`

        Raises:
            :class:`telegram.TelegramError`
        """

        url = '{0}/getChat'.format(self.base_url)

        data = {'chat_id': chat_id}

        result = self._request.post(url, data, timeout=timeout)

        return Chat.de_json(result, self)

    @log
    def get_chat_administrators(self, chat_id, timeout=None, **kwargs):
        """
        Use this method to get a list of administrators in a chat. On success, returns an Array of
        ChatMember objects that contains information about all chat administrators except other
        bots. If the chat is a group or a supergroup and no administrators were appointed,
        only the creator will be returned.

        Args:
            chat_id (int|str): Unique identifier for the target chat or username of the target
                    channel (in the format @channelusername).
            timeout (Optional[int|float]): If this value is specified, use it as the read timeout
                    from the server (instead of the one specified during creation of the connection
                    pool).
            **kwargs (dict): Arbitrary keyword arguments.

        Returns:
            list(:class:`telegram.ChatMember`)

        Raises:
            :class:`telegram.TelegramError`
        """

        url = '{0}/getChatAdministrators'.format(self.base_url)

        data = {'chat_id': chat_id}

        result = self._request.post(url, data, timeout=timeout)

        return [ChatMember.de_json(x, self) for x in result]

    @log
    def get_chat_members_count(self, chat_id, timeout=None, **kwargs):
        """
        Use this method to get the number of members in a chat

        Args:
            chat_id (int|str): Unique identifier for the target chat or username of the target
                    channel (in the format @channelusername).
            timeout (Optional[int|float]): If this value is specified, use it as the read timeout
                    from the server (instead of the one specified during creation of the connection
                    pool).
            **kwargs (dict): Arbitrary keyword arguments.

        Returns:
            int: Number of members in the chat.

        Raises:
            :class:`telegram.TelegramError`
        """

        url = '{0}/getChatMembersCount'.format(self.base_url)

        data = {'chat_id': chat_id}

        result = self._request.post(url, data, timeout=timeout)

        return result

    @log
    def get_chat_member(self, chat_id, user_id, timeout=None, **kwargs):
        """
        Use this method to get information about a member of a chat.

        Args:
            chat_id (int|str): Unique identifier for the target chat or username of the target
                    channel (in the format @channelusername).
            user_id (int): Unique identifier of the target user.
            timeout (Optional[int|float]): If this value is specified, use it as the read timeout
                    from the server (instead of the one specified during creation of the connection
                    pool).
            **kwargs (dict): Arbitrary keyword arguments.

        Returns:
            :class:`telegram.ChatMember`

        Raises:
            :class:`telegram.TelegramError`
        """

        url = '{0}/getChatMember'.format(self.base_url)

        data = {'chat_id': chat_id, 'user_id': user_id}

        result = self._request.post(url, data, timeout=timeout)

        return ChatMember.de_json(result, self)

    def get_webhook_info(self, timeout=None, **kwargs):
        """
        Use this method to get current webhook status. Requires no parameters.
        If the bot is using getUpdates, will return an object with the url field empty.

        Args:
            timeout (Optional[int|float]): If this value is specified, use it as the read timeout
                    from the server (instead of the one specified during creation of the connection
                    pool).
            **kwargs (dict): Arbitrary keyword arguments.

        Returns:
            :class: `telegram.WebhookInfo`
        """

        url = '{0}/getWebhookInfo'.format(self.base_url)

        data = {}

        result = self._request.post(url, data, timeout=timeout)

        return WebhookInfo.de_json(result, self)

    @log
    @message
    def set_game_score(self,
                       user_id,
                       score,
                       chat_id=None,
                       message_id=None,
                       inline_message_id=None,
                       edit_message=None,
                       force=None,
                       disable_edit_message=None,
                       timeout=None,
                       **kwargs):
        """
        Use this method to set the score of the specified user in a game. On success, if the
        message was sent by the bot, returns the edited Message, otherwise returns True. Returns
        an error, if the new score is not greater than the user's current score in the chat and
        force is False.

        Args:
            user_id (int): User identifier.
            score (int): New score, must be non-negative.
            force (Optional[bool]): Pass True, if the high score is allowed to decrease. This can
                    be useful when fixing mistakes or banning cheaters
            disable_edit_message (Optional[bool]): Pass True, if the game message should not be
                    automatically edited to include the current scoreboard.
            chat_id (Optional[int|str]): Required if inline_message_id is not specified.
                    Unique identifier for the target chat
            message_id (Optional[int]): Required if inline_message_id is not specified.
                    Identifier of the sent message.
            inline_message_id (Optional[str]): Required if chat_id and message_id are not
                    specified. Identifier of the inline message.
            timeout (Optional[int|float]): If this value is specified, use it as the read timeout
                    from the server (instead of the one specified during creation of the connection
                    pool).
            **kwargs (dict): Arbitrary keyword arguments.

        Returns:
            :class:`telegram.Message`|bool: The edited message, or if the message wasn't sent by
            the bot, True.

        Raises:
            :class:`telegram.TelegramError`
        """

        url = '{0}/setGameScore'.format(self.base_url)

        data = {'user_id': user_id, 'score': score}

        if chat_id:
            data['chat_id'] = chat_id
        if message_id:
            data['message_id'] = message_id
        if inline_message_id:
            data['inline_message_id'] = inline_message_id
        if force is not None:
            data['force'] = force
        if disable_edit_message is not None:
            data['disable_edit_message'] = disable_edit_message
        if edit_message is not None:
            warnings.warn('edit_message is deprecated, use disable_edit_message instead')
            if disable_edit_message is None:
                data['edit_message'] = edit_message
            else:
                warnings.warn('edit_message is ignored when disable_edit_message is used')

        return url, data

    @log
    def get_game_high_scores(self,
                             user_id,
                             chat_id=None,
                             message_id=None,
                             inline_message_id=None,
                             timeout=None,
                             **kwargs):
        """
        Use this method to get data for high score tables. Will return the score of the specified
        user and several of his neighbors in a game

        Args:
            user_id (int): User identifier.
            chat_id (Optional[int|str]): Required if inline_message_id is not specified. Unique
                    identifier for the target chat.
            message_id (Optional[int]): Required if inline_message_id is not specified. Identifier
                    of the sent message.
            inline_message_id (Optional[str]): Required if chat_id and message_id are not
                    specified. Identifier of the inline message.
            timeout (Optional[int|float]): If this value is specified, use it as the read timeout
                    from the server (instead of the one specified during creation of the connection
                    pool).
            **kwargs (dict): Arbitrary keyword arguments.

        Returns:
            list(:class:`telegram.GameHighScore`)

        Raises:
            :class:`telegram.TelegramError`
        """

        url = '{0}/setGameScore'.format(self.base_url)

        data = {'user_id': user_id}

        if chat_id:
            data['chat_id'] = chat_id
        if message_id:
            data['message_id'] = message_id
        if inline_message_id:
            data['inline_message_id'] = inline_message_id

        result = self._request.post(url, data, timeout=timeout)

        return [GameHighScore.de_json(hs, self) for hs in result]

    @log
    @message
    def send_invoice(self,
                     chat_id,
                     title,
                     description,
                     payload,
                     provider_token,
                     start_parameter,
                     currency,
                     prices,
                     photo_url=None,
                     photo_size=None,
                     photo_width=None,
                     photo_height=None,
                     need_name=None,
                     need_phone_number=None,
                     need_email=None,
                     need_shipping_address=None,
                     is_flexible=None,
                     disable_notification=False,
                     reply_to_message_id=None,
                     reply_markup=None,
                     timeout=None,
                     **kwargs):
        """
        Use this method to send invoices.

        Args:
            chat_id (int|str): Unique identifier for the target private chat.
            title (str): Product name.
            description (str): Product description.
            payload (str): Bot-defined invoice payload, 1-128 bytes. This will not be displayed
                    to the user, use for your internal processes.
            provider_token (str): Payments provider token, obtained via Botfather.
            start_parameter (str): Unique deep-linking parameter that can be used to generate
                    this invoice when used as a start parameter.
            currency (str): Three-letter ISO 4217 currency code
            prices (list(:class:`telegram.LabeledPrice`)): Price breakdown, a list of components
                    (e.g. product price, tax, discount, delivery cost, delivery tax, bonus, etc.)
            photo_url (Optional[str]): URL of the product photo for the invoice. Can be a photo of
                    the goods or a marketing image for a service. People like it better when they
                    see what they are paying for.
            photo_size (Optional[str]): Photo size
            photo_width (Optional[int]): Photo width
            photo_height (Optional[int]): Photo height
            need_name (Optional[bool]): Pass True, if you require the user's full name to complete
                    the order.
            need_phone_number (Optional[bool]): Pass True, if you require the user's phone number
                    to complete the order.
            need_email (Optional[bool]): Pass True, if you require the user's email to
                    complete the order.
            need_shipping_address (Optional[bool]): Pass True, if you require the user's shipping
                    address to complete the order.
            is_flexible (Optional[bool]): Pass True, if the final price depends on the shipping
                    method.
            disable_notification (Optional[bool]): Sends the message silently. Users will receive
                    a notification with no sound.
            reply_to_message_id (Optional[int]): If the message is a reply, ID of the original
                    message.
            reply_markup (Optional[:class:`telegram.ReplyMarkup`]): Additional interface options.
                        An inlinekeyboard. If empty, one 'Pay total price' button will be shown.
                        If not empty, the first button must be a Pay button.
            timeout (Optional[int|float]): If this value is specified, use it as the read timeout
                    from the server (instead of the one specified during creation of the connection
                    pool).
            **kwargs (dict): Arbitrary keyword arguments.

        Returns:
            :class:`telegram.Message`: On success, the sent Message is returned.

        Raises:
            :class:`telegram.TelegramError`
        """

        url = '{0}/sendInvoice'.format(self.base_url)

        data = {
            'chat_id': chat_id,
            'title': title,
            'description': description,
            'payload': payload,
            'provider_token': provider_token,
            'start_parameter': start_parameter,
            'currency': currency,
            'prices': [p.to_dict() for p in prices]
        }

        if photo_url is not None:
            data['photo_url'] = photo_url
        if photo_size is not None:
            data['photo_size'] = photo_size
        if photo_width is not None:
            data['photo_width'] = photo_width
        if photo_height is not None:
            data['photo_height'] = photo_height
        if need_name is not None:
            data['need_name'] = need_name
        if need_phone_number is not None:
            data['need_phone_number'] = need_phone_number
        if need_email is not None:
            data['need_email'] = need_email
        if need_shipping_address is not None:
            data['need_shipping_address'] = need_shipping_address
        if is_flexible is not None:
            data['is_flexible'] = is_flexible

        return url, data

    @log
    def answer_shipping_query(self,
                              shipping_query_id,
                              ok,
                              shipping_options=None,
                              error_message=None,
                              timeout=None,
                              **kwargs):
        """
        If you sent an invoice requesting a shipping address and the parameter is_flexible was
        specified, the Bot API will send an Update with a shipping_query field to the bot. Use
        this method to reply to shipping queries.

        Args:
            shipping_query_id (str): Unique identifier for the query to be answered.
            ok (bool): Specify True if delivery to the specified address is possible and False if
                    there are any problems (for example, if delivery to the specified address
                    is not possible).
            shipping_options (Optional[list(:class:`telegram.ShippingOption`)]): Required if ok is
                    True. A JSON-serialized array of available shipping options.
            error_message (Optional[str]): Required if ok is False. Error message in human readable
                    form that explains why it is impossible to complete the order (e.g. "Sorry,
                    delivery to your desired address is unavailable'). Telegram will display this
                    message to the user.
            timeout (Optional[int|float]): If this value is specified, use it as the read timeout
                    from the server (instead of the one specified during creation of the connection
                    pool).
            **kwargs (dict): Arbitrary keyword arguments.

        Returns:
            bool: On success, True is returned.

        Raises:
            :class:`telegram.TelegramError`
        """

        ok = bool(ok)

        if ok and (shipping_options is None or error_message is not None):
            raise TelegramError(
                'answerShippingQuery: If ok is True, shipping_options '
                'should not be empty and there should not be error_message')

        if not ok and (shipping_options is not None or error_message is None):
            raise TelegramError(
                'answerShippingQuery: If ok is False, error_message '
                'should not be empty and there should not be shipping_options')

        url_ = '{0}/answerShippingQuery'.format(self.base_url)

        data = {'shipping_query_id': shipping_query_id, 'ok': ok}

        if ok:
            data['shipping_options'] = [option.to_dict() for option in shipping_options]
        if error_message is not None:
            data['error_message'] = error_message

        result = self._request.post(url_, data, timeout=timeout)

        return result

    @log
    def answer_pre_checkout_query(self, pre_checkout_query_id, ok,
                                  error_message=None, timeout=None, **kwargs):
        """
        Once the user has confirmed their payment and shipping details, the Bot API sends the final
        confirmation in the form of an Update with the field pre_checkout_query. Use this method to
        respond to such pre-checkout queries.

        Note:
            The Bot API must receive an answer within 10 seconds after the pre-checkout
            query was sent.

        Args:
            pre_checkout_query_id (str): Unique identifier for the query to be answered.
            ok (bool): Specify True if everything is alright (goods are available, etc.) and the
                    bot is ready to proceed with the order. Use False if there are any problems.
            error_message (Optional[str]): Required if ok is False. Error message in human readable
                    form that explains the reason for failure to proceed with the checkout (e.g.
                    "Sorry, somebody just bought the last of our amazing black T-shirts while you
                    were busy filling out your payment details. Please choose a different color or
                    garment!"). Telegram will display this message to the user.
            timeout (Optional[int|float]): If this value is specified, use it as the read timeout
                    from the server (instead of the one specified during creation of the connection
                    pool).
            **kwargs (dict): Arbitrary keyword arguments.

        Returns:
            bool: On success, `True` is returned.

        Raises:
            :class:`telegram.TelegramError`
        """

        ok = bool(ok)

        if not (ok ^ (error_message is not None)):
            raise TelegramError(
                'answerPreCheckoutQuery: If ok is True, there should '
                'not be error_message; if ok is False, error_message '
                'should not be empty')

        url_ = '{0}/answerPreCheckoutQuery'.format(self.base_url)

        data = {'pre_checkout_query_id': pre_checkout_query_id, 'ok': ok}

        if error_message is not None:
            data['error_message'] = error_message

        result = self._request.post(url_, data, timeout=timeout)

        return result

    @log
    def restrict_chat_member(self, chat_id, user_id, until_date=None, can_send_messages=None,
                             can_send_media_messages=None, can_send_other_messages=None,
                             can_add_web_page_previews=None, timeout=None, **kwargs):
        """
        Use this method to restrict a user in a supergroup. The bot must be an administrator in
        the supergroup for this to work and must have the appropriate admin rights. Pass True for
        all boolean parameters to lift restrictions from a user.

        Args:
            chat_id (int|str): Unique identifier for the target chat or username of the target
                    supergroup (in the format @supergroupusername).
            user_id (int): Unique identifier of the target user.
            until_date (Optional[int|datetime]): Date when restrictions will be lifted for the
                    user, unix time. If user is restricted for more than 366 days or less than 30
                    seconds from the current time, they are considered to be restricted forever.
            can_send_messages (Optional[boolean]): Pass True, if the user can send text messages,
                    contacts, locations and venues.
            can_send_media_messages (Optional[boolean]): Pass True, if the user can send audios,
                    documents, photos, videos, video notes and voice notes, implies
                    can_send_messages.
            can_send_other_messages (Optional[boolean]): Pass True, if the user can send
                    animations, games, stickers and use inline bots, implies
                    can_send_media_messages.
            can_add_web_page_previews (Optional[boolean]): Pass True, if the user may add web page
                    previews to their messages, implies can_send_media_messages.
            timeout (Optional[int|float]): If this value is specified, use it as the read timeout
                    from the server (instead of the one specified during creation of the connection
                    pool).
            **kwargs (dict): Arbitrary keyword arguments

        Returns:
            bool: Returns True on success.

        Raises:
            :class:`telegram.TelegramError`
        """

        url = '{0}/restrictChatMember'.format(self.base_url)

        data = {'chat_id': chat_id, 'user_id': user_id}

        if until_date is not None:
            if isinstance(until_date, datetime):
                until_date = to_timestamp(until_date)
            data['until_date'] = until_date
        if can_send_messages is not None:
            data['can_send_messages'] = can_send_messages
        if can_send_media_messages is not None:
            data['can_send_media_messages'] = can_send_media_messages
        if can_send_other_messages is not None:
            data['can_send_other_messages'] = can_send_other_messages
        if can_add_web_page_previews is not None:
            data['can_add_web_page_previews'] = can_add_web_page_previews

        result = self._request.post(url, data, timeout=timeout)

        return result

    @log
    def promote_chat_member(self, chat_id, user_id, can_change_info=None,
                            can_post_messages=None, can_edit_messages=None,
                            can_delete_messages=None, can_invite_users=None,
                            can_restrict_members=None, can_pin_messages=None,
                            can_promote_members=None, timeout=None, **kwargs):
        """
        Use this method to promote or demote a user in a supergroup or a channel. The bot must be
        an administrator in the chat for this to work and must have the appropriate admin rights.
        Pass False for all boolean parameters to demote a user

        Args:
            chat_id (int|str): Unique identifier for the target chat or username of the target
                    supergroup (in the format @supergroupusername).
            user_id (int): Unique identifier of the target user.
            can_change_info (Optional[boolean]): Pass True, if the administrator can change chat
                    title, photo and other settings.
            can_post_messages (Optional[boolean]): Pass True, if the administrator can create
                    channel posts, channels only.
            can_edit_messages (Optional[boolean]): Pass True, if the administrator can edit
                    messages of other users, channels only.
            can_delete_messages (Optional[boolean]): Pass True, if the administrator can delete
                    messages of other users.
            can_invite_users (Optional[boolean]): Pass True, if the administrator can invite new
                    users to the chat.
            can_restrict_members (Optional[boolean]): Pass True, if the administrator can restrict,
                    ban or unban chat members.
            can_pin_messages (Optional[boolean]): Pass True, if the administrator can pin messages,
                    supergroups only.
            can_promote_members (Optional[boolean]): Pass True, if the administrator can add new
                    administrators with a subset of his own privileges or demote administrators
                    that he has promoted, directly or indirectly (promoted by administrators that
                    were appointed by him).
            timeout (Optional[int|float]): If this value is specified, use it as the read timeout
                    from the server (instead of the one specified during creation of the connection
                    pool).
            **kwargs (dict): Arbitrary keyword arguments

        Returns:
            bool: Returns True on success.

        Raises:
            :class:`telegram.TelegramError`
        """

        url = '{0}/promoteChatMember'.format(self.base_url)

        data = {'chat_id': chat_id, 'user_id': user_id}

        if can_change_info is not None:
            data['can_change_info'] = can_change_info
        if can_post_messages is not None:
            data['can_post_messages'] = can_post_messages
        if can_edit_messages is not None:
            data['can_edit_messages'] = can_edit_messages
        if can_delete_messages is not None:
            data['can_delete_messages'] = can_delete_messages
        if can_invite_users is not None:
            data['can_invite_users'] = can_invite_users
        if can_restrict_members is not None:
            data['can_restrict_members'] = can_restrict_members
        if can_pin_messages is not None:
            data['can_pin_messages'] = can_pin_messages
        if can_promote_members is not None:
            data['can_promote_members'] = can_promote_members

        result = self._request.post(url, data, timeout=timeout)

        return result

    @log
    def export_chat_invite_link(self, chat_id, timeout=None, **kwargs):
        """
        Use this method to export an invite link to a supergroup or a channel. The bot must be an
        administrator in the chat for this to work and must have the appropriate admin rights.

        Args:
            chat_id (int|str): Unique identifier for the target chat or username of the target
                    channel (in the format @channelusername).
            timeout (Optional[int|float]): If this value is specified, use it as the read timeout
                    from the server (instead of the one specified during creation of the connection
                    pool).
            **kwargs (dict): Arbitrary keyword arguments

        Returns:
            str: Returns exported invite link as String on success.

        Raises:
            :class:`telegram.TelegramError`
        """

        url = '{0}/exportChatInviteLink'.format(self.base_url)

        data = {'chat_id': chat_id}

        result = self._request.post(url, data, timeout=timeout)

        return result

    @log
    def set_chat_photo(self, chat_id, photo, timeout=None, **kwargs):
        """
        Use this method to set a new profile photo for the chat.
        Photos can't be changed for private chats. The bot must be an administrator in the chat
        for this to work and must have the appropriate admin rights.

        Args:
            chat_id (int|str): Unique identifier for the target chat or username of the target
                    channel (in the format @channelusername).
            photo (`telegram.InputFile`): New chat photo.
            timeout (Optional[int|float]): If this value is specified, use it as the read timeout
                    from the server (instead of the one specified during creation of the connection
                    pool).
            **kwargs (dict): Arbitrary keyword arguments

        Note:
            In regular groups (non-supergroups), this method will only work if the
            'All Members Are Admins' setting is off in the target group.

        Returns:
            bool: Returns True on success.

        Raises:
            :class:`telegram.TelegramError`
        """

        url = '{0}/setChatPhoto'.format(self.base_url)

        data = {'chat_id': chat_id, 'photo': photo}

        result = self._request.post(url, data, timeout=timeout)

        return result

    @log
    def delete_chat_photo(self, chat_id, timeout=None, **kwargs):
        """
        Use this method to delete a chat photo. Photos can't be changed for private chats. The bot
        must be an administrator in the chat for this to work and must have the appropriate admin
        rights.

        Args:
            chat_id (int|str): Unique identifier for the target chat or username of the target
                    channel (in the format @channelusername).
            timeout (Optional[int|float]): If this value is specified, use it as the read timeout
                    from the server (instead of the one specified during creation of the connection
                    pool).
            **kwargs (dict): Arbitrary keyword arguments

        Note:
            In regular groups (non-supergroups), this method will only work if the
            'All Members Are Admins' setting is off in the target group.

        Returns:
            bool: Returns True on success.

        Raises:
            :class:`telegram.TelegramError`
        """

        url = '{0}/deleteChatPhoto'.format(self.base_url)

        data = {'chat_id': chat_id}

        result = self._request.post(url, data, timeout=timeout)

        return result

    @log
    def set_chat_title(self, chat_id, title, timeout=None, **kwargs):
        """
        Use this method to change the title of a chat. Titles can't be changed for private chats.
        The bot must be an administrator in the chat for this to work and must have the appropriate
        admin rights.

        Args:
            chat_id (int|str): Unique identifier for the target chat or username of the target
                    channel (in the format @channelusername).
            title (str): New chat title, 1-255 characters.
            timeout (Optional[int|float]): If this value is specified, use it as the read timeout
                    from the server (instead of the one specified during creation of the connection
                    pool).
            **kwargs (dict): Arbitrary keyword arguments

        Note:
            In regular groups (non-supergroups), this method will only work if the
            'All Members Are Admins' setting is off in the target group.

        Returns:
            bool: Returns True on success.

        Raises:
            :class:`telegram.TelegramError`
        """

        url = '{0}/setChatTitle'.format(self.base_url)

        data = {'chat_id': chat_id, 'title': title}

        result = self._request.post(url, data, timeout=timeout)

        return result

    @log
    def set_chat_description(self, chat_id, description, timeout=None, **kwargs):
        """
        Use this method to change the description of a supergroup or a channel. The bot must be an
        administrator in the chat for this to work and must have the appropriate admin rights.

        Args:
            chat_id (int|str): Unique identifier for the target chat or username of the target
                    channel (in the format @channelusername).
            description (str): New chat description, 1-255 characters.
            timeout (Optional[int|float]): If this value is specified, use it as the read timeout
                    from the server (instead of the one specified during creation of the connection
                    pool).
            **kwargs (dict): Arbitrary keyword arguments

        Returns:
            bool: Returns True on success.

        Raises:
            :class:`telegram.TelegramError`
        """

        url = '{0}/setChatDescription'.format(self.base_url)

        data = {'chat_id': chat_id, 'description': description}

        result = self._request.post(url, data, timeout=timeout)

        return result

    @log
    def pin_chat_message(self, chat_id, message_id, disable_notification=None, timeout=None,
                         **kwargs):
        """
        Use this method to pin a message in a supergroup. The bot must be an administrator in the
        chat for this to work and must have the appropriate admin rights.

        Args:
            chat_id (int|str): Unique identifier for the target chat or username of the target
                    channel (in the format @channelusername).
            message_id (int): Identifier of a message to pin.
            disable_notification (Optional[bool): Pass True, if it is not necessary to send a
                    notification to all group members about the new pinned message.
            timeout (Optional[int|float]): If this value is specified, use it as the read timeout
                    from the server (instead of the one specified during creation of the connection
                    pool).
            **kwargs (dict): Arbitrary keyword arguments

        Returns:
            bool: Returns True on success.

        Raises:
            :class:`telegram.TelegramError`
        """

        url = '{0}/pinChatMessage'.format(self.base_url)

        data = {'chat_id': chat_id, 'message_id': message_id}

        if disable_notification is not None:
            data['disable_notification'] = disable_notification

        result = self._request.post(url, data, timeout=timeout)

        return result

    @log
    def unpin_chat_message(self, chat_id, timeout=None, **kwargs):
        """
        Use this method to unpin a message in a supergroup. The bot must be an administrator in the
        chat for this to work and must have the appropriate admin rights.

        Args:
            chat_id (int|str): Unique identifier for the target chat or username of the target
                    channel (in the format @channelusername).
            timeout (Optional[int|float]): If this value is specified, use it as the read timeout
                    from the server (instead of the one specified during creation of the connection
                    pool).
            **kwargs (dict): Arbitrary keyword arguments

        Returns:
            bool: Returns True on success.

        Raises:
            :class:`telegram.TelegramError`
        """

        url = '{0}/unpinChatMessage'.format(self.base_url)

        data = {'chat_id': chat_id}

        result = self._request.post(url, data, timeout=timeout)

        return result

    @staticmethod
    def de_json(data, bot):
        data = super(Bot, Bot).de_json(data, bot)

        return Bot(**data)

    def to_dict(self):
        data = {'id': self.id, 'username': self.username, 'first_name': self.username}

        if self.last_name:
            data['last_name'] = self.last_name

        return data

    def __reduce__(self):
        return (self.__class__, (self.token, self.base_url.replace(self.token, ''),
                                 self.base_file_url.replace(self.token, '')))

    # camelCase aliases
    getMe = get_me
    sendMessage = send_message
    deleteMessage = delete_message
    forwardMessage = forward_message
    sendPhoto = send_photo
    sendAudio = send_audio
    sendDocument = send_document
    sendSticker = send_sticker
    sendVideo = send_video
    sendVoice = send_voice
    sendVideoNote = send_video_note
    sendLocation = send_location
    sendVenue = send_venue
    sendContact = send_contact
    sendGame = send_game
    sendChatAction = send_chat_action
    answerInlineQuery = answer_inline_query
    getUserProfilePhotos = get_user_profile_photos
    getFile = get_file
    kickChatMember = kick_chat_member
    unbanChatMember = unban_chat_member
    answerCallbackQuery = answer_callback_query
    editMessageText = edit_message_text
    editMessageCaption = edit_message_caption
    editMessageReplyMarkup = edit_message_reply_markup
    getUpdates = get_updates
    setWebhook = set_webhook
    deleteWebhook = delete_webhook
    leaveChat = leave_chat
    getChat = get_chat
    getChatAdministrators = get_chat_administrators
    getChatMember = get_chat_member
    getChatMembersCount = get_chat_members_count
    getWebhookInfo = get_webhook_info
    setGameScore = set_game_score
    getGameHighScores = get_game_high_scores
    sendInvoice = send_invoice
    answerShippingQuery = answer_shipping_query
    answerPreCheckoutQuery = answer_pre_checkout_query
    restrictChatMember = restrict_chat_member
    promoteChatMember = promote_chat_member
    exportChatInviteLink = export_chat_invite_link
    setChatPhoto = set_chat_photo
    deleteChatPhoto = delete_chat_photo
    setChatTitle = set_chat_title
    setChatDescription = set_chat_description
    pinChatMessage = pin_chat_message
    unpinChatMessage = unpin_chat_message
