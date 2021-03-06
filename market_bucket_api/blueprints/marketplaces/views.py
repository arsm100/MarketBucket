from flask import jsonify, Blueprint, request, make_response
from market_bucket.marketplaces.model import Marketplace, db
import simplejson as json
from market_bucket import LAZADA_MARKET_KEY, LAZADA_MARKET_SECRET, LAZADA_REDIRECT_URI, lazada, shopee, oauth, User
from market_bucket.helpers.lazada_sdk.lazop.base import LazopClient, LazopRequest, LazopResponse
from market_bucket.helpers.sendgrid import send_new_marketplace_email

marketplaces_api_blueprint = Blueprint('marketplaces_api',
                                       __name__,
                                       template_folder='templates')


@marketplaces_api_blueprint.route('/', methods=['GET'])
def index():
    marketplaces = Marketplace.query.all()

    # all_billboards = []
    # for billboard in billboards:
    #     billboard.get_bid_times()
    #     del billboard.__dict__['bids']
    #     billboard.__dict__['bids'] = billboard.get_bids()
    #     del billboard.__dict__['_sa_instance_state']
    #     all_billboards.append(billboard.__dict__)

    responseObject = {
        'status': 'success',
        'message': 'All marketplaces returned',
        # 'all_billboards': all_billboards
    }

    return make_response(json.dumps(responseObject)), 200


@marketplaces_api_blueprint.route('/check/lazada', methods=['GET'])
def lazada_authorize():
    return lazada.authorize_redirect(LAZADA_REDIRECT_URI, _external=True)


@marketplaces_api_blueprint.route('/authorize/lazada', methods=['POST'])
def lazada_authorize_login():
    code = request.get_json().get('code')
    auth_header = request.headers.get('Authorization')
    if auth_header:
        auth_token = auth_header.split(" ")[1]
    else:
        responseObject = {
            'status': 'failed',
            'message': 'No authorization header found'
        }

        return make_response(jsonify(responseObject)), 401

    user_id = User.decode_auth_token(auth_token)

    user = User.query.get(user_id)

    if user:
        client = LazopClient("https://auth.lazada.com/rest",
                             LAZADA_MARKET_KEY, LAZADA_MARKET_SECRET)
        api_request = LazopRequest("/auth/token/create")
        api_request.add_api_param("code", code)
        response = client.execute(api_request)
        access_token = response.body.get('access_token')
        refresh_token = response.body.get('refresh_token')
        seller_id = response.body.get('country_user_info')[0].get('seller_id')
        short_code = response.body.get('country_user_info')[
            0].get('short_code')
        # email = response.body.get('account')
        print(response.body)

        new_marketplace = Marketplace(
            user_id=user_id,
            marketplace_name="lazada",
            shop_id=seller_id,
            shop_name=short_code,
            access_token=access_token,
            refresh_token=refresh_token
        )

        db.session.add(new_marketplace)
        db.session.commit()
        send_new_marketplace_email(user.email, user_id, "Lazada")

        responseObject = {
            'status': 'success',
            'message': 'Marketplaces connected successfully',
            'lazada_refresh': refresh_token,
            'lazada_token': access_token
        }

        return make_response(jsonify(responseObject)), 201

    else:
        responseObject = {
            'status': 'failed',
            'message': 'Authentication failed'
        }
        return make_response(jsonify(responseObject)), 401


@marketplaces_api_blueprint.route('/check/shopee', methods=['GET'])
def shopee_authorize():
    return shopee.authorize_redirect(_external=True)


@marketplaces_api_blueprint.route('/authorize/shopee', methods=['POST'])
def shopee_authorize_login():
    shop_id = request.get_json().get('shop_id')
    auth_header = request.headers.get('Authorization')
    if auth_header:
        auth_token = auth_header.split(" ")[1]
    else:
        responseObject = {
            'status': 'failed',
            'message': 'No authorization header found'
        }

        return make_response(jsonify(responseObject)), 401

    user_id = User.decode_auth_token(auth_token)

    user = User.query.get(user_id)

    if user:

        new_marketplace = Marketplace(
            user_id=user_id,
            marketplace_name="shopee",
            shop_id=shop_id,
            shop_name="",
            access_token="",
            refresh_token=""
        )

        db.session.add(new_marketplace)
        db.session.commit()
        send_new_marketplace_email(user.email, user_id, "Shopee")

        responseObject = {
            'status': 'success',
            'message': 'Marketplaces connected successfully',
            'shopee_shop_id': shop_id
        }

        return make_response(jsonify(responseObject)), 201

    else:
        responseObject = {
            'status': 'failed',
            'message': 'Authentication failed'
        }
        return make_response(jsonify(responseObject)), 401


@marketplaces_api_blueprint.route('/delete', methods=['DELETE'])
def destroy():
    auth_header = request.headers.get('Authorization')
    if auth_header:
        auth_token = auth_header.split(" ")[1]
    else:
        responseObject = {
            'status': 'failed',
            'message': 'No authorization header found'
        }

        return make_response(jsonify(responseObject)), 401

    user_id = User.decode_auth_token(auth_token)

    user = User.query.get(user_id)

    if user:
        marketplace_name = request.get_json().get('marketplace_name')
        deleted_marketplace = Marketplace.query.filter_by(
            marketplace_name=marketplace_name, user_id=user_id).first()
        db.session.delete(deleted_marketplace)
        db.session.commit()

        responseObject = {
            'status': 'success',
            'message': 'Marketplaces deleted successfully',
        }

        return make_response(jsonify(responseObject)), 201

    else:
        responseObject = {
            'status': 'failed',
            'message': 'Authentication failed'
        }
        return make_response(jsonify(responseObject)), 401
