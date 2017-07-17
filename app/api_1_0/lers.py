from flask import jsonify, request, g, abort, url_for, current_app
from .. import db
from ..models import LER, Permission
from . import api
from .decorators import permission_required
from .errors import forbidden


@api.route('/lers/')
def get_lers():
    page = request.args.get('page', 1, type=int)
    pagination = LER.query.paginate(
        page, per_page=current_app.config['NRCEVENTS_POSTS_PER_PAGE'],
        error_out=False)
    lers = pagination.items
    prev = None
    if pagination.has_prev:
        prev = url_for('api.get_lers', page=page-1, _external=True)
    next = None
    if pagination.has_next:
        next = url_for('api.get_lers', page=page+1, _external=True)
    return jsonify({
        'lers': [ler.to_json() for ler in lers],
        'prev': prev,
        'next': next,
        'count': pagination.total
    })


@api.route('/lers/<string:lernum>')
def get_ler(lernum):
    ler = LER.query.filter_by(ler_number=lernum).first()
    if ler is None:
        abort(404)
    # ler = LER.query.get_or_404(id)
    return jsonify(ler.to_json())
