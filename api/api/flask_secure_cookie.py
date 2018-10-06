# The MIT License (MIT)
#
# Copyright (c) 2015 Eran Sandler
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from __future__ import absolute_import

import time
import re
import logging
import base64
import hashlib
import hmac

import flask

logger = logging.getLogger("flask-secure-cookie")

_UTF8_TYPES = (bytes, type(None))
_signed_value_version_re = re.compile(br"^([1-9][0-9]*)\|(.*)$")

DEFAULT_SIGNED_VALUE_VERSION = 2
DEFAULT_SIGNED_VALUE_MIN_VERSION = 1

if not isinstance(b'', type('')):
    def u(s):
        return s
    unicode_type = str
    basestring_type = str
else:
    def u(s):
        return s.decode('unicode_escape')
    # These names don't exist in py3, so use noqa comments to disable
    # warnings in flake8.
    unicode_type = unicode  # noqa
    basestring_type = basestring  # noqa

def utf8(value):
    """Converts a string argument to a byte string.

    If the argument is already a byte string or None, it is returned unchanged.
    Otherwise it must be a unicode string and is encoded as utf8.
    """
    if isinstance(value, _UTF8_TYPES):
        return value
    if not isinstance(value, unicode_type):
        raise TypeError(
            "Expected bytes, unicode, or None; got %r" % type(value)
        )
    return value.encode("utf-8")



