from flask import g
from flask import request
from flask import redirect
from flask import flash
from flask import abort
from flask import url_for

from jwt_token import Client

from .utils import _user_context_processor
from .utils import _cookieSeter
from .utils import set_auth_cookies

from jwt_token.token import decode
from jwt_token.token import AccessToken
from jwt_token.token import accessTokenConfig
from jwt_token.token import getUnverifiedClaims
from jwt import ExpiredSignatureError


class LoginManager:
    def __init__(self, IdP_url: str, app=None, add_context_processor: bool = True):
        self.anonymous_user_class = AnonymousUser
        self.user_class = User

        self.login_view = None
        self.login_message = "Please log in to access this page."
        self.login_message_category = "info"

        self.refresh_view = None
        self.needs_refresh_message = "Please reauthenticate to access this page."
        self.needs_refresh_message_category = "info"

        self.localize_callback = None
        self.unauthorized_callback = None
        self.needs_refresh_callback = None

        self.IdPClient = Client(base_url="http://idp", 
                                expected_issuer="auth.myapp.internal", 
                                expected_audience="ui")

        if app is not None:
            self.init_app(app, add_context_processor)
    
    def init_app(self, app, add_context_processor):
        """
        Configures an application. This registers an `after_request` call, and
        attaches this `LoginManager` to it as `app.login_manager`.

        :param app: The :class:`flask.Flask` object to configure.
        :type app: :class:`flask.Flask`
        :param add_context_processor: Whether to add a context processor to
            the app that adds a `current_user` variable to the template.
            Defaults to ``True``.
        :type add_context_processor: bool
        """
        app.login_manager = self
        app.before_request(self._load_user)
        app.after_request(_cookieSeter)

        if add_context_processor:
            app.context_processor(_user_context_processor)
    
    def unauthorized(self):
        """
        This is called when the user is required to log in. If you register a
        callback with :meth:`LoginManager.unauthorized_handler`, then it will
        be called. Otherwise, it will take the following actions:

            - Flash :attr:`LoginManager.login_message` to the user.

            - If the app is using blueprints find the login view for
              the current blueprint using `blueprint_login_views`. If the app
              is not using blueprints or the login view for the current
              blueprint is not specified use the value of `login_view`.

            - Redirect the user to the login view. (The page they were
              attempting to access will be passed in the ``next`` query
              string variable, so you can redirect there if present instead
              of the homepage. Alternatively, it will be added to the session
              as ``next`` if USE_SESSION_FOR_NEXT is set.)

        If :attr:`LoginManager.login_view` is not defined, then it will simply
        raise a HTTP 401 (Unauthorized) error instead.

        This should be returned from a view or before/after_request function,
        otherwise the redirect will have no effect.
        """

        if self.unauthorized_callback:
            return self.unauthorized_callback()

        if not self.login_view:
            abort(401)

        if self.login_message:
            if self.localize_callback is not None:
                flash(
                    self.localize_callback(self.login_message),
                    category=self.login_message_category,
                )
            else:
                flash(self.login_message, category=self.login_message_category)

        return redirect(url_for(self.login_view, next=request.full_path))
    
    def needs_refresh(self):
        """
        This is called when the user is logged in, but they need to be
        reauthenticated because their session is stale. If you register a
        callback with `needs_refresh_handler`, then it will be called.
        Otherwise, it will take the following actions:

            - Flash :attr:`LoginManager.needs_refresh_message` to the user.

            - Redirect the user to :attr:`LoginManager.refresh_view`. (The page
              they were attempting to access will be passed in the ``next``
              query string variable, so you can redirect there if present
              instead of the homepage.)

        If :attr:`LoginManager.refresh_view` is not defined, then it will
        simply raise a HTTP 401 (Unauthorized) error instead.

        This should be returned from a view or before/after_request function,
        otherwise the redirect will have no effect.
        """

        if self.needs_refresh_callback:
            return self.needs_refresh_callback()

        if not self.refresh_view:
            abort(401)

        if self.needs_refresh_message:
            if self.localize_callback is not None:
                flash(
                    self.localize_callback(self.needs_refresh_message),
                    category=self.needs_refresh_message_category,
                )
            else:
                flash(
                    self.needs_refresh_message,
                    category=self.needs_refresh_message_category,
                )

        return redirect(url_for(self.refresh_view, next=request.full_path))
    
    def _update_request_context_with_user(self, payload=None):
        """Store the given user as ctx.user."""

        if payload is None:
            user = self.anonymous_user_class()
        else:
            user = self.user_class(payload=payload)

        g._login_user = user
    
    def _load_user(self):
        """Loads user from jwt, and refreshes if needed"""
        access_token: str = request.cookies.get(self.IdPClient.accessCookieName)
        if not access_token:
            return self._update_request_context_with_user()
        try:
            accessPayload = decode(encoded_token=access_token,
                            secret=self.IdPClient.IdPPublicKey,
                            token=AccessToken,
                            config=accessTokenConfig)
            return self._update_request_context_with_user(accessPayload.claims)
        except ExpiredSignatureError:
            refresh_token = request.cookies.get(self.IdPClient.refreshCookieName)
            if not refresh_token:
                return self._update_request_context_with_user()
            access_jti = getUnverifiedClaims(access_token)["jti"]
            tokens = self.IdPClient.refresh(refresh_token=refresh_token, last_access_jti=access_jti)
            if tokens is None:
                return self._update_request_context_with_user()
            else:
                set_auth_cookies(tokens.access, tokens.refresh)
                return self._update_request_context_with_user(getUnverifiedClaims(tokens.access))

class User:
    """
    This provides default implementations for the methods that Flask-Login
    expects user objects to have.
    """

    # Python 3 implicitly set __hash__ to None if we override __eq__
    # We set it back to its default implementation
    __hash__ = object.__hash__

    def __init__(self, payload):
        self.id = payload["sub"]
        #self.fresh = payload["fresh"]
    
    @property
    def is_fresh(self):
        return self.fresh

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        try:
            return str(self.id)
        except AttributeError:
            raise NotImplementedError("No `id` attribute - override `get_id`") from None

    def __eq__(self, other):
        """
        Checks the equality of two `UserMixin` objects using `get_id`.
        """
        if isinstance(other, User):
            return self.get_id() == other.get_id()
        return NotImplemented

    def __ne__(self, other):
        """
        Checks the inequality of two `UserMixin` objects using `get_id`.
        """
        equal = self.__eq__(other)
        if equal is NotImplemented:
            return NotImplemented
        return not equal


class AnonymousUser:
    """
    This is the default object for representing an anonymous user.
    """

    @property
    def is_authenticated(self):
        return False
    
    @property
    def is_fresh(self):
        return False

    @property
    def is_anonymous(self):
        return True

    def get_id(self):
        return
