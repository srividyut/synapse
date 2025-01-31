# Copyright 2020 The Matrix.org Foundation C.I.C.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from typing import Any, Dict, Optional

import attr

from ._base import Config


@attr.s(frozen=True)
class SsoAttributeRequirement:
    """Object describing a single requirement for SSO attributes."""

    attribute = attr.ib(type=str)
    # If a value is not given, than the attribute must simply exist.
    value = attr.ib(type=Optional[str])

    JSON_SCHEMA = {
        "type": "object",
        "properties": {"attribute": {"type": "string"}, "value": {"type": "string"}},
        "required": ["attribute", "value"],
    }


class SSOConfig(Config):
    """SSO Configuration"""

    section = "sso"

    def read_config(self, config, **kwargs):
        sso_config: Dict[str, Any] = config.get("sso") or {}

        # The sso-specific template_dir
        self.sso_template_dir = sso_config.get("template_dir")

        # Read templates from disk
        (
            self.sso_login_idp_picker_template,
            self.sso_redirect_confirm_template,
            self.sso_auth_confirm_template,
            self.sso_error_template,
            sso_account_deactivated_template,
            sso_auth_success_template,
            self.sso_auth_bad_user_template,
        ) = self.read_templates(
            [
                "sso_login_idp_picker.html",
                "sso_redirect_confirm.html",
                "sso_auth_confirm.html",
                "sso_error.html",
                "sso_account_deactivated.html",
                "sso_auth_success.html",
                "sso_auth_bad_user.html",
            ],
            self.sso_template_dir,
        )

        # These templates have no placeholders, so render them here
        self.sso_account_deactivated_template = (
            sso_account_deactivated_template.render()
        )
        self.sso_auth_success_template = sso_auth_success_template.render()

        self.sso_client_whitelist = sso_config.get("client_whitelist") or []

        self.sso_update_profile_information = (
            sso_config.get("update_profile_information") or False
        )

        # Attempt to also whitelist the server's login fallback, since that fallback sets
        # the redirect URL to itself (so it can process the login token then return
        # gracefully to the client). This would make it pointless to ask the user for
        # confirmation, since the URL the confirmation page would be showing wouldn't be
        # the client's.
        # public_baseurl is an optional setting, so we only add the fallback's URL to the
        # list if it's provided (because we can't figure out what that URL is otherwise).
        if self.public_baseurl:
            login_fallback_url = self.public_baseurl + "_matrix/static/client/login"
            self.sso_client_whitelist.append(login_fallback_url)

    def generate_config_section(self, **kwargs):
        return """\
        # Additional settings to use with single-sign on systems such as OpenID Connect,
        # SAML2 and CAS.
        #
        sso:
            # A list of client URLs which are whitelisted so that the user does not
            # have to confirm giving access to their account to the URL. Any client
            # whose URL starts with an entry in the following list will not be subject
            # to an additional confirmation step after the SSO login is completed.
            #
            # WARNING: An entry such as "https://my.client" is insecure, because it
            # will also match "https://my.client.evil.site", exposing your users to
            # phishing attacks from evil.site. To avoid this, include a slash after the
            # hostname: "https://my.client/".
            #
            # If public_baseurl is set, then the login fallback page (used by clients
            # that don't natively support the required login flows) is whitelisted in
            # addition to any URLs in this list.
            #
            # By default, this list is empty.
            #
            #client_whitelist:
            #  - https://riot.im/develop
            #  - https://my.custom.client/

            # Uncomment to keep a user's profile fields in sync with information from
            # the identity provider. Currently only syncing the displayname is
            # supported. Fields are checked on every SSO login, and are updated
            # if necessary.
            #
            # Note that enabling this option will override user profile information,
            # regardless of whether users have opted-out of syncing that
            # information when first signing in. Defaults to false.
            #
            #update_profile_information: true

            # Directory in which Synapse will try to find the template files below.
            # If not set, or the files named below are not found within the template
            # directory, default templates from within the Synapse package will be used.
            #
            # Synapse will look for the following templates in this directory:
            #
            # * HTML page to prompt the user to choose an Identity Provider during
            #   login: 'sso_login_idp_picker.html'.
            #
            #   This is only used if multiple SSO Identity Providers are configured.
            #
            #   When rendering, this template is given the following variables:
            #     * redirect_url: the URL that the user will be redirected to after
            #       login.
            #
            #     * server_name: the homeserver's name.
            #
            #     * providers: a list of available Identity Providers. Each element is
            #       an object with the following attributes:
            #
            #         * idp_id: unique identifier for the IdP
            #         * idp_name: user-facing name for the IdP
            #         * idp_icon: if specified in the IdP config, an MXC URI for an icon
            #              for the IdP
            #         * idp_brand: if specified in the IdP config, a textual identifier
            #              for the brand of the IdP
            #
            #   The rendered HTML page should contain a form which submits its results
            #   back as a GET request, with the following query parameters:
            #
            #     * redirectUrl: the client redirect URI (ie, the `redirect_url` passed
            #       to the template)
            #
            #     * idp: the 'idp_id' of the chosen IDP.
            #
            # * HTML page to prompt new users to enter a userid and confirm other
            #   details: 'sso_auth_account_details.html'. This is only shown if the
            #   SSO implementation (with any user_mapping_provider) does not return
            #   a localpart.
            #
            #   When rendering, this template is given the following variables:
            #
            #     * server_name: the homeserver's name.
            #
            #     * idp: details of the SSO Identity Provider that the user logged in
            #       with: an object with the following attributes:
            #
            #         * idp_id: unique identifier for the IdP
            #         * idp_name: user-facing name for the IdP
            #         * idp_icon: if specified in the IdP config, an MXC URI for an icon
            #              for the IdP
            #         * idp_brand: if specified in the IdP config, a textual identifier
            #              for the brand of the IdP
            #
            #     * user_attributes: an object containing details about the user that
            #       we received from the IdP. May have the following attributes:
            #
            #         * display_name: the user's display_name
            #         * emails: a list of email addresses
            #
            #   The template should render a form which submits the following fields:
            #
            #     * username: the localpart of the user's chosen user id
            #
            # * HTML page allowing the user to consent to the server's terms and
            #   conditions. This is only shown for new users, and only if
            #   `user_consent.require_at_registration` is set.
            #
            #   When rendering, this template is given the following variables:
            #
            #     * server_name: the homeserver's name.
            #
            #     * user_id: the user's matrix proposed ID.
            #
            #     * user_profile.display_name: the user's proposed display name, if any.
            #
            #     * consent_version: the version of the terms that the user will be
            #       shown
            #
            #     * terms_url: a link to the page showing the terms.
            #
            #   The template should render a form which submits the following fields:
            #
            #     * accepted_version: the version of the terms accepted by the user
            #       (ie, 'consent_version' from the input variables).
            #
            # * HTML page for a confirmation step before redirecting back to the client
            #   with the login token: 'sso_redirect_confirm.html'.
            #
            #   When rendering, this template is given the following variables:
            #
            #     * redirect_url: the URL the user is about to be redirected to.
            #
            #     * display_url: the same as `redirect_url`, but with the query
            #                    parameters stripped. The intention is to have a
            #                    human-readable URL to show to users, not to use it as
            #                    the final address to redirect to.
            #
            #     * server_name: the homeserver's name.
            #
            #     * new_user: a boolean indicating whether this is the user's first time
            #          logging in.
            #
            #     * user_id: the user's matrix ID.
            #
            #     * user_profile.avatar_url: an MXC URI for the user's avatar, if any.
            #           None if the user has not set an avatar.
            #
            #     * user_profile.display_name: the user's display name. None if the user
            #           has not set a display name.
            #
            # * HTML page which notifies the user that they are authenticating to confirm
            #   an operation on their account during the user interactive authentication
            #   process: 'sso_auth_confirm.html'.
            #
            #   When rendering, this template is given the following variables:
            #     * redirect_url: the URL the user is about to be redirected to.
            #
            #     * description: the operation which the user is being asked to confirm
            #
            #     * idp: details of the Identity Provider that we will use to confirm
            #       the user's identity: an object with the following attributes:
            #
            #         * idp_id: unique identifier for the IdP
            #         * idp_name: user-facing name for the IdP
            #         * idp_icon: if specified in the IdP config, an MXC URI for an icon
            #              for the IdP
            #         * idp_brand: if specified in the IdP config, a textual identifier
            #              for the brand of the IdP
            #
            # * HTML page shown after a successful user interactive authentication session:
            #   'sso_auth_success.html'.
            #
            #   Note that this page must include the JavaScript which notifies of a successful authentication
            #   (see https://matrix.org/docs/spec/client_server/r0.6.0#fallback).
            #
            #   This template has no additional variables.
            #
            # * HTML page shown after a user-interactive authentication session which
            #   does not map correctly onto the expected user: 'sso_auth_bad_user.html'.
            #
            #   When rendering, this template is given the following variables:
            #     * server_name: the homeserver's name.
            #     * user_id_to_verify: the MXID of the user that we are trying to
            #       validate.
            #
            # * HTML page shown during single sign-on if a deactivated user (according to Synapse's database)
            #   attempts to login: 'sso_account_deactivated.html'.
            #
            #   This template has no additional variables.
            #
            # * HTML page to display to users if something goes wrong during the
            #   OpenID Connect authentication process: 'sso_error.html'.
            #
            #   When rendering, this template is given two variables:
            #     * error: the technical name of the error
            #     * error_description: a human-readable message for the error
            #
            # You can see the default templates at:
            # https://github.com/matrix-org/synapse/tree/master/synapse/res/templates
            #
            #template_dir: "res/templates"
        """