class SecureCookie(object):
    app = None
    cookie_secret = None

    def __init__(self, app=None, cookie_secret=None):
        self.app = app

        if cookie_secret:
            self.cookie_secret = cookie_secret

        if app is not None:
            self.init_app(app)

    def _time_independent_equals(self, a, b):
        if len(a) != len(b):
            return False
        result = 0
        if isinstance(a[0], int):  # python3 byte strings
            for x, y in zip(a, b):
                result |= x ^ y
        else:  # python2
            for x, y in zip(a, b):
                result |= ord(x) ^ ord(y)
        return result == 0

    def _get_version(self, value):
        # Figures out what version value is.  Version 1 did not include an
        # explicit version field and started with arbitrary base64 data,
        # which makes this tricky.
        m = _signed_value_version_re.match(value)
        if m is None:
            version = 1
        else:
            try:
                version = int(m.group(1))
                if version > 999:
                    # Certain payloads from the version-less v1 format may
                    # be parsed as valid integers.  Due to base64 padding
                    # restrictions, this can only happen for numbers whose
                    # length is a multiple of 4, so we can treat all
                    # numbers up to 999 as versions, and for the rest we
                    # fall back to v1 format.
                    version = 1
            except ValueError:
                version = 1
        return version

    def _create_signature_v1(self, secret, *parts):
        hash = hmac.new(utf8(secret), digestmod=hashlib.sha1)
        for part in parts:
            hash.update(utf8(part))
        return utf8(hash.hexdigest())

    def _create_signature_v2(self, secret, s):
        hash = hmac.new(utf8(secret), digestmod=hashlib.sha256)
        hash.update(utf8(s))
        return utf8(hash.hexdigest())

    def _decode_signed_value_v1(self, secret, name, value, max_age_days, clock):
        parts = utf8(value).split(b"|")
        if len(parts) != 3:
            return None
        signature = self._create_signature_v1(secret, name, parts[0], parts[1])
        if not self._time_independent_equals(parts[2], signature):
            logger.warning("Invalid cookie signature %r", value)
            return None
        timestamp = int(parts[1])
        if timestamp < clock() - max_age_days * 86400:
            logger.warning("Expired cookie %r", value)
            return None
        if timestamp > clock() + 31 * 86400:
            # _cookie_signature does not hash a delimiter between the
            # parts of the cookie, so an attacker could transfer trailing
            # digits from the payload to the timestamp without altering the
            # signature.  For backwards compatibility, sanity-check timestamp
            # here instead of modifying _cookie_signature.
            logger.warning("Cookie timestamp in future; possible tampering %r",
                            value)
            return None
        if parts[1].startswith(b"0"):
            logger.warning("Tampered cookie %r", value)
            return None
        try:
            return base64.b64decode(parts[0])
        except Exception:
            return None

    def _decode_fields_v2(self, value):
        def _consume_field(s):
            length, _, rest = s.partition(b':')
            n = int(length)
            field_value = rest[:n]
            # In python 3, indexing bytes returns small integers; we must
            # use a slice to get a byte string as in python 2.
            if rest[n:n + 1] != b'|':
                raise ValueError("malformed v2 signed value field")
            rest = rest[n + 1:]
            return field_value, rest

        rest = value[2:]  # remove version number
        key_version, rest = _consume_field(rest)
        timestamp, rest = _consume_field(rest)
        name_field, rest = _consume_field(rest)
        value_field, passed_sig = _consume_field(rest)
        return int(key_version), timestamp, name_field, value_field, passed_sig

    def _decode_signed_value_v2(self, secret, name, value, max_age_days, clock):
        try:
            key_version, timestamp, name_field, value_field, passed_sig = self._decode_fields_v2(value)
        except ValueError:
            return None
        signed_string = value[:-len(passed_sig)]

        if isinstance(secret, dict):
            try:
                secret = secret[key_version]
            except KeyError:
                return None

        expected_sig = self._create_signature_v2(secret, signed_string)
        if not self._time_independent_equals(passed_sig, expected_sig):
            return None
        if name_field != utf8(name):
            return None
        timestamp = int(timestamp)
        if timestamp < clock() - max_age_days * 86400:
            # The signature has expired.
            return None
        try:
            return base64.b64decode(value_field)
        except Exception:
            return None

    def decode_signed_value(self, secret, name, value, max_age_days=31,
                        clock=None, min_version=None):
        if clock is None:
            clock = time.time
        if min_version is None:
            min_version = DEFAULT_SIGNED_VALUE_MIN_VERSION
        if min_version > 2:
            raise ValueError("Unsupported min_version %d" % min_version)
        if not value:
            return None

        value = utf8(value)
        version = self._get_version(value)

        if version < min_version:
            return None
        if version == 1:
            return self._decode_signed_value_v1(secret, name, value,
                                           max_age_days, clock)
        elif version == 2:
            return self._decode_signed_value_v2(secret, name, value,
                                           max_age_days, clock)
        else:
            return None

    def create_signed_value(self, name, value, version=None, key_version=None,
        clock=None):

        if version is None:
            version = DEFAULT_SIGNED_VALUE_VERSION

        if clock is None:
            clock = time.time

        timestamp = utf8(str(int(clock())))
        value = base64.b64encode(utf8(value))
        if version == 1:
            signature = self._create_signature_v1(secret, name, value, timestamp)
            value = b"|".join([value, timestamp, signature])
            return value
        elif version == 2:
            # The v2 format consists of a version number and a series of
            # length-prefixed fields "%d:%s", the last of which is a
            # signature, all separated by pipes.  All numbers are in
            # decimal format with no leading zeros.  The signature is an
            # HMAC-SHA256 of the whole string up to that point, including
            # the final pipe.
            #
            # The fields are:
            # - format version (i.e. 2; no length prefix)
            # - key version (integer, default is 0)
            # - timestamp (integer seconds since epoch)
            # - name (not encoded; assumed to be ~alphanumeric)
            # - value (base64-encoded)
            # - signature (hex-encoded; no length prefix)
            def format_field(s):
                return utf8("%d:" % len(s)) + utf8(s)
            to_sign = b"|".join([
                b"2",
                format_field(str(key_version or 0)),
                format_field(timestamp),
                format_field(name),
                format_field(value),
                b''])

            if isinstance(self.cookie_secret, dict):
                assert key_version is not None, 'Key version must be set when sign key dict is used'
                assert version >= 2, 'Version must be at least 2 for key version support'
                secret = secret[key_version]

            signature = self._create_signature_v2(self.cookie_secret, to_sign)
            return to_sign + signature
        else:
            raise ValueError("Unsupported version %d" % version)

    def init_app(self, app, cookie_secret_field="COOKIE_SECRET"):
        if self.cookie_secret:
            return

        self.cookie_secret = app.config.get(cookie_secret_field, None)
        if not self.cookie_secret:
            raise Exception("{0} must be set in the configuration "
                            "prior to initializing SecureCookie"
                            .format(cookie_secret_field))

    def get(self, name, value=None, max_age_days=31, min_version=None):
        if value is None:
            value = flask.request.cookies.get(name)

        return self.decode_signed_value(self.cookie_secret,
                                   name, value, max_age_days=max_age_days,
                                   min_version=min_version)

    def set(self, name, value, response, expires_days=30, expires=None, version=None):
        cookie_value = self.create_signed_value(name, value, version=version)
        max_age = None
        if expires_days and expires is None:
            max_age = expires_days * 86400

        response.set_cookie(name, cookie_value, max_age=max_age, expires=expires)

__all__ = ["SecureCookie"]
