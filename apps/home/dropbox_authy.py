from flask import Flask, request, g, redirect, url_for, abort, \
     render_template, flash, _app_ctx_stack
from dropbox import DropboxOAuth2Flow
from apps.home.config import ConfigData

def get_auth_flow(session):
    redirect_uri = url_for('home_blueprint.dropbox_auth_finish', _external=True)
    print(session)
    return DropboxOAuth2Flow(ConfigData.DROPBOX_APP_KEY, redirect_uri,
                                       session, 'dropbox-auth-csrf-token', consumer_secret=ConfigData.DROPBOX_APP_SECRET)