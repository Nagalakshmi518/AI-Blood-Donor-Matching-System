from app import db
from app.models.badge import Badge


def create_badge(data):

    badge = Badge(**data)

    db.session.add(badge)
    db.session.commit()

    return badge


def get_all_badges():

    return Badge.query.all()


def get_badge(badge_id):

    return Badge.query.get(badge_id)


def get_badges_by_donor(donor_id):

    return Badge.query.filter_by(
        donor_id=donor_id
    ).all()


def update_badge(badge, data):

    for key, value in data.items():
        setattr(badge, key, value)

    db.session.commit()

    return badge


def delete_badge(badge):

    db.session.delete(badge)
    db.session.commit()