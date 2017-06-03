from datetime import datetime
from flask import render_template, session, redirect, url_for, abort, flash
from flask_login import login_required, current_user
from . import main
from .forms import NameForm, EditProfileForm, EditProfileAdminForm, LERForm
from .. import db
from ..models import User, Role, Permission, LER
from ..decorators import admin_required, permission_required


@main.route('/', methods=['GET', 'POST'])
def index():
    form = NameForm()
    if form.validate_on_submit():
        #
        return redirect(url_for('.index'))
    return render_template('index.html',
                           form=form, name=session.get('name'),
                           known=session.get('known', False),
                           current_time=datetime.utcnow())


@main.route('/admin')
@login_required
@admin_required
def for_admins_only():
    return 'For Administrators!'


@main.route('/user/<username>')
def user(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        abort(404)
    return render_template('user.html', user=user)


@main.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.first_name = form.first_name.data
        current_user.last_name = form.last_name.data
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data
        db.session.add(current_user)
        flash('Your profile has been updated.')
        return redirect(url_for('.user', username=current_user.username))
    form.first_name.data = current_user.first_name
    form.last_name.data = current_user.last_name
    form.location.data = current_user.location
    form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', form=form, user=current_user)


@main.route('/edit-profile/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_profile_admin(id):
    user = User.query.get_or_404(id)
    form = EditProfileAdminForm(user=user)
    if form.validate_on_submit():
        user.email = form.email.data
        user.username = form.username.data
        user.confirmed = form.confirmed.data
        user.role = Role.query.get(form.role.data)
        user.first_name = form.first_name.data
        user.last_name = form.last_name.data
        user.location = form.location.data
        user.about_me = form.about_me.data
        db.session.add(user)
        flash('The profile has been updated.')
        return redirect(url_for('.user', username=user.username))
    form.email.data = user.email
    form.username.data = user.username
    form.confirmed.data = user.confirmed
    form.role.data = user.role_id
    form.first_name.data = user.first_name
    form.last_name.data = user.last_name
    form.location.data = user.location
    form.about_me.data = user.about_me
    return render_template('edit_profile.html', form=form, user=user)


@main.route('/create-ler', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.WRITE)
def create_ler():
    form = LERForm()
    if current_user.can(Permission.WRITE) and form.validate_on_submit():
        ler = LER(docket=form.docket.data,
                  title=form.title.data,
                  event_date=form.event_date.data,
                  ler_number=form.ler_number.data,
                  operating_mode=form.operating_mode.data,
                  power_level=form.power_level.data,
                  cfr=form.cfr.data,
                  abstract=form.abstract.data,
                  body=form.body.data,
                  author=current_user._get_current_object())
        db.session.add(ler)
        # db.session.commit()
        return redirect(url_for('.index'))
    return render_template('create_ler.html', form=form)


@main.route('/add-component', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.WRITE)
def add_component():
    return 'Add a Component!'


@main.route('/ler-list')
@login_required
def ler_list():
    return render_template('ler_list.html')